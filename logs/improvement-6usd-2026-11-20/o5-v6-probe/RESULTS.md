# RESULTS — O5: v6 prompt probe (V1 anti-ask vs V2 short imperative)

Date: 2026-11-21 (runs 2026-11-20 17:22–17:57 UTC). Harness: pi-mono
(assembled, `helix run` path). Arms: base + realtool
(`helix-lora-realtool`), 16 group-regenerated v6 fixtures, 1 run/cell,
2 prompt variants × 2 arms × 16 fixtures = **64 runs, 0 INFRA** (final,
after 2 one-time INFRA reruns — see §5). Protocol: DESIGN.md
(pre-registered, written before any O5 GPU run). Scoring independently
re-verified: 0 mismatches (see §5).

> **LABELLING.** Every fixture in this step is GROUP-REGENERATED
> content (group rebuilt from `test6.jsonl` keys + the builder spec
> after the authors' symlinks were found broken; originals
> unrecoverable). Grading is on PUBLIC test cases only (2–4 per
> fixture). Nothing here is the authors' original fixture set, and
> this run is NOT the authors' benchmark and NOT a LiveCodeBench
> evaluation. Comparisons with the hand-written-task evals in §4 are
> DESCRIPTIVE ONLY (different task style, different grading; no
> statistical test across task sets).

## 1. Headline (descriptive) — PRIMARY metric is engagement

Engagement = runs with ≥1 tool call reading OR editing `solution.py`
(read/edit/write) OR running the test (`bash test_solution.py`).
Rescue criterion (DESIGN §4, pre-registered): engagement ≥ 8/16 per arm.

| Variant × arm | Pass@1 (public cases) | Wilson 95% CI | Engagement (PRIMARY) | Wilson 95% CI | Text-only (0 tools) |
|---|---|---|---|---|---|
| V1 × base | **0/16** | 0.000–0.194 | **13/16** | 0.570–0.934 | 3/16 |
| V1 × realtool | **0/16** | 0.000–0.194 | **14/16** | 0.640–0.965 | 2/16 |
| V2 × base | **0/16** | 0.000–0.194 | **1/16** | 0.011–0.283 | 15/16 |
| V2 × realtool | **0/16** | 0.000–0.194 | **2/16** | 0.035–0.360 | 12/16 |

Paired within each variant (McNemar exact, base-vs-realtoool, Pass@1):
V1 gains 0 / losses 0, p = 1.0; V2 gains 0 / losses 0, p = 1.0
(0 discordant pairs in both — no significance claim; n = 16).
No run in any cell saw the marker in a bash result (0/64) and no run
modified the verifier (0/64).

**Verdict, exactly per the pre-registered §4 rules — a SPLIT result:**

- **V1 (anti-ask sentence appended after the execution hints) RESCUES
  engagement, in BOTH arms: base 13/16 and realtool 14/16, both ≥ 8/16.**
  The prompt rescues engagement on repair tasks at this level.
- **V2 (short imperative prepended before the problem statement) does
  NOT rescue engagement in EITHER arm: base 1/16, realtool 2/16.**
- The two variants are NOT merged into "prompt in general works":
  V1 yes, V2 no — exactly as the split rule requires.
- **But engagement is not outcome: Pass@1 is 0/16 in all four cells.**
  V1 fixed the behaviour (the agent now looks at the file) without
  fixing the result (the code it writes, when it writes any, still
  fails the public cases). The bottleneck moved from non-engagement
  to wrong-code — see §3.

**Baseline-definition note (matters for the comparison, not the
verdict).** DESIGN §4 quoted the step-5 baselines as base 2/16,
realtool 6/16 — those are the ANY-tool-call counts from step 5.
Recomputed from the step-5 `result.json` files under the O5 engagement
definition (read/edit/test only), the step-5 baselines are base **2/16**
and realtool **4/16** (the other 2 realtool runs only ran `bash cat`,
which the O5 definition does not count as reading). The rescue verdict
is unaffected under either definition: V1 (13/16, 14/16) clears 8/16
both ways, V2 (O5-def 1/16, 2/16; any-tool 1/16, 4/16) clears it
neither way.

## 2. Per-fixture tables

PASS/FAIL is the external re-grade: final solution.py + PRISTINE
fixture test file, exit 0 + marker `<fixture-id> tests passed`.
R/E/T/M = read solution.py / edited solution.py / ran test command /
marker seen in a bash result.

### Variant V1

| Fixture | Letter | Cases | Base (R/E/T) | Realtool (R/E/T) |
|---|---|---|---|---|
| livecodebench-v6-000-abc387-b | b | 3 | FAIL R/–/T/– (2 tools) | FAIL R/–/–/– (1 tools) |
| livecodebench-v6-006-abc388-g | g | 2 | FAIL R/–/T/– (2 tools) | FAIL R/E/T/– (4 tools) |
| livecodebench-v6-012-abc389-b | b | 2 | FAIL R/E/–/– (2 tools) | FAIL R/E/T/– (3 tools) |
| livecodebench-v6-018-abc390-g | g | 3 | FAIL R/–/–/– (1 tools) | FAIL R/E/T/– (5 tools) |
| livecodebench-v6-024-abc391-d | d | 2 | FAIL –/–/–/– (0 tools) | FAIL R/–/T/– (2 tools) |
| livecodebench-v6-030-abc392-a | a | 2 | FAIL R/–/–/– (1 tools) | FAIL R/–/–/– (1 tools) |
| livecodebench-v6-037-abc393-f | f | 2 | FAIL R/–/–/– (1 tools) | FAIL R/–/–/– (1 tools) |
| livecodebench-v6-043-abc394-f | f | 3 | FAIL R/–/T/– (2 tools) | FAIL R/–/–/– (1 tools) |
| livecodebench-v6-049-abc395-f | f | 4 | FAIL R/–/–/– (1 tools) | FAIL R/–/T/– (2 tools) |
| livecodebench-v6-055-abc396-f | f | 3 | FAIL R/–/–/– (1 tools) | FAIL R/E/–/– (2 tools) |
| livecodebench-v6-063-abc397-g | g | 3 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-070-abc398-a | a | 2 | FAIL R/–/–/– (1 tools) | FAIL R/E/T/– (3 tools) |
| livecodebench-v6-076-abc399-c | c | 3 | FAIL R/–/–/– (1 tools) | FAIL R/–/–/– (1 tools) |
| livecodebench-v6-082-abc400-b | b | 4 | FAIL R/–/–/– (1 tools) | FAIL R/–/–/– (1 tools) |
| livecodebench-v6-090-arc191-a | a | 3 | FAIL –/–/–/– (0 tools) | FAIL R/E/T/– (3 tools) |
| livecodebench-v6-096-arc193-a | a | 2 | FAIL R/–/–/– (1 tools) | FAIL –/–/–/– (0 tools) |

### Variant V2

| Fixture | Letter | Cases | Base (R/E/T) | Realtool (R/E/T) |
|---|---|---|---|---|
| livecodebench-v6-000-abc387-b | b | 3 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-006-abc388-g | g | 2 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-012-abc389-b | b | 2 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-018-abc390-g | g | 3 | FAIL R/–/–/– (1 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-024-abc391-d | d | 2 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-030-abc392-a | a | 2 | FAIL –/–/–/– (0 tools) | FAIL R/–/T/– (2 tools) |
| livecodebench-v6-037-abc393-f | f | 2 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-043-abc394-f | f | 3 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (2 tools) |
| livecodebench-v6-049-abc395-f | f | 4 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-055-abc396-f | f | 3 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-063-abc397-g | g | 3 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-070-abc398-a | a | 2 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-076-abc399-c | c | 3 | FAIL –/–/–/– (0 tools) | FAIL R/–/T/– (2 tools) |
| livecodebench-v6-082-abc400-b | b | 4 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (1 tools) |
| livecodebench-v6-090-arc191-a | a | 3 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |
| livecodebench-v6-096-arc193-a | a | 2 | FAIL –/–/–/– (0 tools) | FAIL –/–/–/– (0 tools) |

No verifier tampering: `verifier_modified` false in all 64 runs.
One harmless side file: V1 realtool 018 wrote an empty
`test_solution.py.out` (a read of it returned ENOENT first); the
verifier itself is byte-identical to the seed, grading unaffected.
No run hit the step limit (max 5 steps) or the 600 s CLI timeout.

## 3. Mechanism: what the agent actually did (transcript evidence)

All 64 transcripts were read (assistant text + tool calls/results).
Step-5 pattern labels reused: Pattern A = ask the user for the file
contents (explicit ask, or a bare "let's start by reading…" announcement
with 0 tool calls); Pattern B = fake tool use in prose; Pattern C =
read, then fix only in prose.

### 3.1 Pattern A — ask the user for the file (V1: 7/32; V2: 28/32)

Counts are Pattern-A-family (explicit ask + bare announcement, 0 tools):

| Variant × arm | Explicit ask for contents | Bare announcement, 0 tools | Pattern A family |
|---|---|---|---|
| V1 × base | 1 (024) | 2 (063, 090) | **3/16** |
| V1 × realtool | 2 (024, 049) | 2 (063, 096) | **4/16** |
| V2 × base | 15 | 1 (076) | **16/16** |
| V2 × realtool | 8 | 4 (012, 055, 090 + 000) | **12/16** |

Step-5 baseline was 24/32. **V1 cuts Pattern A from 24/32 to 7/32;
V2 leaves it essentially untouched at 28/32 — slightly worse than
step 5.** The anti-ask sentence works; the prepended imperative does
not. Two V1 details worth recording: realtool 024 asks for the file
contents in its FIRST reply and then reads the file anyway in a later
step (the ask does not block later engagement); realtool 049 reads the
file first and THEN asks the user to provide its contents — the ask is
a reflex, not a response to missing information. V2 base 076 is the
step-5 "assume" variant: "Since I don't have access to the actual
content of `solution.py`, I'll assume a common approach…" — no ask,
no tool call, hallucinated approach instead.

### 3.2 The new dominant V1 pattern — Pattern C: read, then fix only in prose

V1 got the agent to look, but mostly not to act on what it saw:

| Variant × arm | Read solution.py | Edited solution.py | Ran test cmd | Read but never edited | Full R→E→T |
|---|---|---|---|---|---|
| V1 × base | 13 | 1 | 3 | **12/16** | 0/16 |
| V1 × realtool | 14 | 6 | 7 | **8/16** | 5/16 |
| V2 × base | 1 | 0 | 0 | 1/16 | 0/16 |
| V2 × realtool | 2 | 0 | 2 | 2/16 | 0/16 |

V1 base read 13/16 files and edited exactly one (012) — and even
there it stopped after the edit and asked the USER to run the test
("Now that `solution.py` has been edited, let's run the test script…
Please execute this command and provide the results"). V1 base 030
does the same after reading ("Please execute the above command and
provide the output"). The typical V1-base run is: read the seed,
diagnose it correctly in prose, paste a corrected program in the
reply, stop — the fix exists only in chat text, the file on disk is
still the buggy seed. V1 realtool goes further (edited 6/16, full
read→edit→test in 5/16) but every edited solution still fails grading:
e.g. 006 edited twice and tested, 018 rewrote the file then wrote the
test file's stdout to a `.out` file instead of fixing the syntax error
it had introduced, 070 and 090 edited, tested, got a failure, and
pasted another version in prose instead of writing it. No V1 edit
produced a passing solution on any fixture.

### 3.3 What V2's failure looks like

V2 is step 5 all over again, only faster: 15/16 base runs and 12/16
realtool runs end in 1 step with 0 tools (avg latency base 7.2 s,
realtool 14.3 s, vs V1's 23.0 s / 45.4 s). The prepended imperative
("Fix the bug in solution.py…") is followed by the same long problem
statement and the same ask-the-user reply — the model behaves as if
the first two lines were never there, consistent with the DESIGN §6
risk (a short instruction before a long statement gets skipped).
The one V2-base engagement (018) reads the file and then asks the
user to provide its contents anyway. Only four V2-realtool runs call
any tool at all: 030 (read + test, prose fix), 043 (`bash ls` +
`bash cat`, prose fix), 076 (read + test, prose fix), 082 (`bash cat`
only, after asking the user to review and fix the file); under the O5
engagement definition only 030 and 076 count as engaged — `cat` via
bash is not a read. V2 realtool 000 shows Pattern B again:
a fenced ```bash read path=…``` block in prose instead of a tool call.

### 3.4 What did NOT happen

- No run modified `test_solution.py` (0/64 verifier tampering).
- No run passed any public test during the run (marker seen 0/64)
  and no run passed the external re-grade (0/64).
- No run crashed, timed out, or hit max-steps (12); the only INFRA
  cells were 2 transient provider errors, both resolved by the single
  allowed rerun (see §5).

## 4. Descriptive comparison with step-5 baselines and function tasks

Same harness (pi-mono), same invocation (`helix run`), same models —
DIFFERENT prompts and task sets. Descriptive only; no statistical
comparison across task sets.

| Eval (pi-mono) | Tasks | Base Pass@1 | Realtool Pass@1 | Base engagement* | Realtool engagement* |
|---|---|---|---|---|---|
| Fix eval (35 LeetCode-style function tasks) | 35 | 20/35 | 28/35 | 31/35† | 35/35† |
| Gen eval (15 fresh function tasks) | 15 | 11/15 | 13/15 | 14/15† | 15/15† |
| Step 5 (16 group-regenerated v6 repair tasks, original prompt) | 16 | 0/16 | 1/16 | 2/16 | 4/16 |
| **O5 V1 (same 16, anti-ask appended)** | **16** | **0/16** | **0/16** | **13/16** | **14/16** |
| **O5 V2 (same 16, imperative prepended)** | **16** | **0/16** | **0/16** | **1/16** | **2/16** |

\* Engagement here is the O5 definition (read/edit/test); step-5
numbers recomputed under it (see §1 note). † Function-task engagement
is text-only complement (fix eval text-only base 4/35, realtool 0/35;
gen eval 1/15, 0/15) — same definition family, different prompt.

What changed between the step-5 row and the O5 rows is ONLY the prompt
(one appended sentence for V1, one prepended imperative for V2) —
same fixtures, same models, same harness, same invocation. The V1
jump (2/16 → 13/16 base; 4/16 → 14/16 realtool) is therefore a
prompt effect on behaviour, not a task or model effect — but it buys
zero Pass@1: the repair-task Pass rate stays 0/16 in both arms under
both variants, and the single step-5 PASS (realtool 012) did not
reproduce under either variant (V1 012: base edited-no-test, realtool
write+test, both FAIL; V2 012: both 1-step text-only). The function-task
rows show the other side of the same coin: where the model engages
(31–35/35), it also passes often (20–28/35); on repair tasks it now
engages under V1 and still passes never — engagement is necessary but
not sufficient here, and the remaining failure is code correctness
on AtCoder-style stdin/stdout problems (letters a–g, mostly f/g),
not tool use.

## 5. Verification + costs + limitations

- **Independent re-verification:** `verify_scoring.py` re-graded all
  64 runs from the SAVED solution_final.py + pristine fixture test
  files and hash-checked solution_final.py vs workspace/solution.py
  and the verifier_modified flags: checked=64, skipped_infra=0,
  mismatches=0, hash_mismatches=0 (exit 0).
- **INFRA / reruns (2, both transient provider errors, max 1/cell,
  DESIGN §6):** (1) V1 base 049 — harness_error, finish=provider_error,
  TypeError fetch failed, 43.18 s → rerun FAIL (tests_failed), 2 steps,
  1 tool, read. (2) V1 realtool 006 — harness_error, provider 500
  Internal Server Error after 331.46 s of internal retries → rerun
  FAIL (tests_failed), 4 steps, 4 tools, read+edit+test. Both old
  attempts preserved as `*.attempt1`, REPLACEMENTS.log has 2 entries.
  A third event — the runtime restart mid-V1-cell-18 (049 realtool) —
  killed the driver with only prompt.txt + seeded workspace on disk;
  the cell was re-run fresh on resume (workspace re-seeded by the
  driver) and scored FAIL normally. No rerun was used for any FAIL.
- **Costs:** metered $28.67754058 → $29.30754190 (delayed snapshot),
  delta **+$0.63**, billed **$0.00** (credits absorbed all).
  Planned $0.55; actual $0.63 — over plan by $0.08 (V1's engaged,
  multi-step runs cost ~$0.013/cell; V2's 1-step text-only runs cost
  ~$0.001–0.002/cell). Program total now $4.5189/$6.00; remaining
  $1.4811 (O6 is offline, $0). Billing checkpoints (all billed $0.00):
  before $28.6775, after deploy $28.6975, after pilot $28.7375,
  V1 16 cells $29.0875, after V1 $29.1375, V2 pilot $29.2475,
  V2 16 cells $29.2875, after stop $29.3775, delayed $29.3075.
  The after-stop → delayed move (−$0.07) is billing lag/adjustment
  noise, as seen in step 5. App stopped; 0 tasks verified by the
  operator's own `modal app list`; endpoint returns "modal-http:
  invalid function call" after stop (verified by curl).
- **Git state:** upstream clean (HEAD b5adffa) before and after;
  fork status byte-identical before/after (94 D + 2 ??). No
  commit/push anywhere. No slides/Drive/GitHub/Canva changes.
  No fixture file was modified (prompt variants applied in the
  driver only; every cell's prompt.txt + sha256 saved).
- **Limitations:** group-regenerated fixtures (not the authors'
  originals); public cases only (2–4 per fixture — a PASS means
  passing the public cases, nothing more); n=16, 1 run/cell, single
  harness (pi-mono only, per DESIGN — no second harness was
  justified); no seed/temperature control (model nondeterminism
  unquantified — the step-5 realtool-012 PASS did not reproduce under
  either variant, and V1/V2 were run in different epochs, so the
  V1-vs-V2 contrast is descriptive, not a significance claim);
  V1 and V2 differ in BOTH position and content, so the split result
  says "which variant rescues engagement", not "which prompt factor
  is the cause" (DESIGN §2); AtCoder letter used as a difficulty proxy.

## 6. Files

DESIGN.md, RUN_LOG.md, RESULTS.md (this file), summary.json,
summary.md, fixtures.json, run_v6_driver.py (+ step-5 original copy),
compute_stats.py, verify_scoring.py, warmup.py,
01_modal_vllm_rebuild_C_realtool.py, billing_before.json /
billing_after_deploy.json / billing_checkpoint_pilot.json /
billing_checkpoint_V1_16cells.json / billing_after_V1.json /
billing_checkpoint_V2_pilot.json / billing_checkpoint_V2_16cells.json /
billing_after.json / billing_after2.json, app_list_before_deploy.log /
app_list_after_deploy.log / app_list_after_stop.log,
modal_deploy.log, warmup_pi-mono.log/json, v1_models_pi-mono.json,
pilot_V1.log / pilot_V2.log, full_V1.log / full_V1_resume.log /
full_V2.log, rerun_V1_049_base.log / rerun_V1_006_realtool.log,
REPLACEMENTS.log, health_check_*.json, upstream/fork git-status
snapshots, runs/pi-mono/<variant>/<model>/<fixture>/ (64 cells, each
with prompt, CLI outputs, parsed run record, workspace + storage
trees, solution_final.py, grading outputs, result.json) + 2 archived
`.attempt1` dirs (the replaced INFRA attempts).
