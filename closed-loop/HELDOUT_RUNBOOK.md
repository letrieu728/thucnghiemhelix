# Held-out runbook: live re-run, retrain, held-out evaluation

Goal: replace the mixed live/dry-run BUILD baseline with a fully live one,
retrain on live-only sibling data, and measure the adapter on 10 tasks it
never trained on. Run the steps in order. Nothing here needs new code — the
guard and the held-out set are already in this branch.

## Prerequisites

- Modal vLLM endpoint serving `Qwen/Qwen2.5-Coder-7B-Instruct` from
  `01_modal_vllm.py` (`modal serve` or `modal deploy`), healthy on `/health`.
- `HELIX_LIVE_BASE_URL` pointing at the endpoint's `/v1` URL and
  `OPENAI_API_KEY` set (see `.env.template`).
- The `helix-adapters` Modal volume reachable for training + LoRA serving.
- A clean checkout of this branch. Commit any local changes first: step 1
  overwrites the 31 dry-run BUILD traces in place (that is the point — the
  old files stay in git history, and `PROVENANCE_AUDIT.md` records why).

## Step 1 — Re-run BUILD live (40/40, base model)

```bash
python closed-loop/scripts/02_run_helix_eval.py --phase build --mode live
```

Expected: 40 traces, ~30–60 minutes wall-clock. Verify before continuing:

```bash
python -c "
import json, glob
traces = [json.load(open(f)) for f in glob.glob('closed-loop/data/raw_traces/build_*.json')]
print('files:', len(traces))
print('mode=live:', sum(1 for t in traces if t.get('mode') == 'live'))
print('with transcript:', sum(1 for t in traces if t.get('raw_helix_transcript')))
print('models:', {t['model'] for t in traces})
"
```

All three counts must be 40, and the model set must be exactly
`{'Qwen/Qwen2.5-Coder-7B-Instruct'}`. If any trace shows `mode: dry-run`
or an empty transcript, the run did not go live — do not proceed.

## Step 2 — Extract live-only training data

```bash
python closed-loop/scripts/03_extract_pairs.py
```

Expected output includes `[PROVENANCE] Kept 40 live BUILD traces` and
`Skipped 0 dry-run`. Record the SFT/DPO counts it prints. Never use
`--allow-dry-run` here: its output is smoke-test-only and must not be
trained on. Commit the new `data/processed/*.jsonl` together with the new
traces, in one commit, so data and traces stay in sync.

## Step 3 — Retrain the adapter

```bash
modal run closed-loop/scripts/04_train_lora.py --stage sft_then_dpo --epochs 3
```

Notes:

- Optimizer steps depend on the new dataset size (effective batch 8 in both
  stages). Note the actual step counts from the run output; do not reuse the
  old "6 + 3" figures.
- The entrypoint downloads `loss_history.json` into
  `data/training_runs/<run-id>/`. Commit that file (or at minimum the run-id
  and per-stage losses) so the run is auditable from the repo.
- Restart the vLLM deployment afterwards so it picks up the new adapter
  (a running server does not reload a committed volume on its own).

## Step 4 — Re-run REBUILD live (training tasks, LoRA model)

```bash
python closed-loop/scripts/02_run_helix_eval.py --phase rebuild --mode live
```

Verify as in step 1, but for `rebuild_*.json` with model `helix-lora`.
Then regenerate the comparison:

```bash
python closed-loop/notebooks/evaluate_rebuild.py
```

Report these numbers explicitly as **training-task** numbers.

## Step 5 — Held-out evaluation (base vs LoRA, fresh tasks)

Run both models on the held-out set. The phase is `heldout` and the model
must be named explicitly; held-out traces never enter training extraction.

```bash
python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout --model Qwen/Qwen2.5-Coder-7B-Instruct
python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout --model helix-lora
```

Verify 80 files (`heldout_base_held_*_*.json` and
`heldout_helix-lora_held_*_*.json`, 40 per model), all `mode: live`
with non-empty transcripts. Held-out filenames carry the model slug so
the two runs cannot overwrite each other (see `save_trace` in `02`). Compare with:

```bash
python -c "
import json, glob, collections
rows = [json.load(open(f)) for f in glob.glob('closed-loop/data/raw_traces/heldout_*.json')]
for model in sorted({t['model'] for t in rows}):
    for h in ['minimal', 'pi-mono', 'hermes-agent', 'opencode']:
        sub = [t for t in rows if t['model'] == model and t['harness_id'] == h]
        print(model, h, f\"{sum(t['passed'] for t in sub)}/{len(sub)}\")
"
```

Report held-out numbers **separately** from training-task numbers, per
harness, with the counts (n=10 per harness). With n=10, one task is 10 pp:
do not over-claim from small deltas, and do not average away the per-task
table.

## Step 6 — Update the reports

- Update `REBUILD_REPORT.md` §3 with the new live BUILD/REBUILD table and
  add a held-out table beside it. Keep the 2026-11-12 correction box and
  add a dated note recording the re-run (dates, counts, run-id).
- Update the slides, presentation scripts, and written report with the same
  corrected numbers and the training-task vs held-out distinction. Do not
  leave "40 live runs" anywhere unless step 1 has actually been completed
  and verified.

## Do-not list

- Do not train on `--allow-dry-run` or `--seed-demo` output.
- Do not add held-out problems (or near-duplicates of them) to training
  data. If a held-out task is ever trained on, remove it from the held-out
  set and say so in the report.
- Do not delete old traces to "clean up": overwrite only via a verified
  live re-run, in its own commit, so history preserves the audit trail.
- Do not present training-task gains as generalisation, and do not present
  the 4 prompt scaffolds as assembled HELIX harnesses.
