#!/usr/bin/env python3
"""Expanded DPO extraction for the HELIX rows-2+5 supplement (offline).

Implements DPO_RULES.md exactly -- no more, no less. Read that file
first: it is the pre-registered rule set, and this script is only its
mechanical execution. In particular:

- Provenance gate first (existing provenance.json hash/count check +
  independent live-only re-derivation via 03's own functions). Abort on
  any failure; never extract partially.
- Source: build2 BUILD traces only (160), live only, held-out IDs
  blocked. No Round-1, rebuild, held-out, dry-run or hand-written data.
- Rule A: sibling correctness pairs, max 3 per task, deterministic
  ordering + greedy coverage selection (DPO_RULES.md section 2).
- Rule B: fail->fixed pairs within a single trace, last sandbox-verified
  failing intermediate as rejected, max 1 per trace (section 3).
- No SFT re-extraction. No efficiency-contrast pairs (counted separately
  for reporting only). No intermediate-of-failing-trace rejected.
- Full exclusion audit: every raw Rule-A candidate not selected and
  every multi-step trace's Rule-B disposition is recorded.

Deterministic: sorted file order, fixed sort keys, no randomness, no
network, no model calls. Writes only to --out-dir (default: the
directory containing this script). Never touches data/processed/.

Usage:
  python3 extract_dpo_expanded.py [--out-dir DIR]
"""

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_VERSION = "extract_dpo_expanded.py v1 (2026-11-15)"
CAP_PER_TASK_RULE_A = 3
SYSTEM_PROMPT = (
    "You are an expert autonomous software engineer. "
    "Write concise, optimal, robust, and well-tested code that precisely fulfills the user requirements."
)


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm(text):
    return re.sub(r"\s+", " ", (text or "").strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    closed_loop = here.parent.parent / "closed-loop"
    parser.add_argument("--closed-loop-dir", default=str(closed_loop))
    parser.add_argument("--out-dir", default=str(here))
    args = parser.parse_args()
    closed_loop = Path(args.closed_loop_dir)
    scripts_dir = closed_loop / "scripts"
    traces_dir = closed_loop / "data" / "raw_traces"
    processed_dir = closed_loop / "data" / "processed"

    extractor = _load_module("helix03", str(scripts_dir / "03_extract_pairs.py"))
    runner = _load_module("helix02", str(scripts_dir / "02_run_helix_eval.py"))

    # -- 0. Provenance gate (DPO_RULES.md section 0) -------------------------
    manifest_path = processed_dir / "provenance.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sft_path = processed_dir / "sft_data.jsonl"
    dpo_old_path = processed_dir / "dpo_pairs.jsonl"
    sft_lines = [ln for ln in sft_path.read_text(encoding="utf-8").splitlines()
                 if ln.strip()]
    dpo_old_lines = [ln for ln in dpo_old_path.read_text(encoding="utf-8").splitlines()
                     if ln.strip()]
    gate = {
        "manifest_generated_at": manifest.get("generated_at"),
        "manifest_allow_dry_run": manifest.get("allow_dry_run"),
        "manifest_run_tag_filter": manifest.get("run_tag_filter"),
        "manifest_live_traces_kept": manifest.get("live_traces_kept"),
        "manifest_counts": manifest.get("counts"),
        "sft_lines_now": len(sft_lines),
        "dpo_old_lines_now": len(dpo_old_lines),
        "sft_sha256_now": sha256_file(sft_path),
        "dpo_old_sha256_now": sha256_file(dpo_old_path),
        "sft_sha256_matches_manifest": sha256_file(sft_path) == manifest.get(
            "data_sha256", {}).get("sft_data.jsonl"),
        "dpo_sha256_matches_manifest": sha256_file(dpo_old_path) == manifest.get(
            "data_sha256", {}).get("dpo_pairs.jsonl"),
    }
    gate_ok = (
        manifest.get("allow_dry_run") is False
        and manifest.get("run_tag_filter") == ["build2"]
        and manifest.get("live_traces_kept") == 160
        and manifest.get("counts") == {"sft": 19, "dpo": 6}
        and len(sft_lines) == 19 and len(dpo_old_lines) == 6
        and gate["sft_sha256_matches_manifest"]
        and gate["dpo_sha256_matches_manifest"]
    )
    if not gate_ok:
        print("[ABORT] Provenance gate failed:", json.dumps(gate, indent=2))
        sys.exit(1)
    print("[GATE] provenance.json verified: live-only, build2, 160 traces, "
          "SFT 19 / DPO 6, hashes match.")

    # Independent re-derivation of the eligible set with 03's own logic.
    heldout_ids = extractor._heldout_task_ids()
    eligible = []
    n_scanned = 0
    dry_run_build2 = []
    heldout_blocked = []
    for path in sorted(traces_dir.glob("*.json")):
        n_scanned += 1
        trace = json.loads(path.read_text(encoding="utf-8"))
        if trace.get("phase") != "build" or (trace.get("run_tag") or "") != "build2":
            continue
        if trace.get("task_id") in heldout_ids:
            heldout_blocked.append(path.name)
            continue
        if extractor.is_dry_run_trace(trace):
            dry_run_build2.append(path.name)
            continue
        trace["_source_file"] = path.name
        eligible.append(trace)
    if dry_run_build2 or heldout_blocked or len(eligible) != 160:
        print(f"[ABORT] Eligible-set check failed: eligible={len(eligible)} "
              f"(expected 160), dry-run={dry_run_build2}, "
              f"heldout-blocked={heldout_blocked}")
        sys.exit(1)
    print(f"[GATE] eligible build2 live traces: {len(eligible)} "
          f"(scanned {n_scanned} files, 0 dry-run, 0 held-out IDs).")

    problems = {}
    for problem_set in ("train", "train20", "heldout", "heldout2"):
        for problem in runner.get_problems(problem_set):
            problems[problem["id"]] = problem

    grouped = defaultdict(list)
    for trace in eligible:
        grouped[trace["task_id"]].append(trace)

    # -- 2. Rule A: sibling correctness pairs --------------------------------
    pairs = []
    excluded_a = []
    per_task = {}
    for task_id in sorted(grouped):
        traces = grouped[task_id]
        passed = [t for t in traces
                  if t.get("passed") is True and t.get("assistant_solution")]
        failed = [t for t in traces
                  if t.get("passed") is False and t.get("assistant_solution")]
        candidates = []
        for chosen in passed:
            for rejected in failed:
                if norm(chosen["assistant_solution"]) == norm(rejected["assistant_solution"]):
                    excluded_a.append({
                        "rule": "A_sibling", "task_id": task_id,
                        "chosen_source_trace": chosen["_source_file"],
                        "rejected_source_trace": rejected["_source_file"],
                        "reason": "identical_text"})
                    continue
                candidates.append((chosen, rejected))
        candidates.sort(key=lambda cr: (
            cr[0].get("steps", 999), cr[0].get("latency_sec", 999),
            -(cr[1].get("steps", 0)), -(cr[1].get("latency_sec", 0)),
            cr[0]["_source_file"], cr[1]["_source_file"]))
        chosen_texts_all = {norm(t["assistant_solution"]) for t in passed}
        used_chosen, used_rejected = set(), set()
        selected = []
        for chosen, rejected in candidates:
            if len(selected) >= CAP_PER_TASK_RULE_A:
                break
            cn, rn = norm(chosen["assistant_solution"]), norm(rejected["assistant_solution"])
            take = False
            if cn not in used_chosen:
                take = True
            elif used_chosen >= chosen_texts_all and rn not in used_rejected:
                take = True
            if take:
                selected.append((chosen, rejected))
                used_chosen.add(cn)
                used_rejected.add(rn)
        selected_ids = {(c["_source_file"], r["_source_file"]) for c, r in selected}
        for chosen, rejected in candidates:
            if (chosen["_source_file"], rejected["_source_file"]) not in selected_ids:
                excluded_a.append({
                    "rule": "A_sibling", "task_id": task_id,
                    "chosen_source_trace": chosen["_source_file"],
                    "rejected_source_trace": rejected["_source_file"],
                    "reason": "cap_or_coverage"})
        for idx, (chosen, rejected) in enumerate(selected, start=1):
            pairs.append({
                "task_id": task_id,
                "preference_type": "correctness_contrast",
                "extraction_rule": "A_sibling",
                "pair_id": f"A-{task_id}-{idx}",
                "system": SYSTEM_PROMPT,
                "prompt": chosen.get("prompt"),
                "chosen": chosen.get("assistant_solution"),
                "rejected": rejected.get("assistant_solution"),
                "chosen_harness": chosen.get("harness_id"),
                "rejected_harness": rejected.get("harness_id"),
                "chosen_steps": chosen.get("steps"),
                "rejected_steps": rejected.get("steps"),
                "chosen_source_trace": chosen.get("_source_file"),
                "rejected_source_trace": rejected.get("_source_file"),
                "chosen_temperature": chosen.get("temperature", 0.0),
                "chosen_sample_index": chosen.get("sample_index", 0),
                "rejected_temperature": rejected.get("temperature", 0.0),
                "rejected_sample_index": rejected.get("sample_index", 0),
                "run_tag": chosen.get("run_tag") or "",
            })
        if not passed:
            zero_reason = "no_contrast_all_fail"
        elif not failed:
            zero_reason = "no_contrast_all_pass"
        else:
            zero_reason = None
        per_task[task_id] = {
            "n_traces": len(traces),
            "n_passed": len(passed),
            "n_failed": len(failed),
            "rule_a_raw_candidates": len(candidates) + sum(
                1 for e in excluded_a
                if e["task_id"] == task_id and e["reason"] == "identical_text"),
            "rule_a_selected": len(selected),
            "rule_b_selected": 0,
            "zero_pair_reason": zero_reason,
        }

    # -- 3. Rule B: fail->fixed within one trace ------------------------------
    rule_b_dispositions = []
    for trace in sorted(eligible, key=lambda t: t["_source_file"]):
        if trace.get("steps", 0) < 2:
            continue
        task_id = trace["task_id"]
        problem = problems[task_id]
        transcript = trace.get("raw_helix_transcript") or []
        fname = trace["_source_file"]
        if trace.get("passed") is not True:
            rule_b_dispositions.append({"trace_file": fname, "task_id": task_id,
                                        "disposition": "final_not_passed"})
            continue
        if len(transcript) != trace.get("steps"):
            rule_b_dispositions.append(
                {"trace_file": fname, "task_id": task_id,
                 "disposition": "transcript_length_mismatch",
                 "steps": trace.get("steps"),
                 "transcript_len": len(transcript)})
            continue
        final_code = runner.extract_python_code(trace.get("assistant_solution") or "")
        last_failing = None  # (step_index_1based, code)
        saw_code = False
        for step_pos, turn in enumerate(transcript[:-1], start=1):
            code = runner.extract_python_code(turn.get("content") or "")
            if not code:
                continue
            saw_code = True
            ok, _ = runner.run_test_cases(code, problem["test_cases"])
            if not ok:
                last_failing = (step_pos, code)
        if not saw_code:
            rule_b_dispositions.append({"trace_file": fname, "task_id": task_id,
                                        "disposition": "no_intermediate_code"})
            continue
        if last_failing is None:
            rule_b_dispositions.append({"trace_file": fname, "task_id": task_id,
                                        "disposition": "no_failing_intermediate"})
            continue
        step_pos, code = last_failing
        rejected_text = f"```python\n{code}\n```"
        if norm(rejected_text) == norm(trace.get("assistant_solution") or ""):
            rule_b_dispositions.append(
                {"trace_file": fname, "task_id": task_id,
                 "disposition": "identical_text",
                 "rejected_step": step_pos})
            continue
        pairs.append({
            "task_id": task_id,
            "preference_type": "correctness_contrast",
            "extraction_rule": "B_fail_to_fixed",
            "pair_id": f"B-{task_id}-1",
            "system": SYSTEM_PROMPT,
            "prompt": trace.get("prompt"),
            "chosen": trace.get("assistant_solution"),
            "rejected": rejected_text,
            "chosen_harness": trace.get("harness_id"),
            "rejected_harness": trace.get("harness_id"),
            "chosen_steps": trace.get("steps"),
            "rejected_steps": step_pos,
            "chosen_source_trace": fname,
            "rejected_source_trace": fname,
            "chosen_temperature": trace.get("temperature", 0.0),
            "chosen_sample_index": trace.get("sample_index", 0),
            "rejected_temperature": trace.get("temperature", 0.0),
            "rejected_sample_index": trace.get("sample_index", 0),
            "run_tag": trace.get("run_tag") or "",
            "rejected_step": step_pos,
        })
        per_task[task_id]["rule_b_selected"] += 1
        rule_b_dispositions.append({"trace_file": fname, "task_id": task_id,
                                    "disposition": "selected",
                                    "rejected_step": step_pos})

    # -- 5. Efficiency-contrast count (old Case 2; reporting only) ------------
    efficiency_count = 0
    efficiency_tasks = []
    for task_id in sorted(grouped):
        traces = grouped[task_id]
        passed = [t for t in traces
                  if t.get("passed") is True and t.get("assistant_solution")]
        failed = [t for t in traces if t.get("passed") is False]
        if failed or len(passed) < 2:
            continue
        ordered = sorted(passed, key=lambda t: t.get("steps", 999))
        fastest, slowest = ordered[0], ordered[-1]
        if (slowest.get("steps", 1) - fastest.get("steps", 1)) >= 2 \
                and norm(fastest["assistant_solution"]) != norm(slowest["assistant_solution"]):
            efficiency_count += 1
            efficiency_tasks.append(task_id)

    # -- 4. Final validation + overlap with the old 6 pairs -------------------
    pairs.sort(key=lambda p: (p["task_id"], p["extraction_rule"], p["pair_id"]))
    seen = set()
    for pair in pairs:
        for field in ("system", "prompt", "chosen", "rejected"):
            assert isinstance(pair.get(field), str) and pair[field].strip(), \
                f"empty {field} in {pair['pair_id']}"
        assert pair["chosen"] != pair["rejected"], \
            f"chosen == rejected in {pair['pair_id']}"
        assert pair["task_id"] not in heldout_ids, \
            f"held-out task leaked: {pair['pair_id']}"
        key = (pair["task_id"], norm(pair["chosen"]), norm(pair["rejected"]))
        assert key not in seen, f"duplicate pair: {pair['pair_id']}"
        seen.add(key)
        assert pair["chosen_source_trace"] in {t["_source_file"] for t in eligible}
        assert pair["rejected_source_trace"] in {t["_source_file"] for t in eligible}

    old_pairs = [json.loads(ln) for ln in dpo_old_lines]
    old_keys = {(p["task_id"], p["chosen"], p["rejected"]) for p in old_pairs}
    new_keys = {(p["task_id"], p["chosen"], p["rejected"]) for p in pairs}
    overlap = len(old_keys & new_keys)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = out_dir / "dpo_pairs_expanded.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")

    from collections import Counter
    audit = {
        "script": SCRIPT_VERSION,
        "rules": "DPO_RULES.md (2026-11-15, pre-registered)",
        "provenance_gate": gate,
        "eligible_traces": len(eligible),
        "files_scanned": n_scanned,
        "dry_run_build2_excluded": dry_run_build2,
        "heldout_blocked": heldout_blocked,
        "counts": {
            "total_pairs": len(pairs),
            "by_rule": dict(Counter(p["extraction_rule"] for p in pairs)),
            "by_task": {tid: per_task[tid]["rule_a_selected"]
                        + per_task[tid]["rule_b_selected"]
                        for tid in sorted(per_task)},
            "target_band": "15-30 (goal, not a quota)",
        },
        "per_task": per_task,
        "rule_a_excluded_candidates": excluded_a,
        "rule_a_excluded_count": len(excluded_a),
        "rule_b_dispositions": rule_b_dispositions,
        "rule_b_multi_step_traces": len(rule_b_dispositions),
        "efficiency_contrast_old_case2": {
            "count": efficiency_count, "tasks": efficiency_tasks,
            "note": "Counted for reporting only; NOT included in the DPO file (DPO_RULES.md section 5).",
        },
        "overlap_with_old_dpo_pairs": {
            "old_pairs": len(old_pairs), "preserved_verbatim": overlap,
            "note": "The new file supersedes the old 6 pairs for the supplement run; overlap is reported, not required.",
        },
        "validation": {
            "all_texts_nonempty": True,
            "chosen_ne_rejected_raw": True,
            "no_duplicate_normalized_pairs": True,
            "no_heldout_task_ids": True,
            "all_source_traces_in_eligible_set": True,
        },
        "output_sha256": sha256_file(jsonl_path),
        "output_file": jsonl_path.name,
        "sft_unchanged": {
            "note": "SFT was NOT re-extracted. The supplement run must reuse data/processed/sft_data.jsonl (19 records).",
            "sft_sha256": gate["sft_sha256_now"],
        },
    }
    audit_path = out_dir / "dpo_extraction_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False),
                          encoding="utf-8")

    print(f"[OK] Rule A: {sum(1 for p in pairs if p['extraction_rule'] == 'A_sibling')} pairs; "
          f"Rule B: {sum(1 for p in pairs if p['extraction_rule'] == 'B_fail_to_fixed')} pairs; "
          f"total {len(pairs)} (target band 15-30).")
    print(f"[OK] Excluded Rule-A candidates: {len(excluded_a)}; "
          f"Rule-B dispositions: {len(rule_b_dispositions)} multi-step traces.")
    print(f"[OK] Old DPO overlap: {overlap}/{len(old_pairs)} preserved verbatim; "
          f"old-Case-2 efficiency pairs (excluded): {efficiency_count}.")
    print(f"[OK] wrote {jsonl_path} sha256={audit['output_sha256'][:12]}...")
    print(f"[OK] wrote {audit_path}")


if __name__ == "__main__":
    main()
