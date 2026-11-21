#!/usr/bin/env python3
"""Independent re-verification of step-3 scoring (offline, no GPU).

Same logic as step-2 verify_scoring.py, adapted only for the 3-level
runs/<product>/<model>/<task>/ layout. For every run with a recorded
PASS/FAIL, re-run run_test_cases (from run_driver.py, itself a verbatim
copy of the original 02_run_helix_eval.py function) on the SAVED
solution_final.py and compare with the recorded scoring.passed flag.
Also hash-checks solution_final.py against workspace/solution.py.
INFRA runs (passed=None) are skipped.
Reports mismatches; exit code 0 only when zero mismatches.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_driver as drv

LOG_DIR = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    tasks = {p["id"]: p for p in json.loads((LOG_DIR / "tasks.json").read_text())}
    checked = skipped = mismatches = hash_mismatches = 0
    problems = []
    for result_path in sorted((LOG_DIR / "runs").glob("*/*/*/result.json")):
        run_dir = result_path.parent
        if ".attempt" in run_dir.name:
            continue
        rec = json.loads((run_dir / "result.json").read_text())
        tag = f"{rec.get('product', '?')}/{rec['model_key']}/{rec['task_id']}"
        if rec["classification"] == "INFRA":
            skipped += 1
            continue
        final_path = run_dir / "solution_final.py"
        ws_path = run_dir / "workspace" / "solution.py"
        if rec["classification"] == "FAIL" and rec["classification_reason"] == "solution_missing":
            if ws_path.exists() or final_path.exists():
                problems.append(f"{tag}: marked solution_missing but file exists")
                mismatches += 1
            checked += 1
            continue
        if not final_path.is_file():
            problems.append(f"{tag}: solution_final.py missing")
            mismatches += 1
            continue
        if ws_path.is_file() and sha(final_path) != sha(ws_path):
            hash_mismatches += 1
            problems.append(f"{tag}: solution_final.py hash != workspace solution.py")
        code = final_path.read_bytes().decode("utf-8")
        passed, err = drv.run_test_cases(code, tasks[rec["task_id"]]["test_cases"])
        checked += 1
        if passed != rec["scoring"]["passed"] or (err or None) != (rec["scoring"]["error"] or None):
            mismatches += 1
            problems.append(f"{tag}: recomputed passed={passed} "
                            f"recorded={rec['scoring']['passed']}")
    print(f"checked={checked} infra_skipped={skipped} mismatches={mismatches} "
          f"hash_mismatches={hash_mismatches}")
    for p in problems:
        print("MISMATCH:", p)
    return 1 if mismatches or hash_mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
