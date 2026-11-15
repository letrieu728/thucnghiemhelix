#!/usr/bin/env python3
"""Judge runner — HELIX supplement run, rows 2+5 (2026-11-15).

Uses the FIXED prompt from JUDGE_PROMPT.md verbatim: system prompt and
user template are parsed from the two ```text blocks of that file at
runtime (never retyped), so the runner cannot drift from the registered
prompt. Placeholders replaced by exact string substitution only.

Fixed call spec (JUDGE_PROMPT.md section 1): base model
Qwen/Qwen2.5-Coder-7B-Instruct, temperature 0.0, max_tokens 512,
seed 20261115, one call per cell. Output handling (section 5): strict
JSON parse + schema validation; exactly ONE retry with the identical
request on failure; then label `unparseable` with raw output kept.
Append-only JSONL output; --resume skips cells already recorded.

Usage (from repo root thucnghiemhelix/):
  HELIX_LIVE_BASE_URL=<endpoint>/v1 python3 results/2026-11-15-hang2-hang5/run_judge.py \
      --list primary --limit 10 --out results/2026-11-15-hang2-hang5/judge_runs/2026-11-15/judge_results.jsonl
"""
import argparse
import importlib.util
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SUPPL = Path(__file__).resolve().parent
TRACES_DIR = ROOT / "closed-loop" / "data" / "raw_traces"

JUDGE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
TEMPERATURE = 0.0
MAX_TOKENS = 512
SEED = 20261115

VALID_CODES = {"D1", "D2", "D3", "D4", "D5", "S1", "S2", "S3", "S4", "S5", "S6"}


def load_prompts():
    text = (SUPPL / "JUDGE_PROMPT.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```text\n(.*?)\n```", text, re.S)
    assert len(blocks) == 2, f"expected 2 ```text blocks in JUDGE_PROMPT.md, got {len(blocks)}"
    system_prompt, user_template = blocks
    assert system_prompt.startswith("You are a strict code reviewer")
    for ph in ("{problem_prompt}", "{test_cases_joined}", "{solution_code}"):
        assert ph in user_template, ph
    return system_prompt, user_template


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "helix_runner_02", ROOT / "closed-loop" / "scripts" / "02_run_helix_eval.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_problems(runner):
    problems = {}
    for p in runner.get_problems("train20"):
        problems[p["id"]] = p
    for name in ("heldout_problems.json", "heldout2_problems.json"):
        for p in json.loads((ROOT / "closed-loop" / "data" / name).read_text(encoding="utf-8")):
            problems[p["id"]] = p
    return problems


def validate_parsed(obj):
    """Return (ok, error). Strict schema per JUDGE_PROMPT.md section 5.

    The section-5 enumerated checks are: label in the 3 values; criteria
    valid codes matching the label; reason non-empty; evidence non-empty
    ONLY when the label is degenerate. A missing/null `evidence` key is
    therefore normalised to "" (the value the prompt itself specifies
    for clean) BEFORE this check runs -- see the normalisation in main().
    A non-string evidence value (e.g. a list) is still a schema error,
    and degenerate with empty evidence is still rejected.
    """
    if not isinstance(obj, dict):
        return False, "top level is not a JSON object"
    label = obj.get("label")
    if label not in ("clean", "suspicious", "degenerate"):
        return False, f"bad label: {label!r}"
    criteria = obj.get("criteria")
    if not isinstance(criteria, list) or not all(isinstance(c, str) for c in criteria):
        return False, "criteria is not a list of strings"
    if any(c not in VALID_CODES for c in criteria):
        return False, f"invalid criteria codes: {criteria}"
    has_d = any(c.startswith("D") for c in criteria)
    has_s = any(c.startswith("S") for c in criteria)
    if label == "clean" and criteria != []:
        return False, "clean must have criteria []"
    if label == "suspicious" and (not has_s or has_d):
        return False, "suspicious must have only S criteria"
    if label == "degenerate" and not has_d:
        return False, "degenerate must have at least one D criterion"
    reason = obj.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return False, "reason empty"
    evidence = obj.get("evidence")
    if not isinstance(evidence, str):
        return False, "evidence is not a string"
    if label == "degenerate" and not evidence.strip():
        return False, "degenerate requires non-empty evidence"
    return True, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", choices=["primary", "fallback", "fallback_both_sides"], default="primary")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--start-index", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--resume", action="store_true", help="skip trace_files already in --out")
    args = ap.parse_args()

    import os
    base_url = (args.base_url or os.environ.get("HELIX_LIVE_BASE_URL", "")).strip()
    assert base_url, "HELIX_LIVE_BASE_URL / --base-url required"
    from openai import OpenAI
    client = OpenAI(base_url=base_url, api_key="not-needed", timeout=120.0)

    system_prompt, user_template = load_prompts()
    runner = load_runner()
    problems = load_problems(runner)
    judge_list = json.loads((SUPPL / "judge_list.json").read_text(encoding="utf-8"))
    cells = judge_list[args.list][args.start_index:]
    if args.limit is not None:
        cells = cells[: args.limit]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if args.resume and out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["trace_file"])

    n_done = 0
    with open(out_path, "a", encoding="utf-8") as out:
        for cell in cells:
            if cell["trace_file"] in done:
                print(f"[skip] {cell['trace_file']} (already recorded)")
                continue
            trace = json.loads((TRACES_DIR / cell["trace_file"]).read_text(encoding="utf-8"))
            problem = problems[cell["task_id"]]
            code = runner.extract_python_code(trace.get("assistant_solution") or "")
            solution_code = code if code else ""
            user_msg = (
                user_template.replace("{problem_prompt}", trace.get("prompt", problem["prompt"]))
                .replace("{test_cases_joined}", "\n".join(problem["test_cases"]))
                .replace("{solution_code}", solution_code)
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
            raw_response = ""
            finish_reason = None
            parsed = None
            retries = 0
            attempt_latencies = []
            last_error = ""
            for attempt in range(2):  # initial + exactly one retry
                t0 = time.monotonic()
                try:
                    resp = client.chat.completions.create(
                        model=JUDGE_MODEL,
                        messages=messages,
                        temperature=TEMPERATURE,
                        max_tokens=MAX_TOKENS,
                        seed=SEED,
                        timeout=120.0,
                    )
                except Exception as exc:  # transport error: counts as failed attempt, no label invented
                    attempt_latencies.append(round(time.monotonic() - t0, 3))
                    last_error = f"transport: {exc}"
                    raw_response = ""
                    finish_reason = None
                    if attempt == 0:
                        retries = 1
                        continue
                    break
                attempt_latencies.append(round(time.monotonic() - t0, 3))
                raw_response = resp.choices[0].message.content or ""
                finish_reason = resp.choices[0].finish_reason
                try:
                    candidate = json.loads(raw_response.strip())
                except Exception as exc:
                    last_error = f"json parse: {exc}"
                    if attempt == 0:
                        retries = 1
                        continue
                    break
                # Normalisation (documented, deterministic, uniform):
                # the judge systematically omits the `evidence` key for
                # clean labels; the prompt specifies evidence="" for
                # clean, and JUDGE_PROMPT.md section 5 requires
                # non-empty evidence only for degenerate. Missing/null
                # -> "". No label, criteria or reason is ever altered.
                if isinstance(candidate, dict) and candidate.get("evidence") is None:
                    candidate["evidence"] = ""
                ok, err = validate_parsed(candidate)
                if ok:
                    parsed = candidate
                    last_error = ""
                    break
                last_error = f"schema: {err}"
                if attempt == 0:
                    retries = 1
                    continue
                break

            if parsed is not None:
                record = {
                    "trace_file": cell["trace_file"],
                    "task_id": cell["task_id"],
                    "harness_id": cell["harness_id"],
                    "model": cell["model"],
                    "label": parsed["label"],
                    "criteria": parsed["criteria"],
                    "reason": parsed["reason"],
                    "evidence": parsed["evidence"],
                    "raw_response": raw_response,
                    "finish_reason": finish_reason,
                    "latency_sec": round(sum(attempt_latencies), 3),
                    "attempt_latencies": attempt_latencies,
                    "retries": retries,
                    "judge_model": JUDGE_MODEL,
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS,
                    "seed": SEED,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "run_tag": cell.get("run_tag", ""),
                    "phase": cell.get("phase", ""),
                }
            else:
                record = {
                    "trace_file": cell["trace_file"],
                    "task_id": cell["task_id"],
                    "harness_id": cell["harness_id"],
                    "model": cell["model"],
                    "label": "unparseable",
                    "criteria": [],
                    "reason": "",
                    "evidence": "",
                    "raw_response": raw_response,
                    "finish_reason": finish_reason,
                    "latency_sec": round(sum(attempt_latencies), 3),
                    "attempt_latencies": attempt_latencies,
                    "retries": retries,
                    "judge_model": JUDGE_MODEL,
                    "temperature": TEMPERATURE,
                    "max_tokens": MAX_TOKENS,
                    "seed": SEED,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "run_tag": cell.get("run_tag", ""),
                    "phase": cell.get("phase", ""),
                    "parse_error": last_error,
                }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            out.flush()
            n_done += 1
            print(f"[{n_done}/{len(cells)}] {cell['trace_file']} -> {record['label']} "
                  f"{record['criteria']} latency={record['latency_sec']}s retries={retries} "
                  f"finish={finish_reason} {('ERR:' + last_error) if parsed is None else ''}", flush=True)
    print(f"recorded {n_done} new cells -> {out_path}")


if __name__ == "__main__":
    main()
