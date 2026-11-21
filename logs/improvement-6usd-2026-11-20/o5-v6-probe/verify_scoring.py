#!/usr/bin/env python3
"""Independent re-verification of O5 scoring (offline, no GPU).

Adapted from step-5 verify_scoring.py: glob now reads
runs/pi-mono/<variant>/<model>/<fixture>/result.json; tag includes the
prompt variant. Re-grade + hash-check logic unchanged."""


from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_v6_driver as drv

LOG_DIR = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    checked = skipped = mismatches = hash_mismatches = 0
    problems = []
    for result_path in sorted((LOG_DIR / "runs").glob("pi-mono/*/*/*/result.json")):
        run_dir = result_path.parent
        if ".attempt" in run_dir.name:
            continue
        rec = json.loads(result_path.read_text())
        tag = f"{rec.get('prompt_variant', '?')}/{rec.get('product', '?')}/{rec['model_key']}/{rec['task_id']}"
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
        # Re-grade from the SAVED final file + pristine fixture test file.
        passed, out, err, rc = drv.grade_pristine(rec["fixture_id"], final_path)
        if passed != rec["scoring"]["passed"]:
            mismatches += 1
            problems.append(f"{tag}: re-grade passed={passed} (rc={rc}) != recorded "
                            f"{rec['scoring']['passed']}; grading out={out[:200]!r}")
        # Re-check verifier_modified flag.
        ws_test = run_dir / "workspace" / "test_solution.py"
        fixture_test = drv.FIXTURES_ROOT / rec["fixture_id"] / "workspace" / "test_solution.py"
        expected_modified = (not ws_test.is_file()) or (sha(ws_test) != sha(fixture_test))
        if expected_modified != rec.get("verifier_modified"):
            mismatches += 1
            problems.append(f"{tag}: verifier_modified re-check {expected_modified} != "
                            f"recorded {rec.get('verifier_modified')}")
        checked += 1
    print(f"checked={checked} skipped_infra={skipped} mismatches={mismatches} "
          f"hash_mismatches={hash_mismatches}")
    for p in problems:
        print("MISMATCH:", p)
    return 0 if mismatches == 0 and hash_mismatches == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
