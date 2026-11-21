# O2 — Train lai adapter fix SACH (lcb_* only) + danh gia 45 bai (pi-mono)

**CANH BAO O NHIEM:** cac o held2 cua `realtool` la O NHIEM (adapter cu train tren 16 SFT + 4 DPO thuoc held2) — khong dung so held2 cua nhanh cu de ket luan gi. So sanh moi-vs-cu chi doc tren held3+held4 (30 bai), dang mo ta.

## Phan quyet chinh (30 bai held3+held4, dang ky truoc)

- C1 (hanh vi): text-only clean = 0/30 (nguong <= 1/30) → DAT
- C2 (ket qua): Pass@1 clean 26/30 vs base 21/30 (chenh +5) → DAT
- McNemar (kham pha): p = 0.0625 (p<0,05 KHONG yeu cau cho phan quyet)
- **C1+C2 DAT: fix sach khai quat hoa — hanh vi da sua tren bai chua thay, khong thua base (n=30, 1 luot/o)**
- Ghi chu: clean hon base >= 4 bai tren 30 bai — 'lan dau co thang sach tren held-out' (khong nang ngon tu phan quyet qua 'ung ho khai quat hoa tren bai ham pi-mono').

## Bang du 45 bai (3 nhanh)

| model | Pass@1 /45 | Wilson 95% | text-only /45 | INFRA |
|---|---|---|---|---|
| base | 31/45 | [0.5434, 0.8047] | 7/45 | 0 |
| clean | 37/45 | [0.6867, 0.9071] | 0/45 | 0 |
| realtool | 0/0 | [0.0000, 0.0000] | 0/0 | 0 |

## Tach theo cohort (moi cohort 15 bai)

| model | cohort | Pass@1 /15 | Wilson 95% | text-only /15 | ghi chu |
|---|---|---|---|---|---|
| base | held2 | 10/15 | [0.4171, 0.8482] | 3/15 |  |
| base | held3 | 10/15 | [0.4171, 0.8482] | 2/15 |  |
| base | held4 | 11/15 | [0.4805, 0.8910] | 2/15 |  |
| clean | held2 | 11/15 | [0.4805, 0.8910] | 0/15 |  |
| clean | held3 | 13/15 | [0.6212, 0.9626] | 0/15 |  |
| clean | held4 | 13/15 | [0.6212, 0.9626] | 0/15 |  |
| realtool | held2 | 0/0 | [0.0000, 0.0000] | 0/0 | O NHIEM (realtool train tren held2) |
| realtool | held3 | 0/0 | [0.0000, 0.0000] | 0/0 |  |
| realtool | held4 | 0/0 | [0.0000, 0.0000] | 0/0 |  |

## base: 31/45 PASS (rate 0.6889, Wilson 95% [0.5434, 0.8047]; INFRA 0/45)
- no-tool-call runs: 7/45 (0 PASS); wrote file: 31/37 PASS
- avg latency (scored): 22.56s; avg steps: 2.09; tool calls: {'bash': 24, 'write': 45}

## clean: 37/45 PASS (rate 0.8222, Wilson 95% [0.6867, 0.9071]; INFRA 0/45)
- no-tool-call runs: 0/45 (0 PASS); wrote file: 37/45 PASS
- avg latency (scored): 35.14s; avg steps: 3.0; tool calls: {'bash': 51, 'read': 1, 'write': 49}

## realtool: 0/0 PASS (rate 0.0000, Wilson 95% [0.0000, 0.0000]; INFRA 0/0)
- no-tool-call runs: 0/0 (0 PASS); wrote file: 0/0 PASS
- avg latency (scored): 0.0s; avg steps: 0.0; tool calls: {}

## McNemar base vs clean — CHINH (held3+held4, 30 bai): 30 cap, gains 5, losses 0, same_pass 21, same_fail 4, p (exact, 2 phia) = 0.0625
Cap loai khoi phep thu (INFRA/thieu): 0

## McNemar base vs clean — du 45 bai (mo ta): 45 cap, gains 6, losses 0, same_pass 31, same_fail 8, p (exact, 2 phia) = 0.0312
Cap loai khoi phep thu (INFRA/thieu): 0

## McNemar base vs realtool — du 45 bai (mo ta; held2 cua realtool O NHIEM): 0 cap, gains 0, losses 0, same_pass 0, same_fail 0, p (exact, 2 phia) = 1.0
Cap loai khoi phep thu (INFRA/thieu): 45

## McNemar realtool vs clean — held3+held4, 30 bai (mo ta): 0 cap, gains 0, losses 0, same_pass 0, same_fail 0, p (exact, 2 phia) = 1.0
Cap loai khoi phep thu (INFRA/thieu): 30

## Bang flip theo bai (base → clean → realtool)

| task_id | base | clean | realtool |
|---|---|---|---|
| held2_001_edit_distance | FAIL | PASS |  [O NHIEM] |
| held2_002_regex_match | FAIL | FAIL |  [O NHIEM] |
| held2_003_n_queens_count | PASS | PASS |  [O NHIEM] |
| held2_004_number_of_lis | PASS | PASS |  [O NHIEM] |
| held2_005_word_ladder | PASS | PASS |  [O NHIEM] |
| held2_006_sliding_window_max | PASS | PASS |  [O NHIEM] |
| held2_007_course_order | PASS | PASS |  [O NHIEM] |
| held2_008_median_finder | FAIL | FAIL |  [O NHIEM] |
| held2_009_next_permutation | FAIL | FAIL |  [O NHIEM] |
| held2_010_three_sum | PASS | PASS |  [O NHIEM] |
| held2_011_valid_sudoku | PASS | PASS |  [O NHIEM] |
| held2_012_gas_station | PASS | PASS |  [O NHIEM] |
| held2_013_decode_ways | PASS | PASS |  [O NHIEM] |
| held2_014_rotten_oranges | FAIL | FAIL |  [O NHIEM] |
| held2_015_longest_consecutive | PASS | PASS |  [O NHIEM] |
| held3_001_valid_anagram | PASS | PASS |  |
| held3_002_missing_number | FAIL | PASS |  |
| held3_003_majority_element | PASS | PASS |  |
| held3_004_group_anagrams | FAIL | PASS |  |
| held3_005_top_k_frequent | PASS | PASS |  |
| held3_006_longest_substring_no_repeat | PASS | PASS |  |
| held3_007_container_most_water | PASS | PASS |  |
| held3_008_product_except_self | PASS | PASS |  |
| held3_009_coin_change | PASS | PASS |  |
| held3_010_house_robber | FAIL | PASS |  |
| held3_011_letter_combinations | PASS | PASS |  |
| held3_012_min_window_substring | PASS | PASS |  |
| held3_013_burst_balloons | FAIL | FAIL |  |
| held3_014_find_duplicate_number | PASS | PASS |  |
| held3_015_serialize_binary_tree | FAIL | FAIL |  |
| held4_001_roman_to_integer | PASS | PASS |  |
| held4_002_best_time_stock | PASS | PASS |  |
| held4_003_longest_common_prefix | PASS | PASS |  |
| held4_004_rotate_array | FAIL | FAIL |  |
| held4_005_sort_colors | PASS | PASS |  |
| held4_006_evaluate_rpn | PASS | PASS |  |
| held4_007_min_stack | PASS | PASS |  |
| held4_008_validate_bst | PASS | PASS |  |
| held4_009_level_order | FAIL | PASS |  |
| held4_010_spiral_matrix | PASS | PASS |  |
| held4_011_trie | PASS | PASS |  |
| held4_012_largest_rectangle_histogram | PASS | PASS |  |
| held4_013_max_path_sum | FAIL | FAIL |  |
| held4_014_candy | FAIL | PASS |  |
| held4_015_count_smaller | PASS | PASS |  |

NO POOLED TEST across cohorts; NO test across harnesses (pi-mono only); NO comparison against old-run base numbers — only within-this-run comparisons.
