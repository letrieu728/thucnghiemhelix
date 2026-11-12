#!/usr/bin/env python3
"""Check HELIX conformance fixture symlinks (offline, stdlib only).

The upstream HELIX repo ships 101 fixtures under
packages/conformance/fixtures/tasks as git symlinks pointing at the paper
author's absolute path (/home/HarnessLego-pi-lcb-eval/...). They are broken
on every other machine, which blocks cassette regeneration
(see RESULTS.md, 2026-11-11 Linux run).

Usage:
  python scripts/check_fixture_symlinks.py --repo /path/to/HELIX-checkout [--json]

Exit code: 0 when no broken fixture symlinks are found, 1 otherwise.
Prints a summary plus up to 10 example broken links with their targets.
Only reads the filesystem; it never writes into the checked-out repo.
"""

import argparse
import json
import sys
from pathlib import Path

FIXTURES_REL = Path("packages/conformance/fixtures/tasks")


def check(repo: Path) -> dict:
    fixtures = repo / FIXTURES_REL
    if not fixtures.is_dir():
        return {"repo": str(repo), "error": f"fixtures directory not found: {fixtures}"}
    links = [p for p in fixtures.rglob("*") if p.is_symlink()]
    broken = [p for p in links if not p.exists()]
    return {
        "repo": str(repo),
        "fixtures_dir": str(fixtures),
        "symlinks_total": len(links),
        "broken": len(broken),
        "intact": len(links) - len(broken),
        "broken_examples": [
            {"link": str(p.relative_to(repo)), "target": p.readlink().as_posix() if hasattr(p.readlink(), "as_posix") else str(p.readlink())}
            for p in sorted(broken)[:10]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check HELIX fixture symlinks.")
    parser.add_argument("--repo", required=True, help="Path to a HELIX repo checkout")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    result = check(Path(args.repo))
    if args.json:
        print(json.dumps(result, indent=2))
    elif "error" in result:
        print(f"ERROR: {result['error']}")
    else:
        print(f"Repo: {result['repo']}")
        print(f"Fixture symlinks: {result['symlinks_total']} total, "
              f"{result['broken']} broken, {result['intact']} intact")
        for ex in result["broken_examples"]:
            print(f"  BROKEN: {ex['link']} -> {ex['target']}")
        if result["broken"] > len(result["broken_examples"]):
            print(f"  ... and {result['broken'] - len(result['broken_examples'])} more")
    if "error" in result:
        return 2
    return 1 if result["broken"] else 0


if __name__ == "__main__":
    sys.exit(main())
