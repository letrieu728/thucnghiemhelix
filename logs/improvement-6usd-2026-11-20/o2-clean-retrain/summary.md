# O2 — Train lai adapter fix SACH (lcb_* only) + danh gia 45 bai (pi-mono)

**CANH BAO O NHIEM:** cac o held2 cua `realtool` la O NHIEM (adapter cu train tren 16 SFT + 4 DPO thuoc held2) — khong dung so held2 cua nhanh cu de ket luan gi. So sanh moi-vs-cu chi doc tren held3+held4 (30 bai), dang mo ta.

## Phan quyet chinh (30 bai held3+held4, dang ky truoc)

- C1 (hanh vi): text-only clean = 0/30 (nguong <= 1/30) → DAT
- C2 (ket qua): Pass@1 clean 24/30 vs base 21/30 (chenh +3) → DAT
- McNemar (kham pha): p = 0.4531 (p<0,05 KHONG yeu cau cho phan quyet)
- **C1+C2 DAT: fix sach khai quat hoa — hanh vi da sua tren bai chua thay, khong thua base (n=30, 1 luot/o)**

## Bang du 45 bai (3 nhanh)

| model | Pass@1 /45 | Wilson 95% | text-only /45 | INFRA |
|---|---|---|---|---|
| base | 33/45 | [0.5896, 0.8404] | 5/45 | 0 |
| clean | 34/45 | [0.6133, 0.8576] | 0/45 | 0 |
| realtool | 35/45 | [0.6373, 0.8746] | 0/45 | 0 |

## Tach theo cohort (moi cohort 15 bai)

| model | cohort | Pass@1 /15 | Wilson 95% | text-only /15 | ghi chu |
|---|---|---|---|---|---|
| base | held2 | 12/15 | [0.5481, 0.9295] | 1/15 |  |
| base | held3 | 10/15 | [0.4171, 0.8482] | 3/15 |  |
| base | held4 | 11/15 | [0.4805, 0.8910] | 1/15 |  |
| clean | held2 | 10/15 | [0.4171, 0.8482] | 0/15 |  |
| clean | held3 | 11/15 | [0.4805, 0.8910] | 0/15 |  |
| clean | held4 | 13/15 | [0.6212, 0.9626] | 0/15 |  |
| realtool | held2 | 12/15 | [0.5481, 0.9295] | 0/15 | O NHIEM (realtool train tren held2) |
| realtool | held3 | 11/15 | [0.4805, 0.8910] | 0/15 |  |
| realtool | held4 | 12/15 | [0.5481, 0.9295] | 0/15 |  |

## base: 33/45 PASS (rate 0.7333, Wilson 95% [0.5896, 0.8404]; INFRA 0/45)
- no-tool-call runs: 5/45 (0 PASS); wrote file: 33/40 PASS
- avg latency (scored): 22.08s; avg steps: 2.11; tool calls: {'bash': 23, 'write': 43}

## clean: 34/45 PASS (rate 0.7556, Wilson 95% [0.6133, 0.8576]; INFRA 0/45)
- no-tool-call runs: 0/45 (0 PASS); wrote file: 34/43 PASS
- avg latency (scored): 44.84s; avg steps: 3.11; tool calls: {'bash': 62, 'edit': 1, 'read': 1, 'write': 49}

## realtool: 35/45 PASS (rate 0.7778, Wilson 95% [0.6373, 0.8746]; INFRA 0/45)
- no-tool-call runs: 0/45 (0 PASS); wrote file: 35/45 PASS
- avg latency (scored): 29.96s; avg steps: 2.53; tool calls: {'bash': 26, 'edit': 1, 'read': 1, 'write': 46}

## McNemar base vs clean — CHINH (held3+held4, 30 bai): 30 cap, gains 5, losses 2, same_pass 19, same_fail 4, p (exact, 2 phia) = 0.4531
Cap loai khoi phep thu (INFRA/thieu): 0

## McNemar base vs clean — du 45 bai (mo ta): 45 cap, gains 6, losses 5, same_pass 28, same_fail 6, p (exact, 2 phia) = 1.0
Cap loai khoi phep thu (INFRA/thieu): 0

## McNemar base vs realtool — du 45 bai (mo ta; held2 cua realtool O NHIEM): 45 cap, gains 7, losses 5, same_pass 28, same_fail 5, p (exact, 2 phia) = 0.7744
Cap loai khoi phep thu (INFRA/thieu): 0

## McNemar realtool vs clean — held3+held4, 30 bai (mo ta): 30 cap, gains 1, losses 0, same_pass 23, same_fail 6, p (exact, 2 phia) = 1.0
Cap loai khoi phep thu (INFRA/thieu): 0

## Bang flip theo bai (base → clean → realtool)

| task_id | base | clean | realtool |
|---|---|---|---|
| held2_001_edit_distance | PASS | PASS | PASS [O NHIEM] |
| held2_002_regex_match | PASS | FAIL | FAIL [O NHIEM] |
| held2_003_n_queens_count | PASS | FAIL | PASS [O NHIEM] |
| held2_004_number_of_lis | PASS | PASS | PASS [O NHIEM] |
| held2_005_word_ladder | PASS | PASS | FAIL [O NHIEM] |
| held2_006_sliding_window_max | PASS | PASS | PASS [O NHIEM] |
| held2_007_course_order | PASS | PASS | PASS [O NHIEM] |
| held2_008_median_finder | FAIL | PASS | PASS [O NHIEM] |
| held2_009_next_permutation | FAIL | FAIL | FAIL [O NHIEM] |
| held2_010_three_sum | PASS | PASS | PASS [O NHIEM] |
| held2_011_valid_sudoku | FAIL | FAIL | PASS [O NHIEM] |
| held2_012_gas_station | PASS | PASS | PASS [O NHIEM] |
| held2_013_decode_ways | PASS | PASS | PASS [O NHIEM] |
| held2_014_rotten_oranges | PASS | FAIL | PASS [O NHIEM] |
| held2_015_longest_consecutive | PASS | PASS | PASS [O NHIEM] |
| held3_001_valid_anagram | PASS | PASS | PASS |
| held3_002_missing_number | PASS | PASS | PASS |
| held3_003_majority_element | PASS | PASS | PASS |
| held3_004_group_anagrams | PASS | PASS | PASS |
| held3_005_top_k_frequent | PASS | PASS | PASS |
| held3_006_longest_substring_no_repeat | PASS | PASS | PASS |
| held3_007_container_most_water | PASS | PASS | PASS |
| held3_008_product_except_self | FAIL | PASS | PASS |
| held3_009_coin_change | FAIL | PASS | PASS |
| held3_010_house_robber | PASS | PASS | PASS |
| held3_011_letter_combinations | FAIL | FAIL | FAIL |
| held3_012_min_window_substring | FAIL | FAIL | FAIL |
| held3_013_burst_balloons | FAIL | FAIL | FAIL |
| held3_014_find_duplicate_number | PASS | PASS | PASS |
| held3_015_serialize_binary_tree | PASS | FAIL | FAIL |
| held4_001_roman_to_integer | PASS | PASS | PASS |
| held4_002_best_time_stock | PASS | PASS | PASS |
| held4_003_longest_common_prefix | PASS | PASS | PASS |
| held4_004_rotate_array | FAIL | FAIL | FAIL |
| held4_005_sort_colors | PASS | PASS | PASS |
| held4_006_evaluate_rpn | PASS | PASS | PASS |
| held4_007_min_stack | PASS | PASS | PASS |
| held4_008_validate_bst | PASS | PASS | PASS |
| held4_009_level_order | FAIL | PASS | PASS |
| held4_010_spiral_matrix | PASS | PASS | PASS |
| held4_011_trie | PASS | PASS | PASS |
| held4_012_largest_rectangle_histogram | PASS | PASS | FAIL |
| held4_013_max_path_sum | PASS | FAIL | FAIL |
| held4_014_candy | FAIL | PASS | PASS |
| held4_015_count_smaller | FAIL | PASS | PASS |

NO POOLED TEST across cohorts; NO test across harnesses (pi-mono only); NO comparison against old-run base numbers — only within-this-run comparisons.
