#!/usr/bin/env python3
"""O3 opencode prompt intervention statistics (2026-11-20): read runs/*/*/result.json only.

Pre-registered analysis (O3 DESIGN.md section 4), applied unchanged:
per-branch (B1/B2/B3) Pass@1 + Wilson CIs + text-only counts; paired
McNemar B1-vs-R8 and B2-vs-R8 EXPLORATORY (3 wins/0 losses -> p=0.25 max,
never significant); B3-vs-R1 descriptive; verdict rules from DESIGN
section 4 applied mechanically. Baselines R8/R1 are REUSED from
step6-mini-search/summary.json (same tasks, same runner, same protocol,
same model) — NOT re-run. No pooled tests across branches.

Wilson + McNemar exact + summarise() + no_tool_stats() copied VERBATIM
from the fix compute_stats.py (themselves from step-2 / round1_stats.py),
except the result-record block key "cli" -> "runner" (see run_driver.py).
Aggregation is new: keyed by (recipe, task), single fixed model.
Writes summary.json + summary.md next to this script.
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_driver as drv

LOG_DIR = Path(__file__).resolve().parent


# --- Copied VERBATIM from the fix compute_stats.py (except "cli"->"runner") ---
def wilson(k: int, n: int, z: float = 1.959964):
    """Wilson 95% score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar_exact(gains: int, losses: int) -> float:
    """Two-sided exact McNemar p-value (binomial, discordant pairs only)."""
    n = gains + losses
    if n == 0:
        return 1.0
    m = min(gains, losses)
    tail = sum(math.comb(n, i) for i in range(m + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def summarise(records):
    total = len(records)
    infra = [r for r in records if r["classification"] == "INFRA"]
    scored = [r for r in records if r["classification"] in ("PASS", "FAIL")]
    k = sum(1 for r in scored if r["classification"] == "PASS")
    n = len(scored)
    lo, hi = wilson(k, n)
    lat = [r["runner"]["latency_sec"] for r in scored]
    steps = [r["harness"]["steps"] for r in scored
             if isinstance(r["harness"]["steps"], int)]
    tool_totals = Counter()
    for r in records:
        for tool, c in (r["harness"]["tool_call_counts"] or {}).items():
            tool_totals[tool] += c
    return {
        "n_total": total,
        "n_infra": len(infra),
        "n_scored": n,
        "n_pass": k,
        "n_fail": n - k,
        "pass_rate": round(k / n, 4) if n else 0.0,
        "wilson95": [round(lo, 4), round(hi, 4)],
        "avg_latency_sec_scored": round(sum(lat) / len(lat), 2) if lat else 0.0,
        "total_latency_sec_scored": round(sum(lat), 1) if lat else 0.0,
        "avg_steps_scored": round(sum(steps) / len(steps), 2) if steps else 0.0,
        "tool_call_totals": dict(sorted(tool_totals.items())),
        "infra_task_ids": sorted(r["task_id"] for r in infra),
    }


def no_tool_stats(records):
    """Descriptive mechanism stats (NOT a new test): runs with zero tool
    calls, and pass rate among runs that changed solution.py."""
    scored = [r for r in records if r["classification"] in ("PASS", "FAIL")]
    no_tool = [r for r in scored if r["harness"]["n_tool_calls"] == 0]
    wrote = [r for r in scored if r["scoring"]["solution_changed"]]
    wrote_pass = sum(1 for r in wrote if r["classification"] == "PASS")
    return {
        "n_scored": len(scored),
        "n_no_tool_calls": len(no_tool),
        "n_no_tool_calls_pass": sum(1 for r in no_tool if r["classification"] == "PASS"),
        "n_wrote_file": len(wrote),
        "n_wrote_file_pass": wrote_pass,
    }


# --- O3 aggregation (new) ---

import os

STEP6_SUMMARY = (Path.home() / "workspace/helix-eval/logs/evolution-2026-11-18"
                 / "step6-mini-search" / "summary.json")

BRANCHES = {
    "B1": {"recipe": "R8", "suffix": "I-full",
           "suffix_text": "\n\nUse your tools to do this task. First read solution.py with the read tool, then write or edit it with the write or edit tool, then run it with bash to verify. Do not answer with code in chat text — act with tools."},
    "B2": {"recipe": "R8", "suffix": "I-min",
           "suffix_text": "\n\nUse the write tool to write the solution into solution.py, then run it with bash."},
    "B3": {"recipe": "R1", "suffix": "I-full",
           "suffix_text": "\n\nUse your tools to do this task. First read solution.py with the read tool, then write or edit it with the write or edit tool, then run it with bash to verify. Do not answer with code in chat text — act with tools."},
}
BRANCH_ORDER = ["B1", "B2", "B3"]
BASELINE_FOR = {"B1": "R8", "B2": "R8", "B3": "R1"}


def load_results():
    out = {}
    for result_path in sorted((LOG_DIR / "runs").glob("*/*/result.json")):
        # Skip archived attempts: runs/<branch>/<task>.attemptN/
        if ".attempt" in result_path.parent.name:
            continue
        rec = json.loads(result_path.read_text(encoding="utf-8"))
        branch = rec.get("branch") or result_path.parent.parent.name
        assert result_path.parent.parent.name == branch, (
            f"path/branch mismatch: {result_path} records {branch}")
        assert branch in BRANCHES, f"unknown branch {branch} in {result_path}"
        assert rec["recipe_id"] == BRANCHES[branch]["recipe"], (
            f"branch/recipe mismatch: {result_path} records {rec['recipe_id']}")
        assert rec.get("prompt_suffix") == BRANCHES[branch]["suffix_text"], (
            f"branch/suffix mismatch: {result_path}")
        out[(branch, rec["task_id"])] = rec
    return out


def summarise_branch(results, branch, task_order, manifest):
    recs = [results[(branch, t)] for t in task_order
            if (branch, t) in results]
    entry = {
        "recipe": BRANCHES[branch]["recipe"],
        "suffix": BRANCHES[branch]["suffix"],
        "blend": manifest["recipes"][BRANCHES[branch]["recipe"]]["blend"],
        "recipe_file": manifest["recipes"][BRANCHES[branch]["recipe"]]["file"],
        "complete": len(recs) == len(task_order),
        "missing_task_ids": [t for t in task_order if (branch, t) not in results],
        "overall": summarise(recs),
    }
    for difficulty in ("easy", "medium", "hard"):
        entry[difficulty] = summarise([r for r in recs if r["difficulty"] == difficulty])
    entry["loose_test_subset"] = summarise([r for r in recs if r["loose_test"]])
    nt = no_tool_stats(recs)
    lo, hi = wilson(nt["n_no_tool_calls"], nt["n_scored"])
    nt["text_only_wilson95"] = [round(lo, 4), round(hi, 4)]
    entry["no_tool_mechanism"] = nt
    entry["infra_detail"] = [
        {"task_id": r["task_id"], "reason": r["classification_reason"],
         "exit_code": r["runner"]["exit_code"], "timed_out": r["runner"]["timed_out"],
         "finish": r["harness"]["finish"],
         "harness_error": r["harness"]["error"],
         "stderr_tail": r["runner"]["stderr_tail"][-300:]}
        for r in recs if r["classification"] == "INFRA"]
    entry["per_task"] = [
        {"task_id": r["task_id"], "task_set": r["task_set"],
         "difficulty": r["difficulty"], "loose_test": r["loose_test"],
         "classification": r["classification"],
         "reason": r["classification_reason"],
         "steps": r["harness"]["steps"], "finish": r["harness"]["finish"],
         "n_tool_calls": r["harness"]["n_tool_calls"],
         "tool_call_counts": r["harness"]["tool_call_counts"],
         "latency_sec": r["runner"]["latency_sec"],
         "scoring_error": r["scoring"]["error"]}
        for r in recs]
    return entry


def paired_mcnemar_vs_baseline(results, branch, baseline_per_task, task_order):
    """Paired McNemar: branch vs REUSED baseline (per-task classifications
    from step-6 summary.json). Gains = baseline FAIL -> branch PASS."""
    pairs, excluded = [], []
    for task_id in task_order:
        b = results.get((branch, task_id))
        a_cls = baseline_per_task.get(task_id)
        if b is None or a_cls is None:
            excluded.append({"task_id": task_id, "reason": "missing_run",
                             "baseline": a_cls,
                             branch: b["classification"] if b else None})
            continue
        if b["classification"] == "INFRA":
            excluded.append({"task_id": task_id, "reason": "infra_on_branch_side",
                             "baseline": a_cls, branch: b["classification"]})
            continue
        pairs.append((task_id, a_cls == "PASS", b["classification"] == "PASS"))
    gains = sum(1 for _t, a, b in pairs if not a and b)
    losses = sum(1 for _t, a, b in pairs if a and not b)
    disc = gains + losses
    return {
        "branch": branch,
        "baseline": BASELINE_FOR[branch],
        "paired_tasks": len(pairs),
        "excluded_pairs": excluded,
        "gains_fail_to_pass": gains,
        "losses_pass_to_fail": losses,
        "same_pass": sum(1 for _t, a, b in pairs if a and b),
        "same_fail": sum(1 for _t, a, b in pairs if not a and not b),
        "exact_p_two_sided": round(mcnemar_exact(gains, losses), 4),
        "chi2_continuity_corrected": round((abs(gains - losses) - 1) ** 2 / disc, 3) if disc else 0.0,
        "flips": [{"task_id": t, f"{BASELINE_FOR[branch]}_pass": a, f"{branch}_pass": b}
                  for (t, a, b) in pairs if a != b],
        "label": ("EXPLORATORY: n=10 tasks; baseline REUSED from step 6 "
                  "(different run epoch). With the baseline at 0/10, 3 wins / "
                  "0 losses gives p=0.25 — never significant. Not a "
                  "confirmatory test."),
    }


def verdict_for(branch_entry):
    """Mechanical application of the pre-registered verdict rules
    (O3 DESIGN.md section 4). Returns (verdict, criteria_met)."""
    o = branch_entry["overall"]
    nt = branch_entry["no_tool_mechanism"]
    behavior = nt["n_no_tool_calls"] <= 5  # text-only <= 5/10
    outcome = o["n_pass"] >= 3             # Pass@1 >= 3/10
    if behavior and outcome:
        return ("RESCUED", {"behavior_text_only_le_5": True, "outcome_pass_ge_3": True})
    if behavior and not outcome:
        return ("BEHAVIOR-ONLY", {"behavior_text_only_le_5": True, "outcome_pass_ge_3": False})
    return ("NEGATIVE", {"behavior_text_only_le_5": False, "outcome_pass_ge_3": outcome})


def main():
    results = load_results()
    manifest = json.loads((LOG_DIR / "recipes" / "manifest.json").read_text(encoding="utf-8"))
    step6 = json.loads(STEP6_SUMMARY.read_text(encoding="utf-8"))
    task_order = [t for t in drv.SEARCH_IDS]
    branches_present = sorted({b for (b, _t) in results},
                              key=lambda b: BRANCH_ORDER.index(b) if b in BRANCH_ORDER else 99)

    # Reused baselines (NOT re-run): overall + text-only + per-task classes.
    baselines = {}
    for rid in ("R8", "R1"):
        e = step6["recipes"][rid]
        baselines[rid] = {
            "reused": True,
            "source": "evolution-2026-11-18/step6-mini-search/summary.json",
            "recipe_file": e["recipe_file"],
            "blend": e["blend"],
            "overall": e["overall"],
            "no_tool_mechanism": e["no_tool_mechanism"],
            "per_task_classification": {p["task_id"]: p["classification"]
                                        for p in e["per_task"]},
        }

    summary = {
        "meta": {
            "model": "base (Qwen/Qwen2.5-Coder-7B-Instruct, fixed for all branches)",
            "task_order": task_order,
            "branches_present": branches_present,
            "baseline": "R8 (0/10, text-only 10/10) for B1/B2; R1 (4/10, text-only 2/10) for B3. "
                        "R0 scored 6/10 on these tasks and is NOT the baseline (DESIGN section 0.1).",
            "analysis": "Pre-registered (O3 DESIGN.md section 4). Baselines reused from step 6 "
                        "(different run epoch — caveat in RESULTS.md). McNemar exploratory only. "
                        "No pooled tests across branches.",
        },
        "branches": {b: summarise_branch(results, b, task_order, manifest)
                     for b in branches_present},
        "baselines_reused": baselines,
        "grid": [
            {"task_id": t,
             **{b: (results[(b, t)]["classification"] if (b, t) in results else None)
                for b in branches_present},
             "R8_reused": baselines["R8"]["per_task_classification"].get(t),
             "R1_reused": baselines["R1"]["per_task_classification"].get(t)}
            for t in task_order],
    }

    # McNemar per branch vs its reused baseline.
    summary["mcnemar_exploratory"] = {}
    for b in branches_present:
        base = BASELINE_FOR[b]
        summary["mcnemar_exploratory"][f"{b}_vs_{base}"] = paired_mcnemar_vs_baseline(
            results, b, baselines[base]["per_task_classification"], task_order)

    # Verdicts (mechanical, pre-registered rules).
    summary["verdicts"] = {}
    for b in ("B1", "B2"):
        if b in summary["branches"]:
            v, crit = verdict_for(summary["branches"][b])
            summary["verdicts"][b] = {"verdict": v, "criteria": crit,
                                      "baseline": "R8"}
    if "B3" in summary["branches"]:
        b3 = summary["branches"]["B3"]
        harms = b3["overall"]["n_pass"] <= 2
        summary["verdicts"]["B3"] = {
            "verdict": "SUFFIX-HARMS-WORKING-HARNESS" if harms else "CONTROL-OK",
            "pass": b3["overall"]["n_pass"], "baseline_R1_pass": 4,
            "note": ("B3 <= 2/10 vs R1 4/10: record 'suffix harms a working "
                     "harness' (DESIGN section 4)." if harms else
                     "B3 did not drop >= 2 below R1 4/10.")}

    (LOG_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- summary.md ----
    lines = ["# O3 opencode prompt intervention — summary (pre-registered analysis)", ""]
    lines.append("Model: base only (fixed). Tasks: 10 (same as step 6). One run per cell.")
    lines.append("Baselines REUSED from step 6 (not re-run): R8 0/10 text-only 10/10; R1 4/10 text-only 2/10.")
    lines.append("")
    lines.append("## Per-branch Pass@1 (scored runs only; INFRA excluded)")
    lines.append("")
    lines.append("| Branch | Recipe + suffix | Pass@1 | Wilson 95% | Text-only | Text-only Wilson 95% | Tools | Mean steps | INFRA |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for b in branches_present:
        e = summary["branches"][b]
        o = e["overall"]
        nt = e["no_tool_mechanism"]
        tools = ", ".join(f"{k}:{v}" for k, v in o["tool_call_totals"].items()) or "—"
        lines.append(f"| {b} | {e['recipe']} + {e['suffix']} | {o['n_pass']}/{o['n_scored']} ({o['pass_rate']:.2f}) "
                     f"| [{o['wilson95'][0]:.2f}, {o['wilson95'][1]:.2f}] "
                     f"| {nt['n_no_tool_calls']}/{nt['n_scored']} "
                     f"| [{nt['text_only_wilson95'][0]:.2f}, {nt['text_only_wilson95'][1]:.2f}] "
                     f"| {tools} | {o['avg_steps_scored']} | {o['n_infra']} |")
    lines.append("")
    lines.append("## Reused baselines (step 6, not re-run)")
    lines.append("")
    for rid in ("R8", "R1"):
        e = baselines[rid]
        o = e["overall"]
        nt = e["no_tool_mechanism"]
        tools = ", ".join(f"{k}:{v}" for k, v in o["tool_call_totals"].items()) or "—"
        lines.append(f"- {rid}: Pass@1 {o['n_pass']}/{o['n_scored']}, text-only {nt['n_no_tool_calls']}/{nt['n_scored']}, tools {tools}")
    lines.append("")
    lines.append("## Per-task x branch grid (PASS/FAIL/INFRA; R8/R1 columns reused)")
    lines.append("")
    cols = branches_present + ["R8_reused", "R1_reused"]
    header = "| task_id | " + " | ".join(cols) + " |"
    lines.append(header)
    lines.append("|---|---|" + "---|" * (len(cols) - 1) + "|")
    for row in summary["grid"]:
        lines.append("| " + row["task_id"] + " | " + " | ".join(str(row[c]) for c in cols) + " |")
    lines.append("")
    lines.append("## McNemar, EXPLORATORY (paired vs reused baseline)")
    lines.append("")
    for k, comp in summary["mcnemar_exploratory"].items():
        lines.append(f"- {k}: {comp['paired_tasks']} pairs, gains {comp['gains_fail_to_pass']}, "
                     f"losses {comp['losses_pass_to_fail']}, same_pass {comp['same_pass']}, "
                     f"same_fail {comp['same_fail']}, p (exact, 2-sided) = {comp['exact_p_two_sided']}")
    lines.append("")
    lines.append("With the baseline at 0/10, 3 wins / 0 losses gives p=0.25 — never significant. "
                "Language allowed: 'the intervention descriptively reduced text-only from 10/10 to X/10 on 10 tasks' — no more.")
    lines.append("")
    lines.append("## Verdicts (pre-registered DESIGN section 4 rules)")
    lines.append("")
    for b, v in summary["verdicts"].items():
        lines.append(f"- {b}: **{v['verdict']}** — {json.dumps(v, ensure_ascii=False)}")
    lines.append("")
    (LOG_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({b: summary["branches"][b]["overall"] for b in branches_present}, indent=1))
    print("verdicts:", {b: v["verdict"] for b, v in summary["verdicts"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
