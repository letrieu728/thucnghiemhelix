# O1 — Phân tích 2 lượt (lượt O2 + lượt lặp O1, pi-mono)

Phạm vi: base + clean (90 ô × 2 lượt). Nhánh realtool bị cắt khỏi O1 theo quy tắc billing DESIGN §5 bước 1 — số realtool của O2 ở lại mức 1 lượt/ô, không có trong phân tích 2 lượt này.

Tỉ lệ gộp 2 lượt là **tỉ lệ mô tả trên 2 lượt**, không phải một ước lượng độc lập mới. McNemar tính RIÊNG từng lượt, không gộp p-value qua hai lượt.

## 1. Tỉ lệ ô đồng thuận (cùng PASS/FAIL ở cả hai lượt)

| model | tổng thể | held2 | held3 | held4 |
|---|---|---|---|---|
| base | 31/45 (0.69) | 11/15 (0.73) | 7/15 (0.47) | 13/15 (0.87) |
| clean | 40/45 (0.89) | 12/15 (0.80) | 13/15 (0.87) | 15/15 (1.00) |

Ô đổi kết quả giữa hai lượt — base (14 ô): held2_001_edit_distance (PASS→FAIL), held2_002_regex_match (PASS→FAIL), held2_011_valid_sudoku (FAIL→PASS), held2_014_rotten_oranges (PASS→FAIL), held3_002_missing_number (PASS→FAIL), held3_004_group_anagrams (PASS→FAIL), held3_008_product_except_self (FAIL→PASS), held3_009_coin_change (FAIL→PASS), held3_010_house_robber (PASS→FAIL), held3_011_letter_combinations (FAIL→PASS), held3_012_min_window_substring (FAIL→PASS), held3_015_serialize_binary_tree (PASS→FAIL), held4_013_max_path_sum (PASS→FAIL), held4_015_count_smaller (FAIL→PASS)
Ô đổi kết quả giữa hai lượt — clean (5 ô): held2_003_n_queens_count (FAIL→PASS), held2_008_median_finder (PASS→FAIL), held2_011_valid_sudoku (FAIL→PASS), held3_011_letter_combinations (FAIL→PASS), held3_012_min_window_substring (FAIL→PASS)

## 2. Pass@1 gộp 2 lượt (mô tả) + Wilson 95% CI

| model | held2 (k/30) | held3 (k/30) | held4 (k/30) | chính 30 bài (k/60) | đủ 45 bài (k/90) |
|---|---|---|---|---|---|
| base | 22/30 [0.5555, 0.8582] | 20/30 [0.4878, 0.8077] | 22/30 [0.5555, 0.8582] | 42/60 [0.5749, 0.8010] | 64/90 [0.6104, 0.7946] |
| clean | 21/30 [0.5212, 0.8334] | 24/30 [0.6269, 0.9049] | 26/30 [0.7032, 0.9469] | 50/60 [0.7197, 0.9069] | 71/90 [0.6937, 0.8605] |

Chia nhỏ theo lượt (để đọc khoảng đo được):

- base chính 30 bài: lượt O2 21/30, lượt O1 21/30 → gộp 42/60.
- base đủ 45 bài: lượt O2 33/45, lượt O1 31/45 → gộp 64/90.
- clean chính 30 bài: lượt O2 24/30, lượt O1 26/30 → gộp 50/60.
- clean đủ 45 bài: lượt O2 34/45, lượt O1 37/45 → gộp 71/90.

## 3. So sánh chính clean vs base, 30 bài chưa thấy — McNemar RIÊNG từng lượt

| lượt | clean | base | chênh | gains | losses | same_pass | same_fail | p (exact, 2 phía) |
|---|---|---|---|---|---|---|---|---|
| O2 | 24/30 | 21/30 | +3 | 5 | 2 | 19 | 4 | 0.4531 |
| O1 | 26/30 | 21/30 | +5 | 5 | 0 | 21 | 4 | 0.0625 |

Text-only (C1) từng lượt, 30 bài chính: clean lượt O2 0/30, lượt O1 0/30 (ngưỡng ≤ 1/30); base lượt O2 4/30, lượt O1 4/30.

## 4. Kiểm tra base drift trong chương trình (base lượt O2 vs lượt O1, 45 bài)

- Base lượt O2: 33/45; lượt O1: 31/45; số ô đổi kết quả: **14/45**.
- Ô base đổi kết quả: held2_001_edit_distance (PASS→FAIL), held2_002_regex_match (PASS→FAIL), held2_011_valid_sudoku (FAIL→PASS), held2_014_rotten_oranges (PASS→FAIL), held3_002_missing_number (PASS→FAIL), held3_004_group_anagrams (PASS→FAIL), held3_008_product_except_self (FAIL→PASS), held3_009_coin_change (FAIL→PASS), held3_010_house_robber (PASS→FAIL), held3_011_letter_combinations (FAIL→PASS), held3_012_min_window_substring (FAIL→PASS), held3_015_serialize_binary_tree (PASS→FAIL), held4_013_max_path_sum (PASS→FAIL), held4_015_count_smaller (FAIL→PASS)
- **drift trong-chương-trình ≥ 4 bài — mọi so sánh một-lần-chạy đều hạ xuống mức mô tả**

## 5. Đọc lại phán quyết O2 dưới ánh sáng O1

- Lượt O2: C1 ĐẠT (text-only 0/30), C2 ĐẠT (clean 24/30 vs base 21/30, chênh +3).
- Lượt O1: C1 ĐẠT (text-only 0/30), C2 ĐẠT (clean 26/30 vs base 21/30, chênh +5).
- **phán quyết O2 ổn định qua 2 lượt**
