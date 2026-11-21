#!/usr/bin/env python3
"""Independent re-verification of O3 scoring (offline, no GPU).

Adapted from the step-6 verify_scoring.py (same logic, 2-level layout
runs/<branch>/<task>/; tag gains the branch). For every run with a recorded PASS/FAIL, re-run
run_test_cases (from run_driver.py, itself a verbatim copy of the original
02_run_helix_eval.py function) on the SAVED solution_final.py and compare
with the recorded scoring.passed flag. Also hash-checks solution_final.py
against workspace/solution.py, and checks every record's
recipe_file_sha256 against recipes/manifest.json. INFRA runs
(passed=None) are skipped for scoring but still get the recipe-sha check.
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
    manifest = json.loads((LOG_DIR / "recipes" / "manifest.json").read_text())
    checked = skipped = mismatches = hash_mismatches = sha_mismatches = 0
    problems = []
    for result_path in sorted((LOG_DIR / "runs").glob("*/*/result.json")):
        run_dir = result_path.parent
        if ".attempt" in run_dir.name:
            continue
        rec = json.loads((run_dir / "result.json").read_text())
        tag = f"{rec.get('branch') or rec['recipe_id']}/{rec['recipe_id']}/{rec['task_id']}"
        entry = manifest["recipes"].get(rec["recipe_id"])
        if entry is None or rec.get("recipe_file_sha256") != entry["sha256"]:
            sha_mismatches += 1
            problems.append(f"{tag}: recipe_file_sha256 != manifest sha256")
        if rec.get("blend") != entry["blend"] if entry else True:
            sha_mismatches += 1
            problems.append(f"{tag}: recorded blend != manifest blend")
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
          f"hash_mismatches={hash_mismatches} recipe_sha_mismatches={sha_mismatches}")
    for p in problems:
        print("MISMATCH:", p)
    return 1 if mismatches or hash_mismatches or sha_mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
