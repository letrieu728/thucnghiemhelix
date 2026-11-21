#!/usr/bin/env python3
"""O2 Step 1 — filter fix training data to lcb_* (train) tasks only.

Sources (fix, 18/11/2026):
  ~/workspace/helix-eval/logs/rebuild-fix-lora-tooluse/data/sft_data.jsonl (40)
  ~/workspace/helix-eval/logs/rebuild-fix-lora-tooluse/data/dpo_pairs.jsonl (9)

Keeps only task_id starting with 'lcb_'. Drops all held2_*.
Verifies with the SAME shim parser as the fix (extract_function_calls from
variant C 01_modal_vllm_rebuild_C.py):
  - every kept SFT assistant text parses >=1 tool call
  - every kept DPO 'chosen' parses >=1 tool call, 'rejected' parses 0
    (rejected = FAIL 0-tool trace by construction)
Writes data-clean/sft_data.jsonl, dpo_pairs.jsonl, manifest.json.
Offline, $0.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

FIX_DATA = Path("/home/hatch/workspace/helix-eval/logs/rebuild-fix-lora-tooluse/data")
VARIANT_C = Path("/home/hatch/workspace/helix-eval/logs/rebuild-step1-2026-11-15/variants/01_modal_vllm_rebuild_C.py")
OUT = Path("/home/hatch/workspace/helix-eval/logs/improvement-6usd-2026-11-20/o2-clean-retrain/data-clean")
OUT.mkdir(parents=True, exist_ok=True)

KNOWN_TOOLS = ["bash", "edit", "read", "write"]


def load_shim():
    spec = importlib.util.spec_from_file_location("variant_c", VARIANT_C)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.extract_function_calls


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    extract_function_calls = load_shim()

    sft_all = [json.loads(l) for l in open(FIX_DATA / "sft_data.jsonl")]
    dpo_all = [json.loads(l) for l in open(FIX_DATA / "dpo_pairs.jsonl")]

    sft_keep = [r for r in sft_all if r["task_id"].startswith("lcb_")]
    sft_drop = [r for r in sft_all if not r["task_id"].startswith("lcb_")]
    dpo_keep = [r for r in dpo_all if r["task_id"].startswith("lcb_")]
    dpo_drop = [r for r in dpo_all if not r["task_id"].startswith("lcb_")]

    # (a) no held2_* remains in kept sets
    assert all(not r["task_id"].startswith("held2_") for r in sft_keep + dpo_keep)
    assert all(r["task_id"].startswith("held2_") for r in sft_drop + dpo_drop), \
        "dropped rows must all be held2_*"

    # (b) all kept samples from the 15 lcb tasks listed in DESIGN.md §0
    lcb_tasks_sft = sorted({r["task_id"] for r in sft_keep})
    lcb_tasks_dpo = sorted({r["task_id"] for r in dpo_keep})
    assert len(lcb_tasks_sft) == 15, f"expected 15 distinct lcb SFT tasks, got {len(lcb_tasks_sft)}"
    assert set(lcb_tasks_dpo) <= set(lcb_tasks_sft), "DPO lcb tasks must be subset of SFT lcb tasks"
    assert len(sft_keep) == 24, f"expected 24 SFT kept, got {len(sft_keep)}"
    assert len(dpo_keep) == 5, f"expected 5 DPO kept, got {len(dpo_keep)}"

    # (c) shim parses every kept sample (same parser as fix 49/49 check)
    shim = {"sft": [], "dpo": []}
    for r in sft_keep:
        content = r["messages"][2]["content"]
        parsed, _ = extract_function_calls(content, KNOWN_TOOLS)
        assert len(parsed) >= 1, f"SFT {r['task_id']}: shim parsed 0 tool calls"
        shim["sft"].append({"task_id": r["task_id"], "n_tool_calls_parsed": len(parsed),
                            "tools": [c["name"] for c in parsed]})
    for r in dpo_keep:
        parsed_c, _ = extract_function_calls(r["chosen"], KNOWN_TOOLS)
        parsed_r, _ = extract_function_calls(r["rejected"], KNOWN_TOOLS)
        assert len(parsed_c) >= 1, f"DPO {r['task_id']}: chosen parsed 0 tool calls"
        assert len(parsed_r) == 0, f"DPO {r['task_id']}: rejected parsed {len(parsed_r)} tool calls (expected 0)"
        shim["dpo"].append({"task_id": r["task_id"],
                            "chosen_n_tool_calls_parsed": len(parsed_c),
                            "rejected_n_tool_calls_parsed": len(parsed_r)})

    with open(OUT / "sft_data.jsonl", "w") as f:
        for r in sft_keep:
            f.write(json.dumps(r) + "\n")
    with open(OUT / "dpo_pairs.jsonl", "w") as f:
        for r in dpo_keep:
            f.write(json.dumps(r) + "\n")

    manifest = {
        "source": {
            "sft": str(FIX_DATA / "sft_data.jsonl"),
            "dpo": str(FIX_DATA / "dpo_pairs.jsonl"),
            "sft_source_sha256": sha256(FIX_DATA / "sft_data.jsonl"),
            "dpo_source_sha256": sha256(FIX_DATA / "dpo_pairs.jsonl"),
        },
        "counts": {
            "sft_total": len(sft_all), "sft_kept": len(sft_keep), "sft_dropped": len(sft_drop),
            "dpo_total": len(dpo_all), "dpo_kept": len(dpo_keep), "dpo_dropped": len(dpo_drop),
            "distinct_lcb_tasks_sft": len(lcb_tasks_sft),
            "distinct_lcb_tasks_dpo": len(lcb_tasks_dpo),
        },
        "kept_task_ids": {
            "sft": lcb_tasks_sft,
            "dpo": lcb_tasks_dpo,
        },
        "dropped_task_ids": {
            "sft": sorted({r["task_id"] for r in sft_drop}),
            "dpo": sorted({r["task_id"] for r in dpo_drop}),
        },
        "checks": {
            "a_no_held2_in_kept": True,
            "b_all_kept_in_15_lcb_tasks": True,
            "c_shim_parses_all_kept": True,
            "shim_parser_source": str(VARIANT_C),
            "shim_results": shim,
            "shim_total_checked": len(sft_keep) + len(dpo_keep),
        },
        "output_sha256": {
            "sft_data.jsonl": sha256(OUT / "sft_data.jsonl"),
            "dpo_pairs.jsonl": sha256(OUT / "dpo_pairs.jsonl"),
        },
    }
    with open(OUT / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"SFT: {len(sft_all)} -> kept {len(sft_keep)} (dropped {len(sft_drop)} held2)")
    print(f"DPO: {len(dpo_all)} -> kept {len(dpo_keep)} (dropped {len(dpo_drop)} held2)")
    print(f"distinct lcb SFT tasks: {len(lcb_tasks_sft)}; DPO tasks: {lcb_tasks_dpo}")
    print(f"shim check: {len(sft_keep)} SFT + {len(dpo_keep)} DPO = "
          f"{len(sft_keep) + len(dpo_keep)} samples, all PASS")
    print("manifest:", OUT / "manifest.json")


if __name__ == "__main__":
    main()
