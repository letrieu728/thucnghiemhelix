# RESULTS — O1: Lặp lại các ô quyết định của O2 (pi-mono, 20/11/2026)

Thiết kế đăng ký trước: DESIGN.md trong thư mục này (§3).
Số liệu chi tiết: `o1_2run_summary.json` + `o1_2run_summary.md` (phân tích 2 lượt);
`summary.json` + `summary.md` (chỉ lượt lặp O1, 1 lượt/ô — do compute_stats.py
của O2 tạo ra). verify_scoring.py: checked=90, mismatches=0.

## Phạm vi thực chạy — CẮT GIẢM THEO BILLING (DESIGN §5 bước 1)

O1 chạy **90 lượt** (clean 45 + base 45), KHÔNG phải 135 lượt như thiết kế gốc.
Nhánh `helix-lora-realtool` (45 lượt) bị cắt sau checkpoint chi phí sau 45 ô đầu:
tỉ lệ quan sát $0,0238/ô (4 ô INFRA đốt 21,8/46,5 phút wall) dự báo tổng chương
trình $6,62–$6,85 > trần $6,00; bỏ nhánh cũ dự báo còn $5,33–$5,50 < $6,00.
Quyết định chỉ theo billing (chưa có số base/realtool nào lúc quyết định) — xem
RUN_LOG.md. **Các hàng realtool 0/0 trong summary.json/summary.md có nghĩa là
KHÔNG CHẠY (bị cắt), không phải 0 lượt PASS.** Số realtool của O2 (35/45) ở lại
mức 1 lượt/ô; so sánh clean-vs-realtool không có lượt lặp. So sánh CHÍNH
(clean vs base trên 30 bài chưa thấy) giữ nguyên đầy đủ.

**CẢNH BÁO Ô NHIỄM (kế thừa từ O2):** các ô held2 của `realtool` là Ô NHIỄM
(adapter cũ train trên 16 SFT + 4 DPO thuộc held2) — chỉ liên quan đến số O2,
không ảnh hưởng phân tích 2 lượt base/clean dưới đây.

## 1. Tỉ lệ ô đồng thuận — cùng PASS/FAIL ở cả hai lượt (O2 + O1)

| model | tổng thể (45 ô) | held2 | held3 | held4 |
|---|---|---|---|---|
| base | **31/45 (0,69)** | 11/15 (0,73) | 7/15 (0,47) | 13/15 (0,87) |
| clean | **40/45 (0,89)** | 12/15 (0,80) | 13/15 (0,87) | 15/15 (1,00) |

- Base đổi kết quả ở 14 ô (8 PASS→FAIL, 6 FAIL→PASS); held3 là cohort bất ổn
  nhất của base (8/15 ô đổi).
- Clean đổi kết quả ở 5 ô: held2_003_n_queens_count (FAIL→PASS),
  held2_008_median_finder (PASS→FAIL), held2_011_valid_sudoku (FAIL→PASS),
  held3_011_letter_combinations (FAIL→PASS), held3_012_min_window_substring
  (FAIL→PASS). Clean ổn định hơn base rõ rệt qua 2 lượt.

## 2. Pass@1 gộp 2 lượt — TỈ LỆ MÔ TẢ trên 2 lượt, không phải ước lượng độc lập mới

| model | held2 (k/30) | held3 (k/30) | held4 (k/30) | chính 30 bài (k/60) | đủ 45 bài (k/90) |
|---|---|---|---|---|---|
| base | 22/30 [0,5555, 0,8582] | 20/30 [0,4878, 0,8077] | 22/30 [0,5555, 0,8582] | **42/60 [0,5749, 0,8010]** | 64/90 [0,6104, 0,7946] |
| clean | 21/30 [0,5212, 0,8334] | 24/30 [0,6269, 0,9049] | 26/30 [0,7032, 0,9469] | **50/60 [0,7197, 0,9069]** | 71/90 [0,6937, 0,8605] |

Khoảng đo được từng lượt (để đọc thay vì chỉ đọc số gộp):

| model | chính 30 bài: lượt O2 | lượt O1 | đủ 45 bài: lượt O2 | lượt O1 |
|---|---|---|---|---|
| base | 21/30 | 21/30 | 33/45 | 31/45 |
| clean | 24/30 | 26/30 | 34/45 | 37/45 |

## 3. So sánh chính clean vs base, 30 bài chưa thấy — McNemar RIÊNG từng lượt (KHÔNG gộp p-value)

| lượt | clean | base | chênh | gains | losses | same_pass | same_fail | p (exact, 2 phía) |
|---|---|---|---|---|---|---|---|---|
| O2 | 24/30 | 21/30 | +3 | 5 | 2 | 19 | 4 | **0,4531** |
| O1 (lặp) | 26/30 | 21/30 | +5 | 5 | 0 | 21 | 4 | **0,0625** |

- Cả hai lượt đều cho clean ≥ base; lượt lặp cho chênh lớn hơn (+5 so với +3)
  và 0 losses (lượt O2 có 2 losses). p vẫn > 0,05 ở cả hai lượt (đúng như
  DESIGN O2 §5.1 đã dự báo với n=30) — chỉ được nói "không thua base",
  không được nói "hơn base" có ý nghĩa thống kê.
- Ghi chú theo DESIGN O2 §5.1 (áp cho lượt O1): clean hơn base ≥ 4 bài trên
  30 bài ở lượt lặp (+5) → "lần đầu có thắng sạch trên held-out" — nhưng
  không nâng ngôn từ phán quyết quá "ủng hộ khái quát hóa trên bài hàm pi-mono".
- Text-only (C1) từng lượt, 30 bài chính: clean 0/30 ở CẢ HAI lượt (ngưỡng
  ≤ 1/30); base 4/30 ở cả hai lượt.

## 4. Kiểm tra base drift trong chương trình (base lượt O2 vs lượt O1, cùng 45 bài)

- Base lượt O2: 33/45; lượt O1: 31/45; **số ô đổi kết quả: 14/45** (8 PASS→FAIL,
  6 FAIL→PASS). Tổng số gần như không đổi (−2) nhưng danh tính ô đổi rất nhiều
  — đúng kiểu trôi đã thấy giữa các đợt (25→20→22→23/35).
- **drift trong-chương-trình ≥ 4 bài — mọi so sánh một-lần-chạy đều hạ xuống
  mức mô tả.** Câu này đi vào slide 15/16 khi đồng bộ (O6).
- Hệ quả: mọi số headline 1 lượt/ô của chương trình (kể cả O2) chỉ được đọc ở
  mức mô tả; khoảng đo được từ 2 lượt (mục 2) mới là cách báo cáo đúng.

## 5. Đọc lại phán quyết O2 dưới ánh sáng O1 (ghi ở đây, KHÔNG sửa RESULTS.md của O2)

| Tiêu chí | lượt O2 | lượt O1 (lặp) |
|---|---|---|
| C1 — text-only clean (≤ 1/30) | 0/30 — ĐẠT | 0/30 — ĐẠT |
| C2 — Pass@1 clean ≥ base (30 bài) | 24 vs 21 (+3) — ĐẠT | 26 vs 21 (+5) — ĐẠT |

- **phán quyết O2 ổn định qua 2 lượt** — C1+C2 đạt ở cả hai lượt, không cần
  chọn lượt đẹp (lượt lặp thậm chí cho chênh lớn hơn, nhưng phán quyết không
  đổi nên không có gì để chọn).
- Lượt lặp cũng củng cố C1: clean text-only 0/45 toàn bộ ở cả hai lượt
  (base 5/45 lượt O2, 7/45 lượt O1).

## Đọc kết quả — điểm tốt hơn / điểm đạt được

- **Phán quyết O2 đứng vững qua lượt lặp:** C1+C2 đạt cả hai lượt; clean
  text-only 0/30 cả hai lượt — hành vi đã sửa không phải may mắn một lần chạy.
- **Clean ổn định hơn base:** đồng thuận 40/45 (0,89) so với base 31/45 (0,69);
  held4 của clean 15/15 ô đồng thuận.
- **Khoảng đo được thay cho số điểm:** clean trên 30 bài chưa thấy là 24/30 rồi
  26/30 (gộp mô tả 50/60); base 21/30 rồi 21/30 (gộp 42/60) — nhóm giờ được
  phép báo cáo khoảng này thay vì "mỗi ô 1 lần chạy".
- **Cắt giảm giữ được lõi:** bỏ nhánh cũ tiết kiệm ~$0,9–1,1 mà so sánh chính
  (clean vs base) vẫn đủ 2 lượt; chương trình vẫn trong trần.

## Giới hạn / điểm chưa đạt (báo cáo nguyên trạng)

- **Base trôi 14/45 ô giữa hai lượt trong cùng chương trình** — drift ≥ 4 bài
  kích hoạt câu hạ mức mô tả (mục 4). Mọi so sánh 1 lượt/ô (kể cả các đợt cũ)
  đều phải đọc ở mức mô tả.
- **+5 bài ở lượt lặp vẫn không có ý nghĩa thống kê** (p=0,0625, n=30):
  chỉ "không thua base", không "hơn base".
- **Nhánh cũ không có lượt lặp:** realtool bị cắt theo quy tắc billing —
  không biết realtool 35/45 của O2 trôi bao nhiêu qua 2 lượt; so sánh
  mới-vs-cũ vẫn chỉ có số O2 (1 lượt/ô).
- **2 lượt vẫn là n nhỏ:** khoảng gộp còn rộng (clean chính 50/60, CI
  [0,72, 0,91]); held2 của clean vẫn yếu nhất trong 3 cohort (21/30 gộp,
  thấp hơn base 22/30 — nhưng held2 là so sánh PHỤ vì adaptation).
- Chỉ pi-mono, chỉ bài hàm LeetCode-style Python assert; không khái quát sang
  harness khác hay kiểu bài khác. Hai lượt không hoán đổi được với thời gian
  chạy (time confound, DESIGN §6) — ghi rõ, không tránh được trong ngân sách.

## Chi phí O1

| Checkpoint | Metered | Billed |
|---|---|---|
| Trước O1 | $27,1675 | $0,00 |
| Sau deploy + warmup | $27,2175 | $0,00 |
| Sau clean 45 ô + 4 rerun INFRA | $28,2875 | $0,00 |
| Sau đánh giá (90 ô) | $28,6675 | $0,00 |
| Sau khi dừng app | $28,6975 | $0,00 |

- **Tổng O1: +$1,53 metered** (dự toán $1,77 cho 135 ô; rẻ hơn nhờ cắt 45 ô
  realtool). Billed **$0,00** ở mọi checkpoint — sàn không bị vi phạm.
- Chương trình đến nay: $28,6975 − $24,7886 = **$3,91/$6,00**; còn **$2,09**
  cho O5 (dự toán $0,55) — đủ rộng.
- App `helix-vllm-engine` đã dừng (17:16 UTC); `modal app list` = 3 app
  stopped, **0 task**; endpoint trả "modal-http: invalid function call"
  (đúng kỳ vọng). Upstream git clean (HEAD b5adffa); fork không đổi
  (94 D + 2 ??). KHÔNG commit/push ở đâu. KHÔNG động deck/báo cáo/Drive/GitHub/Canva.
