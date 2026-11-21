#!/usr/bin/env python3
"""Step 5 driver (2026-11-18): run GROUP-REGENERATED v6 fixtures through the
REAL assembled pi-mono harness + Modal vLLM endpoint (variant C +
helix-lora-realtool), score externally against the PRISTINE fixture test
file. See DESIGN.md in this directory (written BEFORE any GPU run).

Adapted from the REBUILD-fix run_driver.py. Copied VERBATIM in logic:
parse_cli_stdout (parser v2), extract_tool_usage, check_health,
classify_infra_reason, the classification order, rerun/resume/skip
semantics, health-check + upstream-git-snapshot behaviour, CLI timeout
(600 s) and max-steps (12).

CHANGED vs run_driver.py (all documented in DESIGN.md section 4):
  - No tasks.json / prompt_template.txt. Fixtures come from fixtures.json;
    workspace is seeded by COPYING the fixture workspace/ (solution.py +
    test_solution.py) from the fork (read-only); prompt is built EXACTLY
    as loadTask in task-parity.ts: prompt.md trimmed + execution hints.
  - Cells are (fixture, model) pairs run in FIXTURE-MAJOR order
    (base then realtool per fixture). --cells selects "pilot" (fixture
    000, both arms), "all" (32 cells), or comma-separated "fixture:model"
    pairs. --rerun re-runs exactly one cell.
  - Scoring is NOT run_test_cases: PASS iff the agent's final solution.py
    passes the PRISTINE test_solution.py (re-read from the fork) in a
    fresh temp dir, exit 0 + marker "<fixture-id> tests passed".
  - Extra mechanism fields: read/edit/write/bash usage vs solution.py,
    ran-test-command, marker-seen-in-bash-result, verifier_modified flag.
  - Product is fixed to pi-mono; cwd is the upstream dir (code identical
    to the fork; the fork differs only by fixture content + 2 docs).

Usage:
  python3 run_v6_driver.py --endpoint https://...modal.run --cells pilot
  python3 run_v6_driver.py --endpoint https://...modal.run --cells all
  python3 run_v6_driver.py --endpoint https://...modal.run --cells livecodebench-v6-000-abc387-b:base --rerun --rerun-reason "..."
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent
UPSTREAM_DIR = Path.home() / "workspace/helix-eval/upstream"
FIXTURES_ROOT = (Path.home() / "workspace/helix-eval/fork/packages/conformance"
                 / "fixtures/tasks")
FIXTURES_PATH = LOG_DIR / "fixtures.json"

PRODUCT = "pi-mono"
MAX_STEPS = 12
CLI_TIMEOUT_SEC = 600

MODEL_IDS = {
    "realtool": "helix-lora-realtool",
    "base": "Qwen/Qwen2.5-Coder-7B-Instruct",
}

# Verbatim from taskPromptWithExecutionHints in task-parity.ts (suite
# livecodebench100 branch). Joined with "\n" after [prompt, ""].
EXECUTION_HINTS = [
    "Execution requirements:",
    "- Do not stop after analysis. After inspecting `solution.py`, modify `solution.py` before giving a final answer.",
    "- Run `python3 test_solution.py` with bash after modifying `solution.py`, and wait for the command to finish.",
    "- If the verifier fails, use the failure output to fix `solution.py` again and rerun `python3 test_solution.py` before answering.",
]


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_fixtures():
    fixtures = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    assert len(fixtures) == 16, f"fixtures.json must hold 16 fixtures, got {len(fixtures)}"
    return fixtures


def build_prompt(fixture_id: str) -> str:
    """Replicate loadTask: prompt.md bytes, .trim(), + execution hints."""
    raw = (FIXTURES_ROOT / fixture_id / "prompt.md").read_bytes()
    prompt = raw.decode("utf-8").strip()
    assert "Execution requirements:" not in prompt, f"{fixture_id}: prompt.md already has hints"
    policy = json.loads((FIXTURES_ROOT / fixture_id / "policy.json").read_text(encoding="utf-8"))
    assert policy.get("suite") == "livecodebench100", f"{fixture_id}: unexpected suite"
    return "\n".join([prompt, ""] + EXECUTION_HINTS)


def grade_pristine(fixture_id: str, solution_path: Path):
    """Run the PRISTINE fixture test file against a solution.py copy.

    Fresh temp dir; pristine test_solution.py re-read from the fork.
    Returns (passed, stdout, stderr, exit_code). PASS iff exit 0 AND
    stdout contains the marker "<fixture-id> tests passed".
    """
    marker = f"{fixture_id} tests passed"
    with tempfile.TemporaryDirectory(prefix="v6grade-") as td:
        td_path = Path(td)
        shutil.copyfile(solution_path, td_path / "solution.py")
        shutil.copyfile(FIXTURES_ROOT / fixture_id / "workspace" / "test_solution.py",
                        td_path / "test_solution.py")
        try:
            proc = subprocess.run(
                [sys.executable, "test_solution.py"],
                cwd=str(td_path), capture_output=True, text=True, timeout=300)
            out, err, rc = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as exc:
            out = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            err = f"TimeoutExpired: grading exceeded 300s"
            rc = -1
    passed = (rc == 0 and marker in out)
    return passed, out, err, rc


# =============================================================================
# Helpers copied VERBATIM in logic from run_driver.py
# =============================================================================

def check_health(endpoint, log_file):
    """Poll GET /health until 200 with shim_enabled=true (cold start can
    take minutes). Abort if a healthy response reports shim disabled."""
    url = endpoint.rstrip("/") + "/health"
    attempts = []
    deadline = time.monotonic() + 600
    attempt = 0
    while time.monotonic() < deadline:
        attempt += 1
        t0 = time.monotonic()
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=180) as resp:
                body = resp.read().decode("utf-8", "replace")
                status = resp.status
            attempts.append({"attempt": attempt, "status": status,
                             "body": body[:500], "elapsed_sec": round(time.monotonic() - t0, 1)})
            if status == 200:
                try:
                    payload = json.loads(body)
                except json.JSONDecodeError:
                    payload = {}
                if payload.get("shim_enabled") is True:
                    log_file.write_text(json.dumps(
                        {"checked_at": now_iso(), "url": url, "attempts": attempts,
                         "verdict": "ok_shim_enabled"}, indent=2), encoding="utf-8")
                    return True
                log_file.write_text(json.dumps(
                    {"checked_at": now_iso(), "url": url, "attempts": attempts,
                     "verdict": "ABORT_shim_disabled"}, indent=2), encoding="utf-8")
                return False
        except Exception as exc:  # noqa: BLE001 - record and retry
            attempts.append({"attempt": attempt, "status": None,
                             "body": f"{type(exc).__name__}: {exc}"[:500],
                             "elapsed_sec": round(time.monotonic() - t0, 1)})
        time.sleep(15)
    log_file.write_text(json.dumps(
        {"checked_at": now_iso(), "url": url, "attempts": attempts,
         "verdict": "ABORT_health_unreachable"}, indent=2), encoding="utf-8")
    return False


def parse_cli_stdout(raw_text):
    """Extract the CLI run-record JSON object from stdout (parser v2)."""
    decoder = json.JSONDecoder()
    pos = 0
    while True:
        start = raw_text.find("{", pos)
        if start < 0:
            break
        try:
            value, end = decoder.raw_decode(raw_text[start:])
        except json.JSONDecodeError:
            pos = start + 1
            continue
        if isinstance(value, dict) and "steps" in value and (
            "transcript" in value or "assistantParts" in value
        ):
            return value
        pos = start + max(end, 1)
    raise ValueError("no CLI run-record JSON object found in stdout")


def extract_tool_usage(parsed):
    """Read tool calls/results from transcript parts (never trust the
    model's prose). Falls back to assistantParts if transcript is absent."""
    messages = parsed.get("transcript") or []
    parts = []
    if messages:
        for msg in messages:
            parts.extend(msg.get("parts") or [])
    else:
        parts = parsed.get("assistantParts") or []
    calls = []
    n_results = 0
    n_result_errors = 0
    for part in parts:
        ptype = part.get("type")
        if ptype == "tool_call":
            calls.append({"tool": part.get("toolName"),
                          "status": part.get("status"),
                          "id": part.get("toolCallID")})
        elif ptype == "tool_result":
            n_results += 1
            texts = []
            for chunk in part.get("content") or []:
                if isinstance(chunk, dict):
                    texts.append(str(chunk.get("text", "")))
            joined = "\n".join(texts).strip().lower()
            if joined.startswith("error") or joined.startswith("failed"):
                n_result_errors += 1
    counts = {}
    for call in calls:
        counts[call["tool"]] = counts.get(call["tool"], 0) + 1
    return calls, counts, n_results, n_result_errors


def extract_mechanism(parsed, fixture_id):
    """Step-5 mechanism fields, from transcript parts only.

    - read_solution: a read call whose path ends with solution.py
    - edited_solution: an edit/write call whose path ends with solution.py
    - ran_test_command: a bash call whose command mentions test_solution.py
    - marker_seen: any bash tool result text contains the marker
    - bash_commands: list of bash commands issued (for audit)
    """
    messages = parsed.get("transcript") or []
    parts = []
    if messages:
        for msg in messages:
            parts.extend(msg.get("parts") or [])
    else:
        parts = parsed.get("assistantParts") or []
    marker = f"{fixture_id} tests passed"
    read_solution = edited_solution = ran_test_command = marker_seen = False
    bash_commands = []
    for part in parts:
        ptype = part.get("type")
        if ptype == "tool_call":
            tool = part.get("toolName")
            inp = part.get("input") or {}
            path = str(inp.get("path", ""))
            if tool == "read" and path.endswith("solution.py"):
                read_solution = True
            if tool in ("edit", "write") and path.endswith("solution.py"):
                edited_solution = True
            if tool == "bash":
                cmd = str(inp.get("command", ""))
                bash_commands.append(cmd[:500])
                if "test_solution.py" in cmd:
                    ran_test_command = True
        elif ptype == "tool_result" and part.get("toolName") == "bash":
            texts = []
            for chunk in part.get("content") or []:
                if isinstance(chunk, dict):
                    texts.append(str(chunk.get("text", "")))
            if marker in "\n".join(texts):
                marker_seen = True
    return {
        "read_solution": read_solution,
        "edited_solution": edited_solution,
        "ran_test_command": ran_test_command,
        "marker_seen_in_bash_result": marker_seen,
        "bash_commands": bash_commands,
    }


def classify_infra_reason(stderr_text):
    low = stderr_text.lower()
    provider_markers = ["provider_error", "502", "503", "504", "econnrefused",
                        "econnreset", "etimedout", "enotfound", "fetch failed",
                        "socket hang up", "connection refused", "connection reset",
                        "network", "timeout", "timed out", "unauthorized", "401",
                        "429", "500"]
    if any(m in low for m in provider_markers):
        return "infra_provider"
    return "infra_unknown_exit_nonzero"


def run_one_cell(fixture, model_key, model_id, endpoint, run_dir, rerun_info=None):
    fixture_id = fixture["id"]
    workspace_dir = run_dir / "workspace"
    storage_dir = run_dir / "storage"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Seed workspace: byte-for-byte COPY of the fixture workspace/
    # (solution.py buggy seed + test_solution.py). Fork is read-only.
    fixture_ws = FIXTURES_ROOT / fixture_id / "workspace"
    seed_solution = (fixture_ws / "solution.py").read_bytes()
    seed_test = (fixture_ws / "test_solution.py").read_bytes()
    (workspace_dir / "solution.py").write_bytes(seed_solution)
    (workspace_dir / "test_solution.py").write_bytes(seed_test)
    seed_hashes = {"solution.py": sha256_bytes(seed_solution),
                   "test_solution.py": sha256_bytes(seed_test)}

    prompt = build_prompt(fixture_id)
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    argv = [
        "npm", "run", "helix", "--", "run", PRODUCT,
        "--provider", "openai-compatible",
        "--model", model_id,
        "--base-url", endpoint.rstrip("/") + "/v1",
        "--api-key", "dummy",
        "--prompt", prompt,
        "--json",
        "--max-steps", str(MAX_STEPS),
        "--cwd", str(workspace_dir),
        "--storage-dir", str(storage_dir),
    ]

    start_epoch = time.time()
    start_iso = now_iso()
    timed_out = False
    proc = subprocess.Popen(
        argv, cwd=str(UPSTREAM_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout_b, stderr_b = proc.communicate(timeout=CLI_TIMEOUT_SEC)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            stdout_b, stderr_b = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            stdout_b, stderr_b = proc.communicate(timeout=30)
    end_epoch = time.time()
    end_iso = now_iso()
    latency = round(end_epoch - start_epoch, 2)
    exit_code = proc.returncode

    stdout_text = stdout_b.decode("utf-8", "replace")
    stderr_text = stderr_b.decode("utf-8", "replace")
    (run_dir / "cli_stdout.txt").write_text(stdout_text, encoding="utf-8")
    (run_dir / "cli_stderr.txt").write_text(stderr_text, encoding="utf-8")

    parsed = None
    parse_ok = False
    parse_error = None
    if not timed_out:
        try:
            parsed = parse_cli_stdout(stdout_text)
            parse_ok = True
            (run_dir / "cli_stdout.json").write_text(
                json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            parse_error = f"{type(exc).__name__}: {exc}"

    harness = {"steps": None, "finish": None, "retries": None,
               "synthetic_continues": None, "blocked_tools": None,
               "error": None, "tools_called": [], "tool_call_counts": {},
               "n_tool_calls": 0, "n_tool_results": 0, "n_tool_result_errors": 0}
    mechanism = {"read_solution": False, "edited_solution": False,
                 "ran_test_command": False, "marker_seen_in_bash_result": False,
                 "bash_commands": []}
    if parse_ok:
        harness["steps"] = parsed.get("steps")
        harness["finish"] = parsed.get("finish")
        harness["retries"] = parsed.get("retries")
        harness["synthetic_continues"] = parsed.get("syntheticContinues")
        harness["blocked_tools"] = parsed.get("blockedTools")
        harness["error"] = parsed.get("error")
        calls, counts, n_results, n_err = extract_tool_usage(parsed)
        harness["tools_called"] = calls
        harness["tool_call_counts"] = counts
        harness["n_tool_calls"] = len(calls)
        harness["n_tool_results"] = n_results
        harness["n_tool_result_errors"] = n_err
        mechanism = extract_mechanism(parsed, fixture_id)

    # ---- Classification, in the pre-committed order (DESIGN.md section 4.3).
    classification = None
    reason = None
    if timed_out:
        classification, reason = "INFRA", "cli_timeout_600s"
    elif exit_code != 0:
        classification, reason = "INFRA", "cli_exit_nonzero:" + classify_infra_reason(stderr_text)
    elif not parse_ok:
        classification, reason = "INFRA", "cli_output_unparseable"
    elif harness["finish"] == "error" or harness["error"] is not None:
        classification, reason = "INFRA", "harness_error"

    # ---- Workspace snapshot + external scoring (pristine verifier).
    solution_path = workspace_dir / "solution.py"
    test_path = workspace_dir / "test_solution.py"
    solution_present = solution_path.is_file()
    solution_changed = False
    solution_bytes = None
    final_hashes = {}
    verifier_modified = None
    if solution_present:
        raw = solution_path.read_bytes()
        solution_bytes = len(raw)
        solution_changed = (sha256_bytes(raw) != seed_hashes["solution.py"])
        final_hashes["solution.py"] = sha256_bytes(raw)
        shutil.copyfile(solution_path, run_dir / "solution_final.py")
    if test_path.is_file():
        final_hashes["test_solution.py"] = sha256_bytes(test_path.read_bytes())
        verifier_modified = (final_hashes["test_solution.py"] != seed_hashes["test_solution.py"])
    else:
        verifier_modified = True  # test file deleted by the agent

    passed = None
    grading = {"exit_code": None, "marker": f"{fixture_id} tests passed",
               "marker_in_grading_stdout": None, "error": None}
    if classification is None:
        if not solution_present:
            classification, reason = "FAIL", "solution_missing"
        else:
            try:
                solution_path.read_bytes().decode("utf-8")
            except UnicodeDecodeError as exc:
                classification, reason = "FAIL", "solution_not_utf8"
                grading["error"] = f"UnicodeDecodeError: {exc}"
            if classification is None:
                passed, gout, gerr, grc = grade_pristine(fixture_id, solution_path)
                (run_dir / "grading_stdout.txt").write_text(gout, encoding="utf-8")
                (run_dir / "grading_stderr.txt").write_text(gerr, encoding="utf-8")
                grading["exit_code"] = grc
                grading["marker_in_grading_stdout"] = grading["marker"] in gout
                if passed:
                    classification, reason = "PASS", "tests_passed"
                else:
                    classification, reason = "FAIL", "tests_failed"

    workspace_files = []
    for path in sorted(workspace_dir.rglob("*")):
        if path.is_file():
            workspace_files.append({"path": str(path.relative_to(workspace_dir)),
                                    "bytes": path.stat().st_size})

    result = {
        "schema_version": 1,
        "step": "step5-v6-fixtures",
        "fixture_label": "group-regenerated",
        "product": PRODUCT,
        "timestamp_start": start_iso,
        "timestamp_end": end_iso,
        "timestamp_start_epoch": start_epoch,
        "timestamp_end_epoch": end_epoch,
        "model_key": model_key,
        "model_id": model_id,
        "task_id": fixture_id,
        "fixture_id": fixture_id,
        "question_id": fixture["question_id"],
        "contest_id": fixture["contest_id"],
        "title": fixture["question_title"],
        "difficulty_letter": fixture["letter"],
        "public_test_cases": fixture["publicTestCases"],
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "seed_hashes": seed_hashes,
        "final_hashes": final_hashes,
        "verifier_modified": verifier_modified,
        "cli": {
            "argv": argv,
            "cwd": str(UPSTREAM_DIR),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "latency_sec": latency,
            "stdout_bytes": len(stdout_b),
            "stderr_bytes": len(stderr_b),
            "stdout_parse_ok": parse_ok,
            "parse_error": parse_error,
            "stderr_tail": stderr_text.strip()[-1000:] if stderr_text.strip() else "",
        },
        "harness": harness,
        "mechanism": mechanism,
        "scoring": {
            "solution_present": solution_present,
            "solution_changed": solution_changed,
            "solution_bytes": solution_bytes,
            "passed": passed,
            "grading": grading,
        },
        "classification": classification,
        "classification_reason": reason,
        "workspace_files": workspace_files,
        "rerun_info": rerun_info,
    }
    (run_dir / "result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description="Step 5 v6-fixture driver")
    parser.add_argument("--endpoint", required=True, help="Modal base URL, no /v1 suffix")
    parser.add_argument("--cells", required=True,
                        help="'pilot' (fixture 000, both arms), 'all' (32 cells), "
                             "or comma-separated 'fixture_id:model' pairs")
    parser.add_argument("--rerun", action="store_true",
                        help="Re-run exactly one cell, archiving the old run dir")
    parser.add_argument("--rerun-reason", default="",
                        help="Required with --rerun: identified infra cause")
    parser.add_argument("--skip-health-check", action="store_true")
    args = parser.parse_args()

    if args.rerun and not args.rerun_reason:
        parser.error("--rerun requires --rerun-reason")

    fixtures = load_fixtures()
    by_id = {f["id"]: f for f in fixtures}
    # Fixture-major order: base then realtool per fixture.
    all_cells = [(f["id"], m) for f in fixtures for m in ("base", "realtool")]

    if args.cells == "pilot":
        selected = [(fixtures[0]["id"], "base"), (fixtures[0]["id"], "realtool")]
    elif args.cells == "all":
        selected = list(all_cells)
    else:
        selected = []
        for spec in args.cells.split(","):
            spec = spec.strip()
            if not spec:
                continue
            fid, _, model = spec.rpartition(":")
            if fid not in by_id or model not in MODEL_IDS:
                parser.error(f"unknown cell spec: {spec}")
            selected.append((fid, model))
    if args.rerun and len(selected) != 1:
        parser.error("--rerun requires exactly one cell")

    runs_root = LOG_DIR / "runs" / PRODUCT
    runs_root.mkdir(parents=True, exist_ok=True)

    # Upstream cleanliness snapshot (read-only check).
    git_before = subprocess.run(["git", "status", "--porcelain"],
                                cwd=str(UPSTREAM_DIR), capture_output=True,
                                text=True, timeout=30)
    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
    (LOG_DIR / f"upstream_git_status_before_{PRODUCT}_{stamp}.txt").write_text(
        f"checked_at: {now_iso()}\n"
        f"command: git -C {UPSTREAM_DIR} status --porcelain\n"
        f"exit_code: {git_before.returncode}\n"
        f"output:\n{git_before.stdout}{git_before.stderr}", encoding="utf-8")
    if git_before.stdout.strip():
        print("[WARN] upstream working tree not clean at driver start; "
              "see snapshot file. Continuing (driver writes outside upstream).",
              flush=True)

    if not args.skip_health_check:
        health_log = LOG_DIR / f"health_check_{PRODUCT}_{stamp}.json"
        print(f"[driver] checking /health (log: {health_log.name}) ...", flush=True)
        if not check_health(args.endpoint, health_log):
            print("[driver] ABORT: /health did not report shim_enabled=true. "
                  f"See {health_log}", flush=True)
            return 2
        print("[driver] /health OK, shim enabled.", flush=True)

    for idx, (fixture_id, model_key) in enumerate(selected, 1):
        run_dir = runs_root / model_key / fixture_id
        rerun_info = None
        if (run_dir / "result.json").exists() and not args.rerun:
            print(f"[{idx}/{len(selected)}] SKIP {fixture_id}:{model_key} (result.json exists)",
                  flush=True)
            continue
        if args.rerun and run_dir.exists():
            n = 1
            while (runs_root / model_key / f"{fixture_id}.attempt{n}").exists():
                n += 1
            archived = runs_root / model_key / f"{fixture_id}.attempt{n}"
            run_dir.rename(archived)
            rerun_info = {"replaced_dir": archived.name,
                          "reason": args.rerun_reason,
                          "rerun_at": now_iso()}
            with open(LOG_DIR / "REPLACEMENTS.log", "a", encoding="utf-8") as fh:
                fh.write(f"{now_iso()} model={model_key} task={fixture_id} "
                         f"archived={archived.name} reason={args.rerun_reason}\n")
            print(f"[driver] archived previous run to {archived.name}", flush=True)
        print(f"[{idx}/{len(selected)}] RUN {fixture_id} model={model_key} ...",
              flush=True)
        result = run_one_cell(by_id[fixture_id], model_key, MODEL_IDS[model_key],
                              args.endpoint, run_dir, rerun_info=rerun_info)
        print(f"[{idx}/{len(selected)}] {fixture_id}:{model_key}: {result['classification']} "
              f"({result['classification_reason']}) steps={result['harness']['steps']} "
              f"tools={result['harness']['n_tool_calls']} "
              f"read={result['mechanism']['read_solution']} "
              f"edit={result['mechanism']['edited_solution']} "
              f"ran_test={result['mechanism']['ran_test_command']} "
              f"marker={result['mechanism']['marker_seen_in_bash_result']} "
              f"latency={result['cli']['latency_sec']}s", flush=True)
    print("[driver] done.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
