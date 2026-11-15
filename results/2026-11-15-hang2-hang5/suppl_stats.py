#!/usr/bin/env python3
"""Statistics for the HELIX supplement run, rows 2+5 (2026-11-15).

NOT round 3. Compares the new `suppl` traces (new adapter, DPO 19 pairs)
against the frozen Round 2 baselines. Baseline cells only: temperature
0.0, sample 0. Reuses reverify/summarise logic from round2_stats.py
(same sandbox re-run of every recorded `passed` flag) via import; the
judge-label table is a separate sensitivity analysis and never enters
the Pass@1 / McNemar tables.

Usage (from repo root thucnghiemhelix/, AFTER all suppl traces exist):
  python3 results/2026-11-15-hang2-hang5/suppl_stats.py [--no-plot]
Outputs: results/2026-11-15-hang2-hang5/suppl_stats.json (+ plot svg/png)
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent.parent.parent
SUPPL = Path(__file__).resolve().parent
NOTEBOOKS = ROOT / "closed-loop" / "notebooks"
sys.path.insert(0, str(NOTEBOOKS))
import round2_stats as r2  # noqa: E402  (needs round1_stats on sys.path)

BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_MODEL = "helix-lora"


def load_all_traces() -> List[Dict[str, Any]]:
    traces = []
    for path in sorted(r2.RAW_TRACES_DIR.glob("*.json")):
        trace = json.loads(path.read_text(encoding="utf-8"))
        trace["_file"] = path.name
        traces.append(trace)
    return traces


def summarise(traces, run_tag, phase=None, model=None):
    subset = [
        t for t in traces
        if t.get("run_tag") == run_tag and r2.is_baseline(t)
        and (phase is None or t.get("phase") == phase)
        and (model is None or t["model"] == model)
    ]
    out: Dict[str, Any] = {}
    for harness in r2.HARNESS_ORDER:
        sub = [t for t in subset if t["harness_id"] == harness]
        k = sum(1 for t in sub if t["passed"])
        lo, hi = r2.wilson(k, len(sub))
        out[harness] = {
            "passed": k, "n": len(sub),
            "pass_rate": round(k / len(sub), 4) if sub else 0.0,
            "wilson95": [round(lo, 4), round(hi, 4)],
            "avg_steps": round(sum(t["steps"] for t in sub) / len(sub), 2) if sub else 0.0,
            "avg_latency_sec": round(sum(t["latency_sec"] for t in sub) / len(sub), 2) if sub else 0.0,
            "total_latency_sec": round(sum(t["latency_sec"] for t in sub), 1),
        }
    total_k = sum(v["passed"] for v in out.values())
    total_n = sum(v["n"] for v in out.values())
    lo, hi = r2.wilson(total_k, total_n)
    out["_total"] = {
        "passed": total_k, "n": total_n,
        "pass_rate": round(total_k / total_n, 4) if total_n else 0.0,
        "wilson95": [round(lo, 4), round(hi, 4)],
        "total_latency_sec": round(sum(v["total_latency_sec"] for v in out.values()), 1),
    }
    return out


def union(traces, run_tag, phase=None, model=None):
    by_task: Dict[str, List[bool]] = collections.defaultdict(list)
    for t in traces:
        if (t.get("run_tag") == run_tag and r2.is_baseline(t)
                and (phase is None or t.get("phase") == phase)
                and (model is None or t["model"] == model)):
            by_task[t["task_id"]].append(bool(t["passed"]))
    solved = sum(1 for v in by_task.values() if any(v))
    lo, hi = r2.wilson(solved, len(by_task))
    return {
        "solved_by_at_least_one_harness": solved, "tasks": len(by_task),
        "wilson95": [round(lo, 4), round(hi, 4)],
        "unsolved_tasks": sorted(t for t, v in by_task.items() if not any(v)),
    }


def paired(traces, left, right):
    def cell_map(run_tag, phase, model):
        return {
            (t["task_id"], t["harness_id"]): bool(t["passed"])
            for t in traces
            if t.get("run_tag") == run_tag and r2.is_baseline(t)
            and (phase is None or t.get("phase") == phase)
            and (model is None or t["model"] == model)
        }
    lm, rm = cell_map(*left), cell_map(*right)
    keys = sorted(set(lm) & set(rm))
    gains = sum(1 for k in keys if not lm[k] and rm[k])
    losses = sum(1 for k in keys if lm[k] and not rm[k])
    return {
        "paired_cells": len(keys),
        "gains_fail_to_pass": gains,
        "losses_pass_to_fail": losses,
        "same_pass": sum(1 for k in keys if lm[k] and rm[k]),
        "same_fail": sum(1 for k in keys if not lm[k] and not rm[k]),
        "exact_p_two_sided": round(r2.mcnemar_exact(gains, losses), 4),
        "flips": [
            {"task_id": task, "harness_id": harness, "before": lm[(task, harness)], "after": rm[(task, harness)]}
            for (task, harness) in keys if lm[(task, harness)] != rm[(task, harness)]
        ],
    }


def judge_analysis():
    judge_path = SUPPL / "judge_runs" / "2026-11-15" / "judge_results.jsonl"
    rows = [json.loads(l) for l in judge_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    heur = json.loads((SUPPL / "heuristic_labels.json").read_text(encoding="utf-8"))
    hmap = {row["trace_file"]: row["heuristic_label"] for row in heur["rows"]}
    by_group: Dict[Tuple[str, str, str], Dict[str, int]] = collections.defaultdict(collections.Counter)
    for r in rows:
        by_group[(r["run_tag"], r["model"], r["harness_id"])][r["label"]] += 1
    parsed = [r for r in rows if r["label"] != "unparseable"]
    agree = sum(1 for r in parsed if hmap[r["trace_file"]] == r["label"])
    return {
        "n_judged": len(rows),
        "labels": dict(collections.Counter(r["label"] for r in rows)),
        "unparseable_files": [r["trace_file"] for r in rows if r["label"] == "unparseable"],
        "unparseable_rate": round(sum(1 for r in rows if r["label"] == "unparseable") / len(rows), 4) if rows else 0.0,
        "latency_sec_total": round(sum(r["latency_sec"] for r in rows), 1),
        "latency_sec_mean": round(sum(r["latency_sec"] for r in rows) / len(rows), 3) if rows else 0.0,
        "retries_total": sum(r["retries"] for r in rows),
        "by_run_tag_model_harness": {
            f"{k[0]}|{k[1]}|{k[2]}": dict(v) for k, v in sorted(by_group.items())
        },
        "heuristic_agreement_parsed": {
            "agree": agree, "n": len(parsed),
            "rate": round(agree / len(parsed), 4) if parsed else 0.0,
        },
        "heuristic_labels_on_judge_set": dict(collections.Counter(hmap[r["trace_file"]] for r in rows)),
        "non_clean_rows": [
            {"trace_file": r["trace_file"], "label": r["label"], "criteria": r["criteria"],
             "reason": r["reason"], "evidence": r["evidence"]}
            for r in rows if r["label"] not in ("clean",)
        ],
        "note": ("Judge labels are a separate sensitivity analysis (7B model, "
                 "same family as the solutions). They never change any passed flag."),
    }


def analyse() -> Dict[str, Any]:
    runner = r2.load_runner()
    traces = load_all_traces()
    suppl = [t for t in traces if t.get("run_tag") == "suppl"]
    mismatches = r2.reverify(suppl, runner)
    suppl_rebuild = [t for t in suppl if t.get("phase") == "rebuild"]
    suppl_heldout = [t for t in suppl if t.get("phase") == "heldout"]
    result = {
        "run": "supplement rows 2+5 (NOT round 3)",
        "date": "2026-11-15",
        "n_suppl_traces": len(suppl),
        "n_suppl_rebuild": len(suppl_rebuild),
        "n_suppl_heldout": len(suppl_heldout),
        "suppl_all_live": all(t.get("mode") == "live" for t in suppl),
        "suppl_models": sorted({t["model"] for t in suppl}),
        "suppl_temperatures": sorted({float(t.get("temperature", 0.0)) for t in suppl}),
        "suppl_baseline_cells": sum(1 for t in suppl if r2.is_baseline(t)),
        "reverify_mismatches_suppl": len(mismatches),
        "reverify_mismatch_files": mismatches,
        "prompt_truncations_suppl": sum(int(t.get("prompt_truncations", 0)) for t in suppl),
        "infra_error_traces_suppl": [
            t["_file"] for t in suppl
            if t.get("error") and ("400" in str(t["error"]) or "Error code: 400" in str(t["error"]))
        ],
        "rebuild_suppl": summarise(traces, "suppl", phase="rebuild", model=LORA_MODEL),
        "heldout_suppl": summarise(traces, "suppl", phase="heldout", model=LORA_MODEL),
        "build2_baseline": summarise(traces, "build2"),
        "rebuild2_baseline": summarise(traces, "rebuild2"),
        "heldout2_base_baseline": summarise(traces, "heldout2", model=BASE_MODEL),
        "heldout2_lora_baseline": summarise(traces, "heldout2", model=LORA_MODEL),
        "union": {
            "rebuild_suppl": union(traces, "suppl", phase="rebuild", model=LORA_MODEL),
            "heldout_suppl": union(traces, "suppl", phase="heldout", model=LORA_MODEL),
            "build2": union(traces, "build2"),
            "rebuild2": union(traces, "rebuild2"),
            "heldout2_base": union(traces, "heldout2", model=BASE_MODEL),
            "heldout2_lora": union(traces, "heldout2", model=LORA_MODEL),
        },
        "mcnemar_build2_vs_rebuild_suppl": paired(traces, ("build2", None, None), ("suppl", "rebuild", LORA_MODEL)),
        "mcnemar_rebuild2_vs_rebuild_suppl": paired(traces, ("rebuild2", None, None), ("suppl", "rebuild", LORA_MODEL)),
        "mcnemar_heldout2_base_vs_suppl": paired(traces, ("heldout2", None, BASE_MODEL), ("suppl", "heldout", LORA_MODEL)),
        "mcnemar_heldout2_lora_vs_suppl": paired(traces, ("heldout2", None, LORA_MODEL), ("suppl", "heldout", LORA_MODEL)),
        "judge_label_analysis": judge_analysis(),
        "method": (
            "Baseline cells only (temperature 0.0, sample 0). Wilson score "
            "intervals (z=1.96); McNemar exact two-sided binomial on "
            "discordant paired cells. Re-verification re-runs every suppl "
            "passed flag in the sandbox via round2_stats.reverify."
        ),
    }
    return result


def make_plot(stats: Dict[str, Any], svg_path: Path, png_path: Path | None = None) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = ["Minimal", "Pi Mono", "Hermes", "OpenCode"]
    x = np.arange(len(r2.HARNESS_ORDER))
    width = 0.27
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), dpi=200)
    fig.suptitle("Supplement run rows 2+5 (2026-11-15): temp 0.0 baseline cells only", fontsize=11)
    for ax, keys, title in [
        (ax1, ["build2_baseline", "rebuild2_baseline", "rebuild_suppl"], "Training tasks (n=20): Pass@1 + Wilson 95% CI"),
        (ax2, ["heldout2_base_baseline", "heldout2_lora_baseline", "heldout_suppl"], "Held-out v2 (n=15): Pass@1 + Wilson 95% CI"),
    ]:
        names = ["Base", "LoRA v2", "LoRA suppl"] if "build2" in keys[0] else ["Base", "LoRA v2", "LoRA suppl"]
        colors = ["#94a3b8", "#3b82f6", "#16a34a"]
        edges = ["#475569", "#1d4ed8", "#166534"]
        for i, key in enumerate(keys):
            vals = [stats[key][h]["pass_rate"] * 100 for h in r2.HARNESS_ORDER]
            lo = [vals[j] - stats[key][h]["wilson95"][0] * 100 for j, h in enumerate(r2.HARNESS_ORDER)]
            hi = [stats[key][h]["wilson95"][1] * 100 - vals[j] for j, h in enumerate(r2.HARNESS_ORDER)]
            ax.bar(x + (i - 1) * width, vals, width, yerr=[lo, hi], capsize=3,
                   label=names[i], color=colors[i], edgecolor=edges[i])
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
    parser = argparse.ArgumentParser(description="Supplement-run statistics + plot")
    parser.add_argument("--no-plot", action="store_true")
    args = parser.parse_args()
    stats = analyse()
    out_json = SUPPL / "suppl_stats.json"
    out_json.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"[OK] Wrote {out_json}")
    print(f"suppl traces: {stats['n_suppl_traces']} (rebuild {stats['n_suppl_rebuild']}, heldout {stats['n_suppl_heldout']}), "
          f"re-verify mismatches: {stats['reverify_mismatches_suppl']}")
    print(f"REBUILD-suppl {stats['rebuild_suppl']['_total']}  HELDOUT-suppl {stats['heldout_suppl']['_total']}")
    for key in ("mcnemar_build2_vs_rebuild_suppl", "mcnemar_rebuild2_vs_rebuild_suppl",
                "mcnemar_heldout2_base_vs_suppl", "mcnemar_heldout2_lora_vs_suppl"):
        m = stats[key]
        print(f"{key}: gains={m['gains_fail_to_pass']} losses={m['losses_pass_to_fail']} p={m['exact_p_two_sided']}")
    if not args.no_plot:
        try:
            make_plot(stats, SUPPL / "suppl_comparison_plot.svg", SUPPL / "suppl_comparison_plot.png")
        except ImportError as exc:
            print(f"[WARN] matplotlib unavailable, plot skipped: {exc}")


if __name__ == "__main__":
    main()
