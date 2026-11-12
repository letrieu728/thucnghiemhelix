# Provenance audit of the committed closed-loop traces (2026-11-12)

> Copy note: this audit was written against the fork (`Vietng-XPrince7/HELIX`,
> `cc44b7b`). The same text is in the fork's fix branch; this copy lives in
> `letrieu728/thucnghiemhelix/closed-loop/` next to the working copy of the
> pipeline. The Vietnamese record of the same audit is
> `results/2026-11-12-closed-loop-trace-audit.md` in this repo.

## What was checked

Every committed trace in `closed-loop/data/raw_traces/` (80 files: 40 BUILD,
40 REBUILD), the extracted datasets in `closed-loop/data/processed/`
(`sft_data.jsonl`, `dpo_pairs.jsonl`), and the runner/extractor code that
produced them. No model was called for this audit: all checks are offline
re-examination of committed files plus re-execution of the sandbox verifier
on the committed solutions.

## Finding 1: BUILD is 9 live + 31 dry-run, not 40 live

Commit `a090aba` ("finish 40 live runs on modal vllm") and the original
`REBUILD_REPORT.md` described all 40 BUILD traces as live Modal runs. The
traces themselves show otherwise:

| Evidence | Live traces (9) | Dry-run traces (31) |
| --- | --- | --- |
| Files | `lcb_001` × 4 harnesses, `lcb_002` × 4, `lcb_003` minimal | `lcb_003` pi-mono/hermes/opencode + `lcb_004`–`lcb_010` × 4 |
| Timestamps (UTC, 2026-10-28) | 18:32:21 → 18:39:13, spaced by latency | 18:30:49.13 → 18:30:50.46 (~1.3 s total, ~40 ms apart) |
| `raw_helix_transcript` | Non-empty (1–5 steps) | Empty (`[]`) |
| Latency / steps | Varied (3.3–118.0 s) | Exactly the dry-run constants in `_dry_run_solution`: opencode 1.2 s / 1 step, hermes-agent 2.1 s / 2, pi-mono 3.4 s / 3, minimal 5.8 s / 5 |
| Solution | Model output with explanation/prose | Byte-identical to the hand-written `_DRY_RUN_SOLUTIONS` in `02_run_helix_eval.py` |

The 31 traces carry no `mode` field (it did not exist yet) and no
`test_result` field (added later, in `cc44b7b`). The runner now writes
`"mode": "live" | "dry-run"` on every trace, and the extractor rejects
dry-run traces by default (see "Fixes in this branch" below).

## Finding 2: training data is mostly hand-written mock code

`03_extract_pairs.py` (old version) selected the passing trace with the
fewest steps per task. Dry-run OpenCode traces always report 1 step, so they
won every selection:

- SFT: 8 of 9 records sourced from dry-run OpenCode traces. Only
  `lcb_001_two_sum` comes from a live trace.
- DPO: all 8 `chosen` solutions sourced from dry-run OpenCode traces;
  7 of 8 `rejected` solutions also dry-run (only the `lcb_003` rejected
  solution, from the live Minimal trace, is a real model output).

Re-running the guarded extractor on the committed traces yields **1 SFT
record and 0 DPO pairs** from live data alone — too little to train on.
That is the honest size of the verified live dataset today, and the reason
BUILD must be re-run live before any retraining claim.

## Finding 3: REBUILD re-tests the training tasks

All 40 REBUILD traces look genuinely live (non-empty transcripts, varied
latencies 4.1–157.9 s, written over 29 minutes on 2026-10-29, model
`helix-lora`, none matching dry-run solutions). But they evaluate the same
10 tasks the adapter was trained on. The three Minimal tasks that flipped
FAIL → PASS (`lcb_004`, `lcb_006`, `lcb_010`) all have their reference
solutions in the SFT file. The HELIX paper itself warns that evolution and
final evaluation should use separate tasks (§9.3) and that sibling groups
must not leak across train/dev splits (§4.3). A 10-task held-out set that
was never trained on is now provided (`data/heldout_problems.json`).

## What still checks out

- **All 80 `passed` flags re-verify**: re-running each committed solution
  through the runner's sandbox `run_test_cases` reproduces every flag
  (0 mismatches). The verifier is honest; the contamination is in what was
  fed to training and what the baseline mixed together, not in grading.
- **REBUILD_REPORT.md §3 arithmetic** matches the traces exactly
  (Minimal 30% → 60%; Pi/Hermes/OpenCode 90% → 70%; gap 60 pp → 10 pp).
- **The training script is real**: `04_train_lora.py` is a genuine Unsloth +
  TRL SFT→DPO pipeline (QLoRA 4-bit, r=16, α=32). With 9 SFT samples at
  effective batch 8 and 8 DPO pairs at effective batch 8, 3 epochs give
  exactly the reported 6 SFT + 3 DPO optimizer steps. No loss history for
  the final run is committed in this repo, so final-run losses cannot be
  verified from here (only the 3-step smoke-run losses in
  `LORA_VALIDATION.md`).
- **Harness fidelity limit (unchanged)**: the four "harnesses" are
  system-prompt + chat-loop emulations in `_live_solution` (direct
  OpenAI-compatible calls with per-harness prompts and test-feedback
  retries). The runner never invokes the HELIX CLI, assembled recipes, or
  real tool/session/permission machinery. Results therefore compare prompt
  scaffolds, not assembled HELIX harnesses. This was already visible in the
  code; it is recorded here so the report is not misread.

## Fixes in this branch

1. `02_run_helix_eval.py`: every trace now records `"mode"`. New
   `--problem-set {train,heldout}` and `--phase heldout` (explicit `--model`
   required) for clean held-out comparisons.
2. `data/heldout_problems.json`: 10 fresh problems (`held_001`–`held_010`,
   4 easy / 6 medium, disjoint IDs from training tasks), each with sandbox
   test cases verified against reference solutions offline.
3. `03_extract_pairs.py`: live-only by default; dry-run traces are skipped
   and counted; `--allow-dry-run` is smoke-test-only and labelled as such;
   extracted records carry their `source_trace` filename.
4. `tests/test_pipeline.py`: stale demo expectations replaced with guard
   tests pinned to the audited counts (9 live / 40 mixed; 1 live-only SFT).
5. `REBUILD_REPORT.md` / `README.md`: correction boxes, honest sample
   numbers matching §3, removal of the unsupported "60% fewer tokens / 2x
   faster" claim, fixed plot image path.
6. `HELDOUT_RUNBOOK.md`: exact commands to re-run BUILD live, retrain, and
   evaluate held-out.

## Still to do (needs Modal access — cannot be done offline)

- [ ] Re-run BUILD live, 40/40, on the base model (runbook step 1).
- [ ] Re-extract live-only SFT/DPO and retrain (runbook steps 2–3); commit
      the run's `loss_history.json` (or its run-id + losses) with the data.
- [ ] Re-run REBUILD live on the 10 training tasks (runbook step 4).
- [ ] Run held-out evaluation for base vs LoRA (runbook step 5) and report
      it separately from training-task numbers.
- [ ] Update slides/scripts/written report to the corrected wording (the
      decks still say "40 live runs").

## Addendum 2026-11-12 — silent model rewrite in the serving proxy (fixed)

The `cc44b7b` version of `01_modal_vllm.py` contained a proxy rule that
silently rewrote every chat-completion request naming the base model to
`helix-lora` whenever an adapter existed in the volume. Any base-model
(BUILD) evaluation run against that deployment would have measured the
adapter while recording the base model name. The rule was introduced in
`cc44b7b` (REBUILD commit, 29/10) and was NOT present in the `a090aba`
server used for the 28/10 BUILD run, so the 9 live BUILD traces are not
affected by it; the REBUILD traces explicitly requested `helix-lora` and
are unaffected too. The rule has been removed in this working copy:
vLLM multi-LoRA routes by the request's model id, and `02` passes the
model explicitly per phase. The fork still contains the rule — port this
fix back before any further base-model evaluation against the fork's
deployment.
