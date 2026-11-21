# O3 opencode prompt intervention — summary (pre-registered analysis)

Model: base only (fixed). Tasks: 10 (same as step 6). One run per cell.
Baselines REUSED from step 6 (not re-run): R8 0/10 text-only 10/10; R1 4/10 text-only 2/10.

## Per-branch Pass@1 (scored runs only; INFRA excluded)

| Branch | Recipe + suffix | Pass@1 | Wilson 95% | Text-only | Text-only Wilson 95% | Tools | Mean steps | INFRA |
|---|---|---|---|---|---|---|---|---|
| B1 | R8 + I-full | 1/10 (0.10) | [0.02, 0.40] | 0/10 | [0.00, 0.28] | bash:7, edit:1, read:10, write:7 | 2.7 | 0 |
| B2 | R8 + I-min | 2/10 (0.20) | [0.06, 0.51] | 3/10 | [0.11, 0.60] | bash:8, write:7 | 1.8 | 0 |
| B3 | R1 + I-full | 6/10 (0.60) | [0.31, 0.83] | 0/10 | [0.00, 0.28] | bash:10, edit:6, read:11, write:10 | 3.8 | 0 |

## Reused baselines (step 6, not re-run)

- R8: Pass@1 0/10, text-only 10/10, tools —
- R1: Pass@1 4/10, text-only 2/10, tools bash:4, write:8

## Per-task x branch grid (PASS/FAIL/INFRA; R8/R1 columns reused)

| task_id | B1 | B2 | B3 | R8_reused | R1_reused |
|---|---|---|---|---|---||
| lcb_001_two_sum | FAIL | PASS | PASS | FAIL | PASS |
| lcb_002_valid_parentheses | FAIL | FAIL | FAIL | FAIL | FAIL |
| lcb_005_binary_search | FAIL | FAIL | PASS | FAIL | PASS |
| lcb_010_number_of_islands | FAIL | PASS | FAIL | FAIL | PASS |
| lcb_015_word_search | PASS | FAIL | PASS | FAIL | FAIL |
| lcb_020_min_jumps | FAIL | FAIL | FAIL | FAIL | FAIL |
| held2_001_edit_distance | FAIL | FAIL | PASS | FAIL | PASS |
| held2_005_word_ladder | FAIL | FAIL | PASS | FAIL | FAIL |
| held2_009_next_permutation | FAIL | FAIL | FAIL | FAIL | FAIL |
| held2_013_decode_ways | FAIL | FAIL | PASS | FAIL | FAIL |

## McNemar, EXPLORATORY (paired vs reused baseline)

- B1_vs_R8: 10 pairs, gains 1, losses 0, same_pass 0, same_fail 9, p (exact, 2-sided) = 1.0
- B2_vs_R8: 10 pairs, gains 2, losses 0, same_pass 0, same_fail 8, p (exact, 2-sided) = 0.5
- B3_vs_R1: 10 pairs, gains 3, losses 1, same_pass 3, same_fail 3, p (exact, 2-sided) = 0.625

With the baseline at 0/10, 3 wins / 0 losses gives p=0.25 — never significant. Language allowed: 'the intervention descriptively reduced text-only from 10/10 to X/10 on 10 tasks' — no more.

## Verdicts (pre-registered DESIGN section 4 rules)

- B1: **BEHAVIOR-ONLY** — {"verdict": "BEHAVIOR-ONLY", "criteria": {"behavior_text_only_le_5": true, "outcome_pass_ge_3": false}, "baseline": "R8"}
- B2: **BEHAVIOR-ONLY** — {"verdict": "BEHAVIOR-ONLY", "criteria": {"behavior_text_only_le_5": true, "outcome_pass_ge_3": false}, "baseline": "R8"}
- B3: **CONTROL-OK** — {"verdict": "CONTROL-OK", "pass": 6, "baseline_R1_pass": 4, "note": "B3 did not drop >= 2 below R1 4/10."}
