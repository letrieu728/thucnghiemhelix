# Round 2 design: expanded training set, sampling, discriminating held-out (2026-11-12)

Goal: test the HELIX closed-loop hypothesis properly after Round 1 showed
(a) a training-task gain consistent with sampling noise (McNemar p = 0.375)
and (b) a saturated held-out set (base 39/40, LoRA 40/40) that cannot
discriminate between models. Round 2 expands the training set, adds
sampling to create real sibling contrast, and evaluates on a harder
held-out set. Nothing in Round 2 overwrites Round 1: all Round 2 traces
carry run tags (`build2`, `rebuild2`, `heldout2`) and Round 1 files,
counts and report sections are preserved.

Budget authority: GPU spend for Round 2 must stay within an estimated
**$6 total** (credits first; no card charge while credit remains). The
estimates below are estimates: Modal bills GPU container-seconds and the
exact balance is not readable via the CLI. If a checkpoint projection
exceeds $6, GPU work stops immediately and the partial state is reported.

## 1. Problem sets (all IDs pairwise disjoint, checked on load)

| Set | File | IDs | Size | Use |
| --- | --- | --- | --- | --- |
| train (Round 1) | `BENCHMARK_PROBLEMS` in `02` | `lcb_001`–`lcb_010` | 10 | Training |
| train-extra | `data/train_extra_problems.json` | `lcb_011`–`lcb_020` | 10 | Training |
| train20 | train + train-extra | `lcb_001`–`lcb_020` | 20 | Round 2 BUILD/REBUILD |
| heldout v1 | `data/heldout_problems.json` | `held_001`–`held_010` | 10 | Round 1 only; NOT re-run |
| heldout2 | `data/heldout2_problems.json` | `held2_001`–`held2_015` | 15 | Round 2 held-out only |

Reference solutions for all 25 new problems were written and verified
offline against the committed test cases: **25/25 pass** (verification
script kept outside the repo so reference code is never committed and
never trained on, the same rule as Round 1). Held-out problems are never
fed to extraction: `03` accepts only `phase == "build"` traces and
additionally blocks any trace whose task ID belongs to a held-out set.

Train-extra difficulty is medium throughout (rain water, course
schedule, palindromic substring, daily temperatures, word search,
partition, merge-k-lists, decode string, unique permutations, min
jumps). Held-out v2 is medium-hard/hard (edit distance, regex matching,
N-queens count, number of LIS, word ladder, sliding-window maximum,
course order, median finder, next permutation, 3Sum, valid Sudoku, gas
station, decode ways, rotting oranges, longest consecutive). The held-out
v2 target is a base-model total well below ceiling (below ~85%); if the
base still scores >= 95%, the set has failed as a discriminator and that
failure is reported as-is — no generalisation claim either way.

## 2. Sampling (why, and how much)

Round 1 ran one deterministic sample per cell (`temperature=0.0`), which
is why DPO had only 2 pairs: only 2 tasks had both a pass and a fail.
Sampling creates within-task contrast: the same (task, harness) can pass
on one sample and fail on another, producing genuine chosen/rejected
pairs from live model output. Sampling traces are used ONLY for
training-data extraction, never for baseline comparisons (those stay
temperature 0.0, n=1, exactly the Round 1 protocol).

Adaptive rule (decided from data, not in advance): after BUILD2 at
temperature 0.0, extract provisionally (offline, $0) and count DPO pairs:

- DPO >= 9: skip sampling entirely (enough contrast already).
- DPO 5–8: sampling on `minimal` only, temperature 0.7, n=2 (40 cells).
- DPO < 5: sampling on `minimal` + `opencode`, temperature 0.7, n=2
  (80 cells). These two harnesses bracket the scaffolding range and are
  the cheapest (1-step / short-loop) cells.

Sampling uses seed `42000 + sample_index`, recorded in each trace.
The extractor caps SFT/DPO at one record per task (best passing trace /
best contrast), so sampling can only increase the number of tasks with
contrast, never duplicate a task's record.

## 3. Trace budget and cost projection

Calibration from Round 1 (measured): 160 traces, total recorded latency
5,003.8 s (mean 31.3 s/cell; build 35.5 s, rebuild 48.1 s, held-out
20.8 s). Round 1 total was estimated at $2–2.50 including one A100
training run and deployment overhead, at the brief's rates (A10G
~$1.10/hr, A100 ~$2.10/hr). Latency is a lower bound on billed GPU
time: cold starts, health polling and the 180 s scaledown window add
overhead, so projections below add explicit overhead allowances and a
safety factor at each checkpoint.

| Phase | Cells | Assumed mean latency | Latency | Notes |
| --- | --- | --- | --- | --- |
| BUILD2 temp 0.0 | 80 | 40 s | 3,200 s | 20 tasks x 4 harnesses |
| Sampling (max) | 80 | 25 s | 2,000 s | Adaptive; may be 40 or 0 |
| REBUILD2 temp 0.0 | 80 | 48 s | 3,840 s | LoRA v2, same 20 tasks |
| HELDOUT2 (both models) | 120 | 35 s | 4,200 s | 15 tasks x 4 x 2; harder tasks, more steps |
| **Total (worst case)** | **360** | — | **13,240 s (3.68 h)** | |

Worst-case cost: serving 3.68 h x $1.10 ≈ $4.05 + training ≈ $0.70 +
cold starts/idle ≈ $0.50 = **≈ $5.25**, leaving ~$0.75 buffer under the
$6 cap. With 40 sampling cells: ≈ $4.90. With no sampling: ≈ $4.55.
Wall time is ~4–4.5 h sequential; runs are chunked (below) so a VM
restart loses at most one chunk, and `--skip-existing` resumes without
re-spending GPU on completed cells.

Checkpoints (after every phase): sum actual recorded latency, project
remaining phases at observed per-harness means x 1.15 safety, add
$0.70 training + $0.25 per remaining deployment. If the projection
exceeds $5.60, cut sampling first. If it exceeds $6.00 at any point,
stop GPU work immediately, finish offline analysis, and report the
partial state. Held-out v2 (both models) is never cut to save money:
if the budget cannot cover it, Round 2 stops and reports instead of
producing a one-model held-out number.

## 4. Run order (sequential; chunked; resumable)

0. Back up the Round 1 adapter `helix-lora-final` to
   `helix-lora-final-backup-20261112` in the `helix-adapters` volume
   (the 20261104 backup is left untouched). Checksum the 160 Round 1
   trace files before any live run.
1. Deploy `01_modal_vllm.py` (8192 context, no proxy rewrite). Verify
   `/health` and routing: one completion as the base model id and one
   as `helix-lora`, recording the returned model ids.
2. BUILD2: `--phase build --problem-set train20 --run-tag build2
   --skip-existing`, in 2 chunks (`--start-index 0 --limit 10`,
   `--start-index 10 --limit 10`). Temperature 0.0, n=1.
3. Provisional extract (offline): `03 --run-tag build2`. Apply the
   adaptive sampling rule from §2; run sampling only if the rule says
   so, same run tag, `--temperature 0.7 --n-samples 2`, with
   `--harnesses` per the rule.
4. Final extract: `03 --run-tag build2` (overwrites `data/processed/`;
   Round 1 datasets stay in git history and Round 1 counts stay in the
   report). Record SFT/DPO counts + SHA-256 hashes from the manifest.
5. Train: `modal run 04_train_lora.py --stage sft_then_dpo --epochs 3`
   with Round 1 hyperparameters unchanged (r=16, alpha=32, lr 2e-4,
   DPO lr 5e-6, seed 42). Record run id + loss history.
6. Redeploy the endpoint so it loads the new adapter; re-verify health
   + routing.
7. REBUILD2: `--phase rebuild --problem-set train20 --run-tag rebuild2
   --skip-existing`, 2 chunks. Temperature 0.0, n=1.
8. HELDOUT2: `--phase heldout --problem-set heldout2 --run-tag heldout2
   --skip-existing` for each model (base, then `helix-lora`), 2 chunks
   each (`--limit 8`, then `--start-index 8 --limit 7`).
9. Independently re-verify EVERY new `passed` flag by re-running the
   sandbox tests (0 mismatches required). Compute Round 2 statistics
   (per-harness Pass@1 + Wilson intervals, union, McNemar, flip table)
   with `notebooks/round2_stats.py`, filtering to temperature 0.0 /
   sample 0 for baseline comparisons. Update tests; all must pass.
10. Stop the Modal app and verify no app is running. Update
    `REBUILD_REPORT.md` (new Round 2 section; Round 1 sections kept
    verbatim), `PROVENANCE_AUDIT.md`, `HELDOUT_RUNBOOK.md`. Push the
    changed files to `thucnghiemhelix` master in snapshot batches and
    verify local hashes match origin.

## 5. What would count as evidence (decided in advance)

- Training-task gain alone proves nothing (Round 1 lesson): it must be
  read with the flip table (gains on untrained tasks / losses on
  trained tasks) and McNemar.
- A held-out v2 gain counts as (weak) generalisation evidence only if
  the set discriminates (base below ceiling), the gain is consistent
  across harnesses rather than one cell, and no held-out ID appears in
  the training manifest. A held-out loss or tie is reported as such.
- If sampling still leaves DPO tiny, or training losses stay flat,
  that is reported as a data-scale limitation, not papered over with
  more epochs or a changed configuration.

## 6. Explicitly out of scope (Group 3, awaiting separate approval)

Real assembled HELIX harnesses, real LiveCodeBench/AtCoder fixtures, a
second co-evolution round, and any Kaggle recount (no link has been
provided). None of these is started in Round 2.

## 7. Protocol change during Round 2: feedback-loop cap of 4 steps

Discovered after the first 8 BUILD2 cells (discarded, kept in working
notes only): with the context window raised to 8192 + truncation, the
failing `lcb_002` cells ran the full recipe loops — pi-mono 8 steps /
231 s, hermes 12 steps / 403 s, opencode 15 steps / 301 s — and still
failed. At that rate the $6 budget would be exceeded before held-out v2.
The 8 cells (1,013 s latency) were discarded and BUILD2 restarted.

Evidence for the cap, from all 160 Round 1 traces: every passing
advanced-harness cell (105/105) finished within 3 steps, and every
Round 1 cell that reached 6+ steps ended in an HTTP 400 context error
— no Round 1 pass ever needed a 4th retry. Round 2 therefore caps
advanced-harness loops at **4 steps** (`MAX_ADVANCED_STEPS` in `02`;
minimal stays at 1). The cap applies uniformly to both models and all
phases, preserves all observed Round 1 passing behaviour, and bounds
each failing cell to ~4 generations. Limitation, stated plainly: Round 2
compares ≤4-step feedback loops, not the unbounded 8/12/15-step recipe
loops — which, in Round 1, never actually completed on failing cells
anyway. Revised latency projection with the cap: failing advanced cells
~120 s worst case; BUILD2 + REBUILD2 + HELDOUT2 worst case ≈ 9,000–
11,000 s serving (≈ $2.75–3.35) + training + overhead, inside $6 with
the §3 checkpoints still enforced.
