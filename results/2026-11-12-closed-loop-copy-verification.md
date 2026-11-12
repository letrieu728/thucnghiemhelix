Verification log: closed-loop working copy in thucnghiemhelix (2026-11-12)
All checks offline, no model calls. Modal-dependent code exercised via a stub (import + validation only; no GPU run).

=== 1. Byte-compile ===
COMPILE-OK

=== 2. Unit tests (modal stub) ===
test_config_matches_training_script (test_pipeline.PipelineTests.test_config_matches_training_script) ... ok
test_dry_run_mode_field_is_skipped (test_pipeline.PipelineTests.test_dry_run_mode_field_is_skipped) ... ok
test_empty_does_not_seed_or_overwrite (test_pipeline.PipelineTests.test_empty_does_not_seed_or_overwrite) ... ok
test_live_only_guard_on_committed_traces (test_pipeline.PipelineTests.test_live_only_guard_on_committed_traces) ... ok
test_loss_history_and_no_steps (test_pipeline.PipelineTests.test_loss_history_and_no_steps) ... ok
test_malformed_and_unpaired_evaluation_fails (test_pipeline.PipelineTests.test_malformed_and_unpaired_evaluation_fails) ... ok
test_missing_empty_invalid_training_inputs (test_pipeline.PipelineTests.test_missing_empty_invalid_training_inputs) ... ok
test_no_hardcoded_metrics (test_pipeline.PipelineTests.test_no_hardcoded_metrics) ... ok
test_provenance_gate_blocks_tampered_data (test_pipeline.PipelineTests.test_provenance_gate_blocks_tampered_data) ... ok
test_rebuild_cannot_be_selected_for_training (test_pipeline.PipelineTests.test_rebuild_cannot_be_selected_for_training) ... ok
Ran 10 tests in 0.084s
OK

=== 3. Extractor guard + manifest (scratch copy) ===
[PROVENANCE] Kept 9 live BUILD traces across 3 tasks.
[PROVENANCE] Skipped 31 dry-run BUILD traces (use --allow-dry-run to include them for smoke tests only):
[OK] Extracted 1 Clean SFT records -> /tmp/thuc-test/closed-loop/data/processed/sft_data.jsonl
[OK] Extracted 0 DPO Preference Pairs -> /tmp/thuc-test/closed-loop/data/processed/dpo_pairs.jsonl
manifest live-only: False {'sft': 1, 'dpo': 0} kept: 9 skipped: 31
--- with --allow-dry-run ---
[OK] Extracted 9 Clean SFT records -> /tmp/thuc-test/closed-loop/data/processed/sft_data.jsonl
[OK] Extracted 8 DPO Preference Pairs -> /tmp/thuc-test/closed-loop/data/processed/dpo_pairs.jsonl
[OK] Wrote provenance manifest -> /tmp/thuc-test/closed-loop/data/processed/provenance.json
manifest allow: True {'sft': 9, 'dpo': 8}

=== 4. Training gate demo (validate_data, modal stub) ===
(a) legacy data default: BLOCKED -> Provenance manifest admits dry-run (mock) data; refusing to train. Re-extract live-only wi
[WARN] Provenance manifest admits dry-run data; proceeding by explicit request.
(a) legacy data +flag: ['dpo', 'sft']
(b) allow-dry-run output default: BLOCKED -> Provenance manifest admits dry-run (mock) data; refusing to train. Re-extract live-only wi

=== 5. Held-out dry-run from the new repo root (limit 1) ===
  Problems : heldout (1 tasks)
  Evaluation complete: 0/4 passed
4
