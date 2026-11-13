# Phân tích kết quả theo từng bài — HELIX vòng 2 (offline)

Ngày phân tích: 2026-11-13. Chỉ đọc dữ liệu sẵn có và tính toán CPU local — **không chạy thêm thí nghiệm, không GPU/Modal, không sửa file gốc, không bịa số.**

Nguồn: `closed-loop/data/raw_traces/` (520 file JSON) + `analysis_round1.json` / `analysis_round2.json` (chỉ để đối chiếu số tổng) + `data/processed/sft_data.jsonl` (19) / `dpo_pairs.jsonl` (6) + đề bài trong `scripts/02_run_helix_eval.py` (lcb_001–010), `train_extra_problems.json` (lcb_011–020), `heldout2_problems.json` (held2_001–015).

## Quy ước lọc (đọc kỹ trước khi dùng bảng)

- **Bảng chính chỉ dùng lượt chuẩn temp 0.0**: vòng 2 lọc theo trường trong file trace — `run_tag` + `temperature == 0.0` (+ `model` để tách base/LoRA ở held-out). Lượt sampling temp 0.7 (`_s0`/`_s1`, chỉ minimal + opencode, 80 file) **không** nằm trong bảng chính, chỉ báo riêng ở Phụ lục B.
- Held-out v2: file base có tiền tố `heldout2_base_`, file LoRA có tiền tố `heldout2_helix-lora_` (không phải `heldout2_lora_`); phân tách theo trường `model` (`Qwen/Qwen2.5-Coder-7B-Instruct` vs `helix-lora`), mỗi nhóm đúng 60 file.
- Trace vòng 1 không có trường `run_tag`/`temperature` nên lọc theo tiền tố tên file (`build_` / `rebuild_` / `heldout_base_` / `heldout_helix-lora_`).
- Mỗi ô trong bảng = 1 file trace, giá trị `passed` (đã kiểm: `passed` khớp `test_result.passed` ở cả 520 file). Thứ tự harness trong chuỗi 4 ký tự: **M**inimal · **P**i-mono · **H**ermes-agent · **O**pencode. ✓ = đậu, – = trượt.
- "Base" ở bảng train = BUILD2 (model gốc); "LoRA" = REBUILD2 (model + adapter vòng 2). Ở bảng held-out, "Base"/"LoRA" là hai lượt chạy heldout2 trên cùng 15 bài.

## Tóm tắt

| Tập | Cải thiện | Tụt | Không đổi | Tổng |
|---|---|---|---|---|
| Train-20 (build2 → rebuild2) | 5 bài | 1 bài | 14 bài | 60/80 → **66/80** (+6 ô) |
| Held-out v2-15 (base → LoRA) | 3 bài | 1 bài | 11 bài | 50/60 → **53/60** (+3 ô) |

- Train: 5 bài cải thiện gồm lcb_002 (+1), lcb_003 (+2), lcb_013 (+2), lcb_017 (+1), lcb_019 (+1); 1 bài tụt là lcb_009 (−1); 14 bài không đổi gồm 13 bài đậu 4/4 ở cả hai lượt và lcb_008 (3/4 cả hai lượt).
- Held-out v2: 3 bài cải thiện gồm held2_001 (+1), held2_002 (+1), held2_014 (+2); 1 bài tụt là held2_008 (−1); 11 bài không đổi gồm 10 bài đậu 4/4 ở cả hai lượt và held2_009 (0/4 cả hai lượt).
- Toàn bộ mức tăng ròng đều tập trung ở rất ít bài: train +6 ô đến từ 6 bài có đổi chiều (8 ô đổi chiều, 7 tăng / 1 giảm); held-out +3 ô đến từ 4 bài có đổi chiều (7 ô đổi chiều, 5 tăng / 2 giảm), trong đó riêng held2_014 đóng góp +2 ròng với 4 ô đổi chiều.

## Bảng 1 — Tập train-20: build2 (base) vs rebuild2 (LoRA), lượt chuẩn

| Bài | Tên bài | Base (M·P·H·O) | LoRA (M·P·H·O) | Base | LoRA | Δ | Phân loại |
|---|---|---|---|---|---|---|---|
| `lcb_001_two_sum` | Two Sum with Indices | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_002_valid_parentheses` | Valid Parentheses String with Wildcard | `––––` | `–✓––` | 0/4 | 1/4 | +1 | Cải thiện |
| `lcb_003_lru_cache` | LRU Cache Implementation with Eviction Return | `––––` | `✓––✓` | 0/4 | 2/4 | +2 | Cải thiện |
| `lcb_004_reverse_linked_list` | Reverse a Linked List | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_005_binary_search` | Binary Search | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_006_max_subarray` | Maximum Subarray Sum and Slice | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_007_climbing_stairs` | Climbing Stairs (DP) | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_008_merge_intervals` | Merge Overlapping Intervals with Count | `–✓✓✓` | `–✓✓✓` | 3/4 | 3/4 | 0 | Không đổi |
| `lcb_009_word_break` | Word Break Sentences (DP/Backtracking) | `–––✓` | `––––` | 1/4 | 0/4 | -1 | Tụt |
| `lcb_010_number_of_islands` | Number of Islands (BFS/DFS) | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_011_trap_rain_water` | Trapping Rain Water | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_012_can_finish_courses` | Course Schedule (Cycle Detection) | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_013_longest_palindromic_substring` | Longest Palindromic Substring | `––––` | `✓––✓` | 0/4 | 2/4 | +2 | Cải thiện |
| `lcb_014_daily_temperatures` | Daily Temperatures | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_015_word_search` | Word Search in Grid | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_016_partition_equal_subset` | Partition Equal Subset Sum | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_017_merge_k_sorted_lists` | Merge K Sorted Linked Lists | `✓✓–✓` | `✓✓✓✓` | 3/4 | 4/4 | +1 | Cải thiện |
| `lcb_018_decode_string` | Decode Nested String | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `lcb_019_permutations_unique` | Unique Permutations | `–––✓` | `✓––✓` | 1/4 | 2/4 | +1 | Cải thiện |
| `lcb_020_min_jumps` | Jump Game II (Minimum Jumps) | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| **Tổng** | | | | **60/80** | **66/80** | **+6** | |

### Đọc bảng 1

- **Không bài nào 0/4 ở cả hai lượt.** Ba bài base 0/4 ở lượt chuẩn — lcb_002, lcb_003, lcb_013 — đều có ô đậu ở rebuild2. Ngược lại, lcb_009 là bài duy nhất 0/4 ở rebuild2 (base còn 1/4).
- **13 bài đậu hết 4/4 ở cả hai lượt**: lcb_001, 004, 005, 006, 007, 010, 011, 012, 014, 015, 016, 018, 020. Các bài này không đóng góp gì vào chênh lệch và cũng không thể hiện cải thiện (đã trần).
- **lcb_002 — trường hợp đặc biệt, đã kiểm chứng:** base không đậu lần nào trong cả 8 trace build2 (4 lượt chuẩn + 4 sampling), và là bài duy nhất trong 20 bài **không có record SFT/DPO nào** (19 SFT phủ 19 bài còn lại, mỗi bài đúng 1 record; 6 DPO phủ lcb_003, 008, 009, 013, 017, 019). LoRA vẫn đậu 1 ô (pi-mono) ở rebuild2. Mức +1 này không thể quy cho huấn luyện trực tiếp trên bài này — nó chỉ cho thấy một ô đổi chiều, không phải bằng chứng học được bài đó. (Ở vòng 1, lcb_002 cũng 0/4 ở build và 1/4 ở rebuild, ô đậu là opencode — khác harness với vòng 2.)
- **lcb_009 — bài tụt duy nhất và cũng là bài mong manh nhất:** lần đậu duy nhất của base trong 8 trace build2 là ô opencode lượt chuẩn (cả 4 lượt sampling đều trượt); chính ô đó trượt ở rebuild2. Cả record SFT lẫn cặp DPO của bài này đều lấy từ đúng lần đậu duy nhất đó, nhưng rebuild2 vẫn 0/4.
- **lcb_003 và lcb_013** có mẫu giống nhau: 0/4 → 2/4, cùng đậu minimal + opencode, cùng trượt pi-mono + hermes-agent. Cả hai đều có cặp DPO mà phía "chosen" chỉ có được nhờ lượt sampling có ô đậu (vd DPO của lcb_003 lấy chosen từ `build2_lcb_003_lru_cache_opencode_s0.json`).
- **lcb_008** là bài duy nhất không đổi mà không trần: minimal trượt ở cả hai lượt, 3 harness còn lại đậu cả hai lượt. Lượt sampling của bài này 3/4 (minimal_s0 đậu, minimal_s1 trượt) — cùng một harness, cùng một bài, kết quả đổi theo lượt lấy mẫu.

## Bảng 2 — Tập held-out v2-15: base vs LoRA, lượt chuẩn

| Bài | Tên bài | Base (M·P·H·O) | LoRA (M·P·H·O) | Base | LoRA | Δ | Phân loại |
|---|---|---|---|---|---|---|---|
| `held2_001_edit_distance` | Edit Distance | `✓✓–✓` | `✓✓✓✓` | 3/4 | 4/4 | +1 | Cải thiện |
| `held2_002_regex_match` | Regular Expression Matching | `✓✓✓–` | `✓✓✓✓` | 3/4 | 4/4 | +1 | Cải thiện |
| `held2_003_n_queens_count` | N-Queens Count | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_004_number_of_lis` | Number of Longest Increasing Subsequences | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_005_word_ladder` | Word Ladder Length | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_006_sliding_window_max` | Sliding Window Maximum | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_007_course_order` | Course Schedule II (Valid Order) | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_008_median_finder` | Find Median from Data Stream | `–✓✓✓` | `––✓✓` | 3/4 | 2/4 | -1 | Tụt |
| `held2_009_next_permutation` | Next Permutation | `––––` | `––––` | 0/4 | 0/4 | 0 | Không đổi |
| `held2_010_three_sum` | 3Sum | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_011_valid_sudoku` | Valid Sudoku | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_012_gas_station` | Gas Station Circuit | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_013_decode_ways` | Decode Ways | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| `held2_014_rotten_oranges` | Rotting Oranges | `––✓–` | `✓✓–✓` | 1/4 | 3/4 | +2 | Cải thiện |
| `held2_015_longest_consecutive` | Longest Consecutive Sequence | `✓✓✓✓` | `✓✓✓✓` | 4/4 | 4/4 | 0 | Không đổi |
| **Tổng** | | | | **50/60** | **53/60** | **+3** | |

### Đọc bảng 2 (đã kiểm chứng lại từ traces, không tin mù)

- **held2_009 (Next Permutation) — đúng là trượt 0/4 ở cả hai lượt.** Cả 8 file trace đều `passed: false` (xem đối chiếu ở mục Kiểm chứng). Đây là bài duy nhất không ô nào đậu ở cả base lẫn LoRA, và là bài duy nhất của held-out v2 mà union "giải được bởi ≥1 harness" không đạt được ở cả hai lượt.
- **held2_014 (Rotting Oranges) — đúng là cải thiện 1/4 → 3/4**, nhưng con số ròng che đi 4 ô đổi chiều: base chỉ đậu hermes-agent; LoRA đậu minimal, opencode, pi-mono và làm trượt đúng ô hermes-agent đó. Đây là ví dụ rõ nhất rằng "cải thiện theo bài" không có nghĩa là mọi ô đều tốt lên.
- **held2_008 (Find Median from Data Stream) — đúng là tụt 3/4 → 2/4**: ô pi-mono đậu ở base trượt ở LoRA; minimal trượt ở cả hai lượt. Đây là bài tụt duy nhất của held-out v2.
- **held2_001 và held2_002** mỗi bài +1 (sửa lần lượt ô hermes-agent và opencode, lên 4/4).
- **10 bài đậu hết 4/4 ở cả hai lượt**: held2_003, 004, 005, 006, 007, 010, 011, 012, 013, 015. Dù cả 15 bài held-out v2 đều gắn nhãn "hard" trong file đề, base đã đậu trọn 10/15 bài — nhãn độ khó là do người soạn gắn, độ khó thực nghiệm phải đo bằng tỉ lệ trượt của base (xem Bàn luận b).

## Bàn luận

### (a) Các ô trong cùng một bài KHÔNG độc lập — kiểm định ở cấp độ bài

McNemar headline (train: 7 tăng / 1 giảm, p = 0,0703 trên 80 ô; held-out v2: 5 tăng / 2 giảm, p = 0,4531 trên 60 ô) coi mỗi ô (bài × harness) là một cặp độc lập. Giả định này không đứng: 4 ô của cùng một bài dùng chung đề bài, chung model, chung test case — và dữ liệu cho thấy chúng chuyển động cùng nhau:

- Ở build2, 16/20 bài có kết quả nhất quán cả 4 ô (toàn đậu hoặc toàn trượt); ở rebuild2 là 15/20; ở held-out v2 base là 11/15. Chỉ 4–5 bài mỗi lượt là "chia rẽ" giữa các harness.
- Các ô đổi chiều tập trung vào ít bài: 8 ô đổi chiều của train nằm trong 6 bài; 7 ô đổi chiều của held-out v2 nằm trong 4 bài, riêng held2_014 chiếm 4 ô. Số quan sát độc lập hiệu dụng nằm đâu đó giữa số bài (20/15) và số ô (80/60) — chắc chắn nhỏ hơn số ô mà McNemar dùng, nên McNemar phóng đại lực thống kê (p nhỏ hơn mức xứng đáng).

Để bổ sung góc nhìn — **không thay thế kết luận headline** — dưới đây là hai kiểm định ở cấp độ bài, trên số ô đậu mỗi bài (0–4), mỗi bài là một cặp ghép base–LoRA:

| Kiểm định cấp bài | Train-20 | Held-out v2-15 |
|---|---|---|
| Sign test (exact, hai phía; chỉ đếm dấu của Δ, bỏ các bài Δ = 0) | 5 tăng / 1 giảm, 14 hòa; n = 6; **p = 0,2188** | 3 tăng / 1 giảm, 11 hòa; n = 4; **p = 0,6250** |
| Wilcoxon signed-rank (exact, hai phía; liệt kê toàn bộ 2^n cách gán dấu trên các Δ ≠ 0, hạng trung bình cho |Δ| bằng nhau) | n ≠ 0 = 6, W+ = 18,5, W− = 2,5; **p = 0,1562** | n ≠ 0 = 4, W+ = 8,0, W− = 2,0; **p = 0,5000** |
| McNemar cấp ô (headline, để đối chiếu) | p = 0,0703 | p = 0,4531 |

Giả định và giới hạn, nói rõ:

- **Sign test** giả định các bài độc lập với nhau và (dưới H0) mỗi bài không hòa có xác suất tăng/giảm bằng nhau. Nó bỏ qua độ lớn của Δ (bài +2 và +1 tính như nhau) và bỏ 14/20 (train) và 11/15 (held-out) bài hòa — nên lực rất thấp: với n = 6, ngay cả 6/6 bài cùng chiều cũng chỉ cho p = 0,0313; với n = 4, 4/4 cùng chiều cũng chỉ cho p = 0,1250. Không bác bỏ được H0 ở đây không có nghĩa là "không có tác dụng", mà là "mẫu quá nhỏ để phân biệt".
- **Wilcoxon** dùng thêm độ lớn, nhưng giả định phân phối của các Δ đối xứng quanh median — đáng ngờ với điểm số rời rạc 0–4, nhiều hòa và Δ chỉ nhận giá trị −1/+1/+2. Kết quả Wilcoxon ở đây chỉ mang tính bổ sung, và cả hai kiểm định đều đồng thuận với headline: **không đạt ý nghĩa thống kê ở α = 0,05 ở bất kỳ cấp độ nào**.
- Cả hai kiểm định cấp bài vẫn giả định các bài độc lập — hợp lý hơn giả định các ô độc lập, nhưng các bài vẫn cùng một bộ test-style LeetCode và cùng một lần chạy model, nên "độc lập" cũng chỉ là gần đúng.
- Vấn đề sâu hơn mà không kiểm định nào sửa được: mỗi ô chỉ có **một** lần chạy temp 0.0, không lặp lại. Một ô đổi chiều có thể do adapter, cũng có thể do biến thiên giữa các lần chạy (bằng chứng: lcb_008 minimal_s0 đậu / minimal_s1 trượt ở sampling; lcb_002 đậu ở harness khác nhau giữa vòng 1 và vòng 2). Không có lần lặp thì không tách được hai nguồn này.

Kết luận cho mục (a): **giữ nguyên kết luận headline** (chênh lệch không có ý nghĩa thống kê; McNemar p = 0,0703 / 0,4531). Góc nhìn cấp bài cho thấy bằng chứng còn yếu hơn khi tôn trọng cấu trúc cụm theo bài — đúng như kỳ vọng khi lực thống kê thấp, không phải mâu thuẫn mới.

### (b) Bài khó phân biệt (held-out v2) vs bài trần (held-out v1)

- **Held-out v1 (10 bài, vòng 1) gần như hoàn toàn trần:** base 39/40, LoRA 40/40. 9/10 bài đậu 4/4 ở cả hai lượt; ô trượt duy nhất của base là held_006 (Top K Frequent Elements) trên pi-mono — và đó là **lỗi hạ tầng, không phải đáp án sai**: trace ghi `Error code: 400 - This model's maximum context length is 4096 tokens…` (prompt 3073 token + 1024 token đầu ra vượt giới hạn). Nói cách khác, held-out v1 có **0 lần trượt do năng lực** của base — tập này không thể đo được cải thiện hay thoái hóa, mọi chênh lệch đều là nhiễu/trần. (Chi tiết theo bài ở Phụ lục A.)
- **Held-out v2 (15 bài) phân biệt được tốt hơn, nhưng vẫn trần nặng:** base trượt 10/60 ô, rải trên 5 bài (held2_001, 002, 008, 009, 014), gồm 1 bài trượt trọn (held2_009). 10/15 bài vẫn đậu 4/4 ngay từ base — các bài đó chỉ có thể giữ nguyên hoặc tụt, không thể hiện cải thiện. Số bài "có cửa cải thiện" thực sự chỉ là 5, và số bài "có cửa tụt" là 14.
- **Tập train-20 cũng trần nặng:** 13/20 bài đậu 4/4 ở cả hai lượt; toàn bộ chênh lệch đến từ 7 bài còn lại. Điều này không có gì lạ với bài LeetCode easy/medium và model 7B đã mạnh — nhưng nó có nghĩa là tỉ lệ đậu tổng (75% → 82,5%) phóng đại cảm giác tiến bộ: phần lớn bài không thay đổi gì.
- Nhãn "hard" của held-out v2 không đảm bảo độ khó thực nghiệm: base vẫn đậu 50/60. Độ khó nên báo bằng tỉ lệ trượt của base, không bằng nhãn.

### (c) Không kết luận khái quát hóa

Từ held-out v2, **không được kết luận LoRA khái quát hóa** (cũng như không được kết luận nó làm hại):

1. Chênh lệch +3 ô không có ý nghĩa thống kê ở cả cấp ô (McNemar p = 0,4531) lẫn cấp bài (sign test p = 0,6250; Wilcoxon exact p = 0,5000).
2. Mức tăng ròng tập trung vào một bài (held2_014, +2 trong tổng +3) mà bên trong có cả tăng lẫn giảm; đồng thời có 1 bài tụt (held2_008). Mẫu hình này giống nhiễu chạy-lại hơn là cải thiện hệ thống.
3. n = 15 bài tự chọn (không phải mẫu ngẫu nhiên của một quần thể bài nào), mỗi ô một lần chạy, không lặp lại — không có cơ sở để ngoại suy ra "bài mới nói chung".
4. Dữ liệu huấn luyện rất nhỏ (19 SFT + 6 DPO) và 1 bài train (lcb_002) cải thiện mà không hề có trong dữ liệu huấn luyện, trong khi 1 bài có cả SFT+DPO (lcb_009) lại tụt — thiết kế này không cho phép quy kết nhân quả "huấn luyện → cải thiện bài X".

Cách nói trung thực: **held-out v2 không cho bằng chứng khái quát hóa, cũng không cho bằng chứng thoái hóa rõ rệt; kết quả phù hợp với "không thay đổi đáng kể" trong giới hạn của 15 bài và một lần chạy.** Muốn trả lời câu hỏi khái quát hóa cần nhiều bài phân biệt hơn và/hoặc lặp lại — việc đó nằm ngoài phạm vi phân tích offline này và không được thực hiện.

## Kiểm chứng

### Đối chiếu số tổng (tính lại từ traces vs số chốt)

| Lượt | Tính lại từ traces | Số chốt | Từng harness (tính lại) | Khớp? |
|---|---|---|---|---|
| BUILD2 | 60/80 | 60/80 | minimal 14, pi-mono 15, hermes 14, opencode 17 | ✓ |
| REBUILD2 | 66/80 | 66/80 | minimal 17, pi-mono 16, hermes 15, opencode 18 | ✓ |
| Held-out v2 base | 50/60 | 50/60 | minimal 12, pi-mono 13, hermes 13, opencode 12 | ✓ |
| Held-out v2 LoRA | 53/60 | 53/60 | minimal 13, pi-mono 13, hermes 13, opencode 14 | ✓ |
| Vòng 1 BUILD → REBUILD | 28/40 → 31/40 | 28/40 → 31/40 | build 6/7/7/8; rebuild 7/8/7/9 | ✓ |
| Vòng 1 held-out base → LoRA | 39/40 → 40/40 | 39/40 → 40/40 | base 10/9/10/10; LoRA 10/10/10/10 | ✓ |

Kiểm tra thêm: danh sách ô đổi chiều tính lại khớp từng ô với `flips` trong `analysis_round2.json` (train 8 ô, held-out v2 7 ô); McNemar tính lại từ số ô bất đồng khớp p = 0,0703 / 0,4531; tổng các Δ theo bài khớp chênh lệch tổng (+6 train, +3 held-out v2); `passed` khớp `test_result.passed` ở cả 520 file; mỗi nhóm lượt chuẩn có đúng 1 trace cho mỗi cặp (bài, harness), không thiếu không thừa.

### Đối chiếu trực tiếp 3 bài với file trace (trường `passed`)

**1. held2_014_rotten_oranges — 1/4 → 3/4:**

| File trace | Model | passed |
|---|---|---|
| `heldout2_base_held2_014_rotten_oranges_hermes-agent.json` | base | true |
| `heldout2_base_held2_014_rotten_oranges_minimal.json` | base | false |
| `heldout2_base_held2_014_rotten_oranges_opencode.json` | base | false |
| `heldout2_base_held2_014_rotten_oranges_pi-mono.json` | base | false |
| `heldout2_helix-lora_held2_014_rotten_oranges_hermes-agent.json` | helix-lora | false |
| `heldout2_helix-lora_held2_014_rotten_oranges_minimal.json` | helix-lora | true |
| `heldout2_helix-lora_held2_014_rotten_oranges_opencode.json` | helix-lora | true |
| `heldout2_helix-lora_held2_014_rotten_oranges_pi-mono.json` | helix-lora | true |

**2. held2_009_next_permutation — 0/4 → 0/4:** cả 8 file (`heldout2_base_…` và `heldout2_helix-lora_…` × 4 harness) đều `passed: false`.

**3. lcb_003_lru_cache — 0/4 → 2/4 (lượt chuẩn vòng 2):** 4 file `build2_lcb_003_lru_cache_*.json` đều `passed: false`; ở `rebuild2_…`, minimal và opencode `passed: true`, pi-mono và hermes-agent `passed: false`.

## Phụ lục A — Vòng 1 theo từng bài (ngữ cảnh, lượt chuẩn)

Train-10 (build → rebuild): lcb_002 0→1 (opencode), lcb_003 0→1 (opencode), lcb_008 3→4 (minimal), lcb_009 1→1 nhưng đổi harness (opencode đậu → trượt, pi-mono trượt → đậu: Δ ròng 0 che 2 ô đổi chiều — cùng hiện tượng như held2_014), 6 bài còn lại 4→4. Sign test cấp bài: 3 tăng / 0 giảm, 7 hòa, p = 0,2500; Wilcoxon exact p = 0,2500. McNemar cấp ô: 4 tăng / 1 giảm, p = 0,375.

Held-out v1-10 (base → LoRA): chỉ held_006 3→4 (ô pi-mono, chính là ô lỗi HTTP 400 ở base); 9 bài còn lại 4→4. Sign test: 1 tăng / 0 giảm, 9 hòa, p = 1,0000; Wilcoxon exact p = 1,0000. McNemar cấp ô: 1 tăng / 0 giảm, p = 1,0.

## Phụ lục B — Lượt sampling temp 0.7 (riêng, không nằm trong bảng chính)

80 trace, 63 đậu (minimal + opencode, mỗi bài 4 lượt: s0/s1 × 2 harness). Theo bài (số ô đậu /4): lcb_001 4, lcb_002 0, lcb_003 1, lcb_004 4, lcb_005 4, lcb_006 4, lcb_007 4, lcb_008 3, lcb_009 0, lcb_010 4, lcb_011 4, lcb_012 4, lcb_013 2, lcb_014 4, lcb_015 4, lcb_016 4, lcb_017 2, lcb_018 4, lcb_019 3, lcb_020 4. Chỉ 5 bài có kết quả sampling chia rẽ (lcb_003, 008, 013, 017, 019) — 5 trong 6 bài có cặp DPO nằm trong nhóm này; ngoại lệ là lcb_009 (sampling 0/4, cặp DPO lấy tương phản từ lượt chuẩn). Lượt sampling có vai trò thực chất trong trích xuất dữ liệu huấn luyện: 14/19 record SFT và 2/6 phía "chosen" của DPO lấy từ trace sampling (trong 160 trace build2 mà bộ trích xuất dùng, gồm cả sampling). Không so sánh trực tiếp tỉ lệ sampling với tỉ lệ lượt chuẩn theo bài vì khác harness-phủ (sampling chỉ 2 harness) và khác nhiệt độ.

## Phụ lục C — Tệp kèm theo

- `per_task_results.csv`: 35 dòng (20 train + 15 heldout2), cột `problem_id, ten_bai, do_kho, tap, base_pass, lora_pass, delta, phan_loai, ghi_chu`; `base_pass`/`lora_pass` tính trên 4 harness lượt chuẩn; `ghi_chu` nêu harness đổi chiều và (với train) số record SFT/DPO của bài. Tổng cột trong CSV khớp số chốt (train 60→66, held-out v2 50→53).
- Mọi số trong tài liệu này đều tính lại từ 520 file trace bằng script đọc-only; không số nào chép tay từ báo cáo trước mà không đối chiếu.
