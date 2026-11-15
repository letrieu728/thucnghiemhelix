#!/usr/bin/env python3
"""Stage expanded DPO (19 pairs) for the 2026-11-15 supplement run.

Writes a NEW provenance.json preserving every field of the Round 2
manifest except: generated_at (new), extractor (staging note + script
name), counts (sft 19, dpo 19), data_sha256[dpo_pairs.jsonl] (new hash).
Does NOT touch sft_data.jsonl. Does not modify 03_extract_pairs.py.
Run from repo root thucnghiemhelix/.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # results/... -> repo root
# This script lives in results/2026-11-15-hang2-hang5/, so parent.parent is repo root.
SUPPL = Path(__file__).resolve().parent
PROCESSED = ROOT / "closed-loop" / "data" / "processed"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    sft_hash = sha256_file(PROCESSED / "sft_data.jsonl")
    assert sft_hash == "4f4d6ad8b63c9407d0ac2a2409a05130622e01dc6dc181187ab5b802f71aec11", sft_hash
    dpo_hash = sha256_file(PROCESSED / "dpo_pairs.jsonl")
    assert dpo_hash == "47b8e0756876a3d627f73ffa6776d19f2011c2d1c26a4894406a5fd0216af19c", dpo_hash
    n_sft = sum(1 for _ in open(PROCESSED / "sft_data.jsonl", encoding="utf-8") if _.strip())
    n_dpo = sum(1 for _ in open(PROCESSED / "dpo_pairs.jsonl", encoding="utf-8") if _.strip())
    assert (n_sft, n_dpo) == (19, 19), (n_sft, n_dpo)

    backup_manifest = json.loads((SUPPL / "staging-backup" / "provenance.json").read_text(encoding="utf-8"))
    manifest = json.loads((SUPPL / "staging-backup" / "provenance.json").read_text(encoding="utf-8"))
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    manifest["extractor"] = (
        "staging dot bo sung hang 2+5 (2026-11-15): dpo_pairs_expanded.jsonl (19 pairs, "
        "extract_dpo_expanded.py v1 per DPO_RULES.md) staged by stage_supplement_provenance.py; "
        "SFT unchanged from Round 2 manifest; source: " + backup_manifest["extractor"]
    )
    manifest["counts"] = {"sft": 19, "dpo": 19}
    manifest["data_sha256"] = dict(backup_manifest["data_sha256"])
    manifest["data_sha256"]["dpo_pairs.jsonl"] = dpo_hash
    # Everything else preserved verbatim: allow_dry_run, run_tag_filter,
    # run_tags_observed, live_traces_kept, dry-run counts, tasks, source_traces.
    (PROCESSED / "provenance.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("staged provenance.json: counts", manifest["counts"], "dpo hash", dpo_hash[:12], "sft hash", sft_hash[:12])
    print("generated_at", manifest["generated_at"])


if __name__ == "__main__":
    main()
