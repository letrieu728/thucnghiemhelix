"""
round1_stats.py - Supplementary statistics for the Round 1 live re-run (2026-11-12)
====================================================================================
Reproducible, offline analysis of the 160 committed Round 1 traces
(BUILD 40 + REBUILD 40 + held-out 80). Computes, from the trace files only:

  - Pass@1 per harness with Wilson 95% score intervals (n is tiny: 10/task
    set per harness, so intervals are wide and overlapping — reported, not hidden).
  - Portfolio union per task set: tasks solved by at least one harness,
    the post-hoc-oracle quantity the HELIX paper reports (79/100 on AtCoder).
  - McNemar exact (binomial) tests on paired cells: BUILD vs REBUILD
    (training tasks) and base vs LoRA (held-out v1).
  - Independent re-verification of every recorded `passed` flag by
    re-running the sandbox verifier on the committed solutions.

Outputs (no GPU, no network):
  - closed-loop/data/analysis_round1.json
  - closed-loop/data/rebuild_comparison_plot.svg (and .png when matplotlib
    is available; the SVG is the committed figure because it is text)

Usage:
  python closed-loop/notebooks/round1_stats.py
  python closed-loop/notebooks/round1_stats.py --no-plot
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

CLOSED_LOOP_ROOT = Path(__file__).resolve().parent.parent
RAW_TRACES_DIR = CLOSED_LOOP_ROOT / "data" / "raw_traces"
HARNESS_ORDER = ["minimal", "pi-mono", "hermes-agent", "opencode"]
BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_MODEL = "helix-lora"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "helix_runner_02", CLOSED_LOOP_ROOT / "scripts" / "02_run_helix_eval.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wilson(k: int, n: int, z: float = 1.959964) -> Tuple[float, float]:
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


def load_round1_traces() -> List[Dict[str, Any]]:
    """Round 1 traces only: untagged traces (no run_tag), phase build/rebuild/heldout."""
    traces = []
    for path in sorted(RAW_TRACES_DIR.glob("*.json")):
        trace = json.loads(path.read_text(encoding="utf-8"))
        if trace.get("run_tag"):
            continue
        trace["_file"] = path.name
        traces.append(trace)
    return traces


def reverify(traces: List[Dict[str, Any]], runner) -> List[str]:
    """Re-run the sandbox verifier on every committed solution."""
    problems = {p["id"]: p for p in runner.BENCHMARK_PROBLEMS}
    heldout_path = CLOSED_LOOP_ROOT / "data" / "heldout_problems.json"
    for problem in json.loads(heldout_path.read_text(encoding="utf-8")):
        problems[problem["id"]] = problem
    mismatches = []
    for trace in traces:
        problem = problems.get(trace["task_id"])
        if problem is None:
            mismatches.append(f"{trace['_file']}: unknown task {trace['task_id']}")
            continue
        code = runner.extract_python_code(trace.get("assistant_solution") or "")
        recomputed = False
        if code:
            recomputed, _ = runner.run_test_cases(code, problem["test_cases"])
        if recomputed != trace["passed"]:
            mismatches.append(
                f"{trace['_file']}: recomputed={recomputed} recorded={trace['passed']}"
            )
    return mismatches


def summarise(traces: List[Dict[str, Any]], phase: str, model: str | None = None) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for harness in HARNESS_ORDER:
        sub = [
            t for t in traces
            if t["phase"] == phase and t["harness_id"] == harness
            and (model is None or t["model"] == model)
        ]
        k = sum(1 for t in sub if t["passed"])
        lo, hi = wilson(k, len(sub))
        out[harness] = {
            "passed": k,
            "n": len(sub),
            "pass_rate": round(k / len(sub), 4) if sub else 0.0,
            "wilson95": [round(lo, 4), round(hi, 4)],
            "avg_steps": round(sum(t["steps"] for t in sub) / len(sub), 2) if sub else 0.0,
            "avg_latency_sec": round(sum(t["latency_sec"] for t in sub) / len(sub), 2) if sub else 0.0,
            "total_latency_sec": round(sum(t["latency_sec"] for t in sub), 1),
        }
    total_k = sum(v["passed"] for v in out.values())
    total_n = sum(v["n"] for v in out.values())
    lo, hi = wilson(total_k, total_n)
    out["_total"] = {
        "passed": total_k,
        "n": total_n,
        "pass_rate": round(total_k / total_n, 4) if total_n else 0.0,
        "wilson95": [round(lo, 4), round(hi, 4)],
        "total_latency_sec": round(sum(v["total_latency_sec"] for v in out.values()), 1),
    }
    return out


def portfolio_union(traces: List[Dict[str, Any]], phase: str, model: str | None = None) -> Dict[str, Any]:
    by_task: Dict[str, List[bool]] = collections.defaultdict(list)
    for trace in traces:
        if trace["phase"] == phase and (model is None or trace["model"] == model):
            by_task[trace["task_id"]].append(bool(trace["passed"]))
    solved = sum(1 for outcomes in by_task.values() if any(outcomes))
    lo, hi = wilson(solved, len(by_task))
    return {
        "solved_by_at_least_one_harness": solved,
        "tasks": len(by_task),
        "wilson95": [round(lo, 4), round(hi, 4)],
        "unsolved_tasks": sorted(t for t, v in by_task.items() if not any(v)),
    }


def paired_mcnemar(
    traces: List[Dict[str, Any]],
    left: Tuple[str, str | None],
    right: Tuple[str, str | None],
) -> Dict[str, Any]:
    def cell_map(phase: str, model: str | None) -> Dict[Tuple[str, str], bool]:
        return {
            (t["task_id"], t["harness_id"]): bool(t["passed"])
            for t in traces
            if t["phase"] == phase and (model is None or t["model"] == model)
        }

    left_map, right_map = cell_map(*left), cell_map(*right)
    keys = sorted(set(left_map) & set(right_map))
    gains = sum(1 for k in keys if not left_map[k] and right_map[k])
    losses = sum(1 for k in keys if left_map[k] and not right_map[k])
    same_pass = sum(1 for k in keys if left_map[k] and right_map[k])
    same_fail = sum(1 for k in keys if not left_map[k] and not right_map[k])
    discordant = gains + losses
    chi2_cc = round((abs(gains - losses) - 1) ** 2 / discordant, 3) if discordant else 0.0
    return {
        "paired_cells": len(keys),
        "gains_fail_to_pass": gains,
        "losses_pass_to_fail": losses,
        "same_pass": same_pass,
        "same_fail": same_fail,
        "exact_p_two_sided": round(mcnemar_exact(gains, losses), 4),
        "chi2_continuity_corrected": chi2_cc,
    }


def analyse() -> Dict[str, Any]:
    runner = load_runner()
    traces = load_round1_traces()
    mismatches = reverify(traces, runner)
    result = {
        "round": 1,
        "date": "2026-11-12",
        "n_traces": len(traces),
        "reverify_mismatches": len(mismatches),
        "reverify_mismatch_files": mismatches,
        "build": summarise(traces, "build"),
        "rebuild": summarise(traces, "rebuild"),
        "heldout_base": summarise(traces, "heldout", BASE_MODEL),
        "heldout_lora": summarise(traces, "heldout", LORA_MODEL),
        "union": {
            "build": portfolio_union(traces, "build"),
            "rebuild": portfolio_union(traces, "rebuild"),
            "heldout_base": portfolio_union(traces, "heldout", BASE_MODEL),
            "heldout_lora": portfolio_union(traces, "heldout", LORA_MODEL),
        },
        "mcnemar_build_vs_rebuild": paired_mcnemar(traces, ("build", None), ("rebuild", None)),
        "mcnemar_heldout_base_vs_lora": paired_mcnemar(
            traces, ("heldout", BASE_MODEL), ("heldout", LORA_MODEL)
        ),
        "total_latency_sec": round(sum(t["latency_sec"] for t in traces), 1),
        "method": (
            "Wilson score intervals (z=1.96); McNemar exact two-sided binomial "
            "on discordant paired cells; union counts tasks solved by >=1 harness. "
            "Intervals are wide because n=10 per harness; overlap means the "
            "BUILD->REBUILD deltas are not distinguishable from sampling noise."
        ),
    }
    return result


def make_plot(stats: Dict[str, Any], svg_path: Path, png_path: Path | None = None) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = ["Minimal", "Pi Mono", "Hermes", "OpenCode"]
    x = np.arange(len(HARNESS_ORDER))
    width = 0.35
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=200)
    fig.suptitle("Round 1 live re-run (2026-11-12): BUILD vs REBUILD, n=10 per harness", fontsize=11)

    for ax, key_a, key_b, title in [
        (ax1, "build", "rebuild", "Training tasks: Pass@1 with Wilson 95% CI"),
        (ax2, "heldout_base", "heldout_lora", "Held-out v1: Pass@1 with Wilson 95% CI (ceiling)"),
    ]:
        a = [stats[key_a][h]["pass_rate"] * 100 for h in HARNESS_ORDER]
        b = [stats[key_b][h]["pass_rate"] * 100 for h in HARNESS_ORDER]
        a_lo = [a[i] - stats[key_a][h]["wilson95"][0] * 100 for i, h in enumerate(HARNESS_ORDER)]
        a_hi = [stats[key_a][h]["wilson95"][1] * 100 - a[i] for i, h in enumerate(HARNESS_ORDER)]
        b_lo = [b[i] - stats[key_b][h]["wilson95"][0] * 100 for i, h in enumerate(HARNESS_ORDER)]
        b_hi = [stats[key_b][h]["wilson95"][1] * 100 - b[i] for i, h in enumerate(HARNESS_ORDER)]
        ax.bar(x - width / 2, a, width, yerr=[a_lo, a_hi], capsize=4, label="Base", color="#94a3b8", edgecolor="#475569")
        ax.bar(x + width / 2, b, width, yerr=[b_lo, b_hi], capsize=4, label="LoRA", color="#3b82f6", edgecolor="#1d4ed8")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=12)
        ax.set_ylim(0, 118)
        ax.set_ylabel("Pass@1 (%)")
        ax.set_title(title, fontsize=10)
        ax.legend()
    fig.tight_layout()
    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    print(f"[OK] Saved {svg_path}")
    if png_path is not None:
        fig.savefig(png_path, bbox_inches="tight")
        print(f"[OK] Saved {png_path}")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Round 1 supplementary statistics + plot")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    stats = analyse()
    out_json = CLOSED_LOOP_ROOT / "data" / "analysis_round1.json"
    out_json.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"[OK] Wrote {out_json}")
    print(f"Traces: {stats['n_traces']}, re-verify mismatches: {stats['reverify_mismatches']}")
    print(f"Union BUILD {stats['union']['build']['solved_by_at_least_one_harness']}/{stats['union']['build']['tasks']} "
          f"-> REBUILD {stats['union']['rebuild']['solved_by_at_least_one_harness']}/{stats['union']['rebuild']['tasks']}")
    print(f"McNemar BUILD vs REBUILD: {stats['mcnemar_build_vs_rebuild']}")
    print(f"McNemar held-out base vs LoRA: {stats['mcnemar_heldout_base_vs_lora']}")
    if not args.no_plot:
        try:
            make_plot(stats, CLOSED_LOOP_ROOT / "data" / "rebuild_comparison_plot.svg",
                      CLOSED_LOOP_ROOT / "data" / "rebuild_comparison_plot.png")
        except ImportError as exc:
            print(f"[WARN] matplotlib unavailable, plot skipped: {exc}")


if __name__ == "__main__":
    main()
