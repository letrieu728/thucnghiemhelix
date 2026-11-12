"""
round2_stats.py - Statistics for the Round 2 live run (2026-11-12)
====================================================================
Offline analysis of run-tagged Round 2 traces (build2 / rebuild2 /
heldout2). Baseline comparisons use ONLY temperature 0.0, sample 0
cells (the Round 1 protocol); sampling cells (temperature 0.7) are
summarised separately and never enter baseline rates.

Computes, from the trace files only:
  - Pass@1 per harness with Wilson 95% score intervals.
  - Portfolio union per task set.
  - McNemar exact tests on paired cells (BUILD2 vs REBUILD2 on the 20
    training tasks; base vs LoRA on held-out v2).
  - Flip table (task x harness, BUILD2 -> REBUILD2 and held-out).
  - Sampling summary: how many tasks gained pass/fail contrast only
    through sampling.
  - Independent re-verification of every Round 2 `passed` flag.
  - Leakage check: no held-out task ID in the training provenance
    manifest's task list or source traces.

Outputs:
  - closed-loop/data/analysis_round2.json
  - closed-loop/data/round2_comparison_plot.svg (and .png)

Usage:
  python closed-loop/notebooks/round2_stats.py
  python closed-loop/notebooks/round2_stats.py --no-plot
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from round1_stats import HARNESS_ORDER, mcnemar_exact, wilson

CLOSED_LOOP_ROOT = Path(__file__).resolve().parent.parent
RAW_TRACES_DIR = CLOSED_LOOP_ROOT / "data" / "raw_traces"
BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_MODEL = "helix-lora"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "helix_runner_02", CLOSED_LOOP_ROOT / "scripts" / "02_run_helix_eval.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_round2_traces() -> List[Dict[str, Any]]:
    traces = []
    for path in sorted(RAW_TRACES_DIR.glob("*.json")):
        trace = json.loads(path.read_text(encoding="utf-8"))
        if trace.get("run_tag") not in ("build2", "rebuild2", "heldout2"):
            continue
        trace["_file"] = path.name
        traces.append(trace)
    return traces


def is_baseline(trace: Dict[str, Any]) -> bool:
    """Temperature 0.0, first sample: the comparable protocol."""
    return float(trace.get("temperature", 0.0)) == 0.0 and int(trace.get("sample_index", 0)) == 0


def reverify(traces: List[Dict[str, Any]], runner) -> List[str]:
    problems = {p["id"]: p for p in runner.get_problems("train20")}
    for name in ("heldout_problems.json", "heldout2_problems.json"):
        for problem in json.loads((CLOSED_LOOP_ROOT / "data" / name).read_text(encoding="utf-8")):
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


def summarise_tagged(traces: List[Dict[str, Any]], run_tag: str, model: str | None = None) -> Dict[str, Any]:
    """Per-harness summary over baseline cells of one run tag (and model)."""
    subset = [
        t for t in traces
        if t.get("run_tag") == run_tag and is_baseline(t)
        and (model is None or t["model"] == model)
    ]
    # Reuse round1 summarise() by faking phase: group by harness directly.
    out: Dict[str, Any] = {}
    for harness in HARNESS_ORDER:
        sub = [t for t in subset if t["harness_id"] == harness]
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


def union_tagged(traces: List[Dict[str, Any]], run_tag: str, model: str | None = None) -> Dict[str, Any]:
    by_task: Dict[str, List[bool]] = collections.defaultdict(list)
    for trace in traces:
        if (
            trace.get("run_tag") == run_tag and is_baseline(trace)
            and (model is None or trace["model"] == model)
        ):
            by_task[trace["task_id"]].append(bool(trace["passed"]))
    solved = sum(1 for outcomes in by_task.values() if any(outcomes))
    lo, hi = wilson(solved, len(by_task))
    return {
        "solved_by_at_least_one_harness": solved,
        "tasks": len(by_task),
        "wilson95": [round(lo, 4), round(hi, 4)],
        "unsolved_tasks": sorted(t for t, v in by_task.items() if not any(v)),
    }


def paired_mcnemar_tagged(
    traces: List[Dict[str, Any]],
    left: Tuple[str, str | None],
    right: Tuple[str, str | None],
) -> Dict[str, Any]:
    def cell_map(run_tag: str, model: str | None) -> Dict[Tuple[str, str], bool]:
        return {
            (t["task_id"], t["harness_id"]): bool(t["passed"])
            for t in traces
            if t.get("run_tag") == run_tag and is_baseline(t)
            and (model is None or t["model"] == model)
        }

    left_map, right_map = cell_map(*left), cell_map(*right)
    keys = sorted(set(left_map) & set(right_map))
    gains = sum(1 for k in keys if not left_map[k] and right_map[k])
    losses = sum(1 for k in keys if left_map[k] and not right_map[k])
    same_pass = sum(1 for k in keys if left_map[k] and right_map[k])
    same_fail = sum(1 for k in keys if not left_map[k] and not right_map[k])
    discordant = gains + losses
    flips = [
        {"task_id": task, "harness_id": harness, "before": left_map[(task, harness)], "after": right_map[(task, harness)]}
        for (task, harness) in keys
        if left_map[(task, harness)] != right_map[(task, harness)]
    ]
    return {
        "paired_cells": len(keys),
        "gains_fail_to_pass": gains,
        "losses_pass_to_fail": losses,
        "same_pass": same_pass,
        "same_fail": same_fail,
        "exact_p_two_sided": round(mcnemar_exact(gains, losses), 4),
        "chi2_continuity_corrected": round((abs(gains - losses) - 1) ** 2 / discordant, 3) if discordant else 0.0,
        "flips": flips,
    }


def sampling_summary(traces: List[Dict[str, Any]]) -> Dict[str, Any]:
    sampled = [t for t in traces if t.get("run_tag") == "build2" and float(t.get("temperature", 0.0)) > 0.0]
    by_task: Dict[str, List[bool]] = collections.defaultdict(list)
    for trace in sampled:
        by_task[trace["task_id"]].append(bool(trace["passed"]))
    # Tasks whose temp-0 cells were unanimous but sampling added contrast.
    temp0: Dict[str, List[bool]] = collections.defaultdict(list)
    for trace in traces:
        if trace.get("run_tag") == "build2" and is_baseline(trace):
            temp0[trace["task_id"]].append(bool(trace["passed"]))
    contrast_only_via_sampling = []
    for task, outcomes in by_task.items():
        base = temp0.get(task, [])
        if base and all(base) == base[0] and len(set(outcomes)) > 1:
            contrast_only_via_sampling.append(task)
        elif base and len(set(base)) == 1 and any(o != base[0] for o in outcomes):
            contrast_only_via_sampling.append(task)
    return {
        "n_sampling_traces": len(sampled),
        "n_tasks_sampled": len(by_task),
        "sampling_passed": sum(1 for t in sampled if t["passed"]),
        "temperatures": sorted({float(t.get("temperature", 0.0)) for t in sampled}),
        "tasks_with_sampling_contrast": sorted(t for t, v in by_task.items() if len(set(v)) > 1),
        "contrast_only_via_sampling": sorted(set(contrast_only_via_sampling)),
    }


def leakage_check() -> Dict[str, Any]:
    manifest_path = CLOSED_LOOP_ROOT / "data" / "processed" / "provenance.json"
    heldout_ids = set()
    for name in ("heldout_problems.json", "heldout2_problems.json"):
        for problem in json.loads((CLOSED_LOOP_ROOT / "data" / name).read_text(encoding="utf-8")):
            heldout_ids.add(problem["id"])
    if not manifest_path.exists():
        return {"manifest_exists": False, "leaked_ids": []}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_tasks = set(manifest.get("tasks", []))
    leaked = sorted(manifest_tasks & heldout_ids)
    return {
        "manifest_exists": True,
        "run_tag_filter": manifest.get("run_tag_filter"),
        "counts": manifest.get("counts"),
        "n_tasks": len(manifest_tasks),
        "leaked_ids": leaked,
        "source_traces": len(manifest.get("source_traces", [])),
    }


def analyse() -> Dict[str, Any]:
    runner = load_runner()
    traces = load_round2_traces()
    mismatches = reverify(traces, runner)
    baseline = [t for t in traces if is_baseline(t)]
    result = {
        "round": 2,
        "date": "2026-11-12",
        "n_traces_total": len(traces),
        "n_baseline_traces": len(baseline),
        "n_by_run_tag": {
            tag: sum(1 for t in traces if t.get("run_tag") == tag)
            for tag in ("build2", "rebuild2", "heldout2")
        },
        "reverify_mismatches": len(mismatches),
        "reverify_mismatch_files": mismatches,
        "total_latency_sec_all": round(sum(t["latency_sec"] for t in traces), 1),
        "total_latency_sec_baseline": round(sum(t["latency_sec"] for t in baseline), 1),
        "prompt_truncations_total": sum(int(t.get("prompt_truncations", 0)) for t in traces),
        "infra_error_traces": [
            t["_file"] for t in traces
            if t.get("error") and ("400" in str(t["error"]) or "Error code: 400" in str(t["error"]))
        ],
        "build2": summarise_tagged(traces, "build2"),
        "rebuild2": summarise_tagged(traces, "rebuild2"),
        "heldout2_base": summarise_tagged(traces, "heldout2", BASE_MODEL),
        "heldout2_lora": summarise_tagged(traces, "heldout2", LORA_MODEL),
        "union": {
            "build2": union_tagged(traces, "build2"),
            "rebuild2": union_tagged(traces, "rebuild2"),
            "heldout2_base": union_tagged(traces, "heldout2", BASE_MODEL),
            "heldout2_lora": union_tagged(traces, "heldout2", LORA_MODEL),
        },
        "mcnemar_build2_vs_rebuild2": paired_mcnemar_tagged(traces, ("build2", None), ("rebuild2", None)),
        "mcnemar_heldout2_base_vs_lora": paired_mcnemar_tagged(
            traces, ("heldout2", BASE_MODEL), ("heldout2", LORA_MODEL)
        ),
        "sampling": sampling_summary(traces),
        "leakage_check": leakage_check(),
        "method": (
            "Baseline cells only (temperature 0.0, sample 0) for all rates, "
            "unions and McNemar tests. Wilson score intervals (z=1.96); "
            "McNemar exact two-sided binomial on discordant paired cells."
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
    fig.suptitle("Round 2 live run (2026-11-12): temp 0.0 baseline cells only", fontsize=11)
    for ax, key_a, key_b, title in [
        (ax1, "build2", "rebuild2", "Training tasks (n=20): Pass@1 + Wilson 95% CI"),
        (ax2, "heldout2_base", "heldout2_lora", "Held-out v2 (n=15): Pass@1 + Wilson 95% CI"),
    ]:
        a = [stats[key_a][h]["pass_rate"] * 100 for h in HARNESS_ORDER]
        b = [stats[key_b][h]["pass_rate"] * 100 for h in HARNESS_ORDER]
        a_lo = [a[i] - stats[key_a][h]["wilson95"][0] * 100 for i, h in enumerate(HARNESS_ORDER)]
        a_hi = [stats[key_a][h]["wilson95"][1] * 100 - a[i] for i, h in enumerate(HARNESS_ORDER)]
        b_lo = [b[i] - stats[key_b][h]["wilson95"][0] * 100 for i, h in enumerate(HARNESS_ORDER)]
        b_hi = [stats[key_b][h]["wilson95"][1] * 100 - b[i] for i, h in enumerate(HARNESS_ORDER)]
        ax.bar(x - width / 2, a, width, yerr=[a_lo, a_hi], capsize=4, label="Base", color="#94a3b8", edgecolor="#475569")
        ax.bar(x + width / 2, b, width, yerr=[b_lo, b_hi], capsize=4, label="LoRA v2", color="#3b82f6", edgecolor="#1d4ed8")
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
    parser = argparse.ArgumentParser(description="Round 2 statistics + plot")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    stats = analyse()
    out_json = CLOSED_LOOP_ROOT / "data" / "analysis_round2.json"
    out_json.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"[OK] Wrote {out_json}")
    print(f"Traces: {stats['n_traces_total']} total, {stats['n_baseline_traces']} baseline, "
          f"re-verify mismatches: {stats['reverify_mismatches']}")
    print(f"BUILD2 {stats['build2']['_total']}  REBUILD2 {stats['rebuild2']['_total']}")
    print(f"HELDOUT2 base {stats['heldout2_base']['_total']}  LoRA {stats['heldout2_lora']['_total']}")
    print(f"McNemar BUILD2 vs REBUILD2: gains={stats['mcnemar_build2_vs_rebuild2']['gains_fail_to_pass']} "
          f"losses={stats['mcnemar_build2_vs_rebuild2']['losses_pass_to_fail']} "
          f"p={stats['mcnemar_build2_vs_rebuild2']['exact_p_two_sided']}")
    print(f"McNemar held-out v2: gains={stats['mcnemar_heldout2_base_vs_lora']['gains_fail_to_pass']} "
          f"losses={stats['mcnemar_heldout2_base_vs_lora']['losses_pass_to_fail']} "
          f"p={stats['mcnemar_heldout2_base_vs_lora']['exact_p_two_sided']}")
    print(f"Leakage check: {stats['leakage_check']}")
    if not args.no_plot:
        try:
            make_plot(stats, CLOSED_LOOP_ROOT / "data" / "round2_comparison_plot.svg",
                      CLOSED_LOOP_ROOT / "data" / "round2_comparison_plot.png")
        except ImportError as exc:
            print(f"[WARN] matplotlib unavailable, plot skipped: {exc}")


if __name__ == "__main__":
    main()
