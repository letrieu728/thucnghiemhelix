#!/usr/bin/env python3
"""O2-clean driver (2026-11-20): pi-mono ONLY, 45 tasks (held2+held3+held4),
3 models (base / clean / realtool) through the Modal vLLM endpoint
(variant C + helix-lora-clean + helix-lora-realtool), score externally.
IDENTICAL protocol to the REBUILD-fix driver except the task list and
the model under test; see DESIGN.md in this directory (written BEFORE
any GPU run).

Diff vs REBUILD-fix run_driver.py (only these, everything else verbatim):
  - tasks.json holds 45 tasks (15 held2 + 15 held3 + 15 held4; NO lcb_*);
    load_tasks asserts 45;
  - --model choices are "base" / "clean" / "realtool" (MODEL_IDS clean ->
    helix-lora-clean); all three arms are run FRESH in this experiment;
  - PILOT_IDS are the first held2 tasks (no lcb_* task is in the eval set);
  - task_set is the cohort (held2 / held3 / held4) from the task_id prefix;
  - docstring + usage examples updated; scoring, CLI argv, layout
    (runs/<product>/<model>/<task>/), health check, spend guard unchanged.

Usage:
  python3 run_driver.py --endpoint https://...modal.run --product pi-mono --model clean --tasks pilot3
  python3 run_driver.py --endpoint https://...modal.run --product pi-mono --model clean --tasks all
  python3 run_driver.py --endpoint https://...modal.run --product pi-mono --model base --tasks all
  python3 run_driver.py --endpoint https://...modal.run --product pi-mono --model realtool --tasks all
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
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent
UPSTREAM_DIR = Path.home() / "workspace/helix-eval/upstream"
TASKS_PATH = LOG_DIR / "tasks.json"
TEMPLATE_PATH = LOG_DIR / "prompt_template.txt"

MAX_STEPS = 12
CLI_TIMEOUT_SEC = 600
SEED_LINE = "# Write your implementation for this task in this file."

MODEL_IDS = {
    "clean": "helix-lora-clean",
    "realtool": "helix-lora-realtool",
    "base": "Qwen/Qwen2.5-Coder-7B-Instruct",
}

PILOT_IDS = [
    "held2_001_edit_distance",
    "held2_002_regex_match",
    "held2_003_n_queens_count",
    "held2_004_number_of_lis",
    "held2_005_word_ladder",
]

# Step 3 pilot: exactly the first 3 pilot ids of step 2.
PILOT3_IDS = PILOT_IDS[:3]

LOOSE_TEST_IDS = {
    "lcb_002_valid_parentheses",
    "lcb_004_reverse_linked_list",
    "lcb_009_word_break",
    "lcb_014_daily_temperatures",
    "lcb_019_permutations_unique",
    "held2_011_valid_sudoku",
}

# =============================================================================
# Scoring — copied VERBATIM in semantics from run_test_cases in
# closed-loop/scripts/02_run_helix_eval.py lines 521-548
# (SANDBOX_TIMEOUT_SEC = 5, line 120). Do not "improve" this.
# =============================================================================
SANDBOX_TIMEOUT_SEC = 5  # max wall-clock seconds per test_cases run


def run_test_cases(code, test_cases, timeout=SANDBOX_TIMEOUT_SEC):
    """Copied from 02_run_helix_eval.py run_test_cases (lines 521-548)."""
    # Build a self-contained script: inject code then assertions
    test_lines = "\n".join(test_cases)
    script = f"{code}\n\n# --- auto-generated test harness ---\n{test_lines}\n"

    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, None
        err = (result.stderr or result.stdout or "").strip()
        return False, err[:500]  # cap error length for JSON cleanliness
    except subprocess.TimeoutExpired:
        return False, f"TimeoutError: execution exceeded {timeout}s"
    except Exception as exc:
        return False, f"SubprocessError: {exc}"


# =============================================================================
# Helpers
# =============================================================================

def now_iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_tasks():
    tasks = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    assert len(tasks) == 45, f"tasks.json must hold 45 tasks, got {len(tasks)}"
    return tasks


def load_template():
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    # File ends with a newline by convention; the template itself has none.
    text = text.rstrip("\n")
    assert "{prompt}" in text, "prompt template must contain {prompt}"
    return text


def build_prompt(template, problem):
    # .replace, not .format: problem prompts may contain braces.
    return template.replace("{prompt}", problem["prompt"])


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
    """Extract the CLI run-record JSON object from stdout.

    `npm run` echoes the full command line (including --prompt text) to
    stdout BEFORE the JSON output. Prompt text may itself contain '{',
    '[]' or '{}' (e.g. lcb_002's prompt mentions (), [], {}), so taking
    the substring from the FIRST '{' is WRONG (parser v1 bug, found in
    the pilot: lcb_002 failed with "Extra data" because the first '{'
    belonged to '{}' inside the echoed prompt).

    Parser v2: scan every '{' position, JSON-decode from there, and accept
    the first dict that looks like a run record (has 'steps' plus
    'transcript'/'assistantParts'). Anything else (prompt fragments) is
    skipped. Raises ValueError if no run record is found.
    """
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


def run_one_task(problem, task_set, model_key, model_id, endpoint, run_dir,
                 template, product, rerun_info=None):
    task_id = problem["id"]
    workspace_dir = run_dir / "workspace"
    storage_dir = run_dir / "storage"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Seed workspace: task.md = prompt verbatim (exact bytes, no added
    # newline); solution.py = exactly one seed line + trailing newline.
    (workspace_dir / "task.md").write_bytes(problem["prompt"].encode("utf-8"))
    (workspace_dir / "solution.py").write_text(SEED_LINE + "\n", encoding="utf-8")

    prompt = build_prompt(template, problem)
    (run_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

    argv = [
        "npm", "run", "helix", "--", "run", product,
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

    # ---- Classification, in the pre-committed order (DESIGN.md section 5.2).
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
    # else: score solution.py below.

    # ---- External scoring (only when not already INFRA).
    solution_path = workspace_dir / "solution.py"
    solution_present = solution_path.is_file()
    solution_changed = False
    solution_bytes = None
    passed = None
    score_error = None
    if classification is None:
        if not solution_present:
            classification, reason = "FAIL", "solution_missing"
        else:
            raw = solution_path.read_bytes()
            solution_bytes = len(raw)
            solution_changed = (raw.decode("utf-8", "replace") != SEED_LINE + "\n")
            shutil.copyfile(solution_path, run_dir / "solution_final.py")
            try:
                code = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                classification, reason = "FAIL", "solution_not_utf8"
                score_error = f"UnicodeDecodeError: {exc}"
                code = None
            if code is not None:
                passed, score_error = run_test_cases(code, problem["test_cases"])
                if passed:
                    classification, reason = "PASS", "tests_passed"
                else:
                    classification, reason = "FAIL", "tests_failed"
    else:
        # INFRA runs: still snapshot whatever solution.py exists (evidence),
        # but do NOT score it and do NOT let it change the classification.
        if solution_present:
            raw = solution_path.read_bytes()
            solution_bytes = len(raw)
            solution_changed = (raw.decode("utf-8", "replace") != SEED_LINE + "\n")
            shutil.copyfile(solution_path, run_dir / "solution_final.py")

    workspace_files = []
    for path in sorted(workspace_dir.rglob("*")):
        if path.is_file():
            workspace_files.append({"path": str(path.relative_to(workspace_dir)),
                                    "bytes": path.stat().st_size})

    result = {
        "schema_version": 1,
        "product": product,
        "timestamp_start": start_iso,
        "timestamp_end": end_iso,
        "timestamp_start_epoch": start_epoch,
        "timestamp_end_epoch": end_epoch,
        "model_key": model_key,
        "model_id": model_id,
        "task_id": task_id,
        "title": problem["title"],
        "difficulty": problem["difficulty"],
        "task_set": task_set,
        "loose_test": task_id in LOOSE_TEST_IDS,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
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
        "scoring": {
            "solution_present": solution_present,
            "solution_changed": solution_changed,
            "solution_bytes": solution_bytes,
            "passed": passed,
            "error": score_error,
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
    parser = argparse.ArgumentParser(description="Rebuild Step 3 driver")
    parser.add_argument("--endpoint", required=True, help="Modal base URL, no /v1 suffix")
    parser.add_argument("--product", required=True, choices=["pi-mono", "opencode", "hermes-agent"],
                        help="Assembled harness product")
    parser.add_argument("--model", required=True, choices=["clean", "realtool", "base"])
    parser.add_argument("--tasks", required=True,
                        help="'pilot', 'pilot3', 'all', or comma-separated task ids")
    parser.add_argument("--rerun", action="store_true",
                        help="Re-run exactly one task, archiving the old run dir")
    parser.add_argument("--rerun-reason", default="",
                        help="Required with --rerun: identified infra cause")
    parser.add_argument("--skip-health-check", action="store_true")
    parser.add_argument("--clock-start-epoch", type=float, default=None,
                        help="Container warmup start (epoch) for spend guard")
    parser.add_argument("--spend-cap-usd", type=float, default=None,
                        help="Stop before next task if elapsed*rate exceeds this")
    parser.add_argument("--planning-rate-per-sec", type=float, default=1.50 / 3600,
                        help="Conservative all-in $/sec for the spend guard")
    args = parser.parse_args()

    if args.rerun and not args.rerun_reason:
        parser.error("--rerun requires --rerun-reason")

    tasks = load_tasks()
    by_id = {p["id"]: p for p in tasks}
    order = [p["id"] for p in tasks]

    if args.tasks == "pilot":
        selected = list(PILOT_IDS)
    elif args.tasks == "pilot3":
        selected = list(PILOT3_IDS)
    elif args.tasks == "all":
        selected = list(order)
    else:
        selected = [t.strip() for t in args.tasks.split(",") if t.strip()]
    for task_id in selected:
        if task_id not in by_id:
            parser.error(f"unknown task id: {task_id}")
    if args.rerun and len(selected) != 1:
        parser.error("--rerun requires exactly one task")

    model_id = MODEL_IDS[args.model]
    runs_root = LOG_DIR / "runs" / args.product / args.model
    runs_root.mkdir(parents=True, exist_ok=True)

    # Upstream cleanliness snapshot (read-only check).
    git_before = subprocess.run(["git", "status", "--porcelain"],
                                cwd=str(UPSTREAM_DIR), capture_output=True,
                                text=True, timeout=30)
    stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S")
    (LOG_DIR / f"upstream_git_status_before_{args.product}_{args.model}_{stamp}.txt").write_text(
        f"checked_at: {now_iso()}\n"
        f"command: git -C {UPSTREAM_DIR} status --porcelain\n"
        f"exit_code: {git_before.returncode}\n"
        f"output:\n{git_before.stdout}{git_before.stderr}", encoding="utf-8")
    if git_before.stdout.strip():
        print("[WARN] upstream working tree not clean at driver start; "
              "see snapshot file. Continuing (driver writes outside upstream).",
              flush=True)

    if not args.skip_health_check:
        health_log = LOG_DIR / f"health_check_{args.product}_{args.model}_{stamp}.json"
        print(f"[driver] checking /health (log: {health_log.name}) ...", flush=True)
        if not check_health(args.endpoint, health_log):
            print("[driver] ABORT: /health did not report shim_enabled=true. "
                  f"See {health_log}", flush=True)
            return 2
        print("[driver] /health OK, shim enabled.", flush=True)

    template = load_template()

    for idx, task_id in enumerate(selected, 1):
        # Spend guard (checked before each task).
        if args.clock_start_epoch is not None and args.spend_cap_usd is not None:
            est = (time.time() - args.clock_start_epoch) * args.planning_rate_per_sec
            if est > args.spend_cap_usd:
                print(f"[driver] SPEND GUARD: estimated ${est:.2f} > cap "
                      f"${args.spend_cap_usd:.2f}; stopping before {task_id}.",
                      flush=True)
                return 3
        run_dir = runs_root / task_id
        rerun_info = None
        if (run_dir / "result.json").exists() and not args.rerun:
            print(f"[{idx}/{len(selected)}] SKIP {task_id} (result.json exists)",
                  flush=True)
            continue
        if args.rerun and run_dir.exists():
            n = 1
            while (runs_root / f"{task_id}.attempt{n}").exists():
                n += 1
            archived = runs_root / f"{task_id}.attempt{n}"
            run_dir.rename(archived)
            rerun_info = {"replaced_dir": archived.name,
                          "reason": args.rerun_reason,
                          "rerun_at": now_iso()}
            with open(LOG_DIR / "REPLACEMENTS.log", "a", encoding="utf-8") as fh:
                fh.write(f"{now_iso()} model={args.model} task={task_id} "
                         f"archived={archived.name} reason={args.rerun_reason}\n")
            print(f"[driver] archived previous run to {archived.name}", flush=True)
        problem = by_id[task_id]
        task_set = task_id.split("_")[0]  # cohort: held2 / held3 / held4
        print(f"[{idx}/{len(selected)}] RUN {task_id} model={args.model} ...",
              flush=True)
        result = run_one_task(problem, task_set, args.model, model_id,
                              args.endpoint, run_dir, template, args.product,
                              rerun_info=rerun_info)
        print(f"[{idx}/{len(selected)}] {task_id}: {result['classification']} "
              f"({result['classification_reason']}) steps={result['harness']['steps']} "
              f"tools={result['harness']['n_tool_calls']} "
              f"latency={result['cli']['latency_sec']}s", flush=True)
    print("[driver] done.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
