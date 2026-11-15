#!/usr/bin/env python3
"""Build the fixed judge cell list for the HELIX rows-2+5 supplement.

Primary list: every PASS baseline cell (temperature 0.0, sample 0) that
carries a Round-2 claim -- REBUILD2 (66) + held-out v2, both models
(50 base + 53 LoRA = 103) -- 169 cells in total. BUILD2 baseline PASS
cells (60) are NOT in the primary list: the critic question concerns
the LoRA results and the held-out comparison, and re-labelling the
base training-task passes adds cost without changing any claim. Their
count is recorded in the metadata for transparency.

Fallback list (used only if the GPU cost checkpoint in GPU_RUN_PLAN.md
triggers): the PASS sides of all 15 flip pairs (BUILD2->REBUILD2 and
held-out base->LoRA) + a seeded random sample of 40 further primary
cells (seed 20261115). A both-sides variant (30 flip traces + the same
40) is also emitted for the worker's choice; the PASS-only fallback is
the recommended one.

Deterministic: sorted filename order, fixed seed. Offline, read-only
except for writing judge_list.json next to this script.

Usage:
  python3 build_judge_list.py [--out-dir DIR]
"""

import argparse
import json
import random
from pathlib import Path

SCRIPT_VERSION = "build_judge_list.py v1 (2026-11-15)"
FALLBACK_SEED = 20261115
FALLBACK_RANDOM_N = 40
BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
LORA_MODEL = "helix-lora"


def entry(trace, fname):
    return {
        "trace_file": fname,
        "phase": trace.get("phase"),
        "run_tag": trace.get("run_tag") or "",
        "task_id": trace.get("task_id"),
        "task_title": trace.get("task_title"),
        "harness_id": trace.get("harness_id"),
        "model": trace.get("model"),
        "passed": trace.get("passed"),
        "steps": trace.get("steps"),
        "temperature": trace.get("temperature", 0.0),
        "sample_index": trace.get("sample_index", 0),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    closed_loop = here.parent.parent / "closed-loop"
    parser.add_argument("--traces-dir", default=str(
        closed_loop / "data" / "raw_traces"))
    parser.add_argument("--out-dir", default=str(here))
    args = parser.parse_args()

    traces = {}
    for path in sorted(Path(args.traces_dir).glob("*.json")):
        traces[path.name] = json.loads(path.read_text(encoding="utf-8"))

    def is_baseline(trace):
        return trace.get("temperature", 0.0) == 0.0 \
            and trace.get("sample_index", 0) == 0

    # Primary: REBUILD2 PASS + HELDOUT2 PASS (both models), baseline only.
    primary = []
    for fname in sorted(traces):
        trace = traces[fname]
        if not is_baseline(trace) or trace.get("passed") is not True:
            continue
        if trace.get("run_tag") in ("rebuild2", "heldout2"):
            primary.append(entry(trace, fname))

    # Flip pairs (baseline cells only).
    def cell_map(run_tag, model=None):
        out = {}
        for fname in sorted(traces):
            trace = traces[fname]
            if trace.get("run_tag") != run_tag or not is_baseline(trace):
                continue
            if model is not None and trace.get("model") != model:
                continue
            out[(trace["task_id"], trace["harness_id"])] = (fname, trace)
        return out

    build2 = cell_map("build2")
    rebuild2 = cell_map("rebuild2")
    held_base = cell_map("heldout2", BASE_MODEL)
    held_lora = cell_map("heldout2", LORA_MODEL)

    flips = []
    for label, before, after in (("train_BUILD2_to_REBUILD2", build2, rebuild2),
                                 ("heldout2_base_to_LoRA", held_base, held_lora)):
        for key in sorted(before):
            fname_b, trace_b = before[key]
            fname_a, trace_a = after[key]
            if trace_b["passed"] != trace_a["passed"]:
                direction = "gain" if trace_a["passed"] else "loss"
                pass_side = fname_a if trace_a["passed"] else fname_b
                fail_side = fname_b if trace_a["passed"] else fname_a
                flips.append({
                    "comparison": label,
                    "task_id": key[0],
                    "harness_id": key[1],
                    "direction": direction,
                    "before_trace_file": fname_b,
                    "after_trace_file": fname_a,
                    "pass_side_trace_file": pass_side,
                    "fail_side_trace_file": fail_side,
                })

    flip_pass_files = sorted({f["pass_side_trace_file"] for f in flips})
    primary_files = {e["trace_file"] for e in primary}
    flip_pass_in_primary = [f for f in flip_pass_files if f in primary_files]
    flip_pass_outside_primary = [f for f in flip_pass_files
                                 if f not in primary_files]

    # Fallback random sample: seeded, from primary cells excluding the
    # flip PASS sides already in the primary list.
    pool = sorted(primary_files - set(flip_pass_in_primary))
    rng = random.Random(FALLBACK_SEED)
    sampled = sorted(rng.sample(pool, FALLBACK_RANDOM_N))

    fallback_entries = []
    for fname in flip_pass_files:
        item = entry(traces[fname], fname)
        item["fallback_reason"] = "flip_pass_side"
        fallback_entries.append(item)
    for fname in sampled:
        item = entry(traces[fname], fname)
        item["fallback_reason"] = "seeded_random_sample"
        fallback_entries.append(item)
    fallback_entries.sort(key=lambda e: e["trace_file"])

    # Both-sides variant: all 30 flip-pair traces + the same 40 sampled.
    both_sides_files = sorted({f["before_trace_file"] for f in flips}
                              | {f["after_trace_file"] for f in flips})
    fallback_both = []
    for fname in both_sides_files:
        item = entry(traces[fname], fname)
        item["fallback_reason"] = "flip_pair_both_sides"
        fallback_both.append(item)
    for fname in sampled:
        item = entry(traces[fname], fname)
        item["fallback_reason"] = "seeded_random_sample"
        fallback_both.append(item)
    fallback_both.sort(key=lambda e: e["trace_file"])

    # Transparency counts (all baseline, temp 0.0 / sample 0).
    def count_pass(run_tag, model=None):
        return sum(1 for t in traces.values()
                   if t.get("run_tag") == run_tag and is_baseline(t)
                   and t.get("passed") is True
                   and (model is None or t.get("model") == model))

    metadata = {
        "script": SCRIPT_VERSION,
        "primary_definition": ("PASS baseline cells (temp 0.0, sample 0) in "
                               "run_tag rebuild2 + heldout2 (both models)."),
        "primary_count": len(primary),
        "primary_breakdown": {
            "rebuild2_pass": count_pass("rebuild2"),
            "heldout2_base_pass": count_pass("heldout2", BASE_MODEL),
            "heldout2_lora_pass": count_pass("heldout2", LORA_MODEL),
        },
        "excluded_from_primary_counts": {
            "build2_baseline_pass": count_pass("build2"),
            "build2_sampling_pass": sum(
                1 for t in traces.values()
                if t.get("run_tag") == "build2"
                and t.get("temperature", 0.0) != 0.0
                and t.get("passed") is True),
            "round1_untagged_pass": sum(
                1 for t in traces.values()
                if not (t.get("run_tag") or "") and t.get("passed") is True),
        },
        "all_baseline_pass_total": sum(
            1 for t in traces.values()
            if is_baseline(t) and t.get("passed") is True),
        "flip_pairs": len(flips),
        "flip_pass_side_traces": len(flip_pass_files),
        "flip_pass_outside_primary": flip_pass_outside_primary,
        "fallback": {
            "seed": FALLBACK_SEED,
            "random_sample_n": FALLBACK_RANDOM_N,
            "total": len(fallback_entries),
            "flip_pass_sides": len(flip_pass_files),
            "both_sides_variant_total": len(fallback_both),
        },
    }

    out = {"metadata": metadata, "primary": primary, "flips": flips,
           "fallback": fallback_entries, "fallback_both_sides": fallback_both}
    out_path = Path(args.out_dir) / "judge_list.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    print(f"primary={len(primary)} flips={len(flips)} "
          f"flip_pass_sides={len(flip_pass_files)} "
          f"fallback={len(fallback_entries)} "
          f"fallback_both_sides={len(fallback_both)}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
