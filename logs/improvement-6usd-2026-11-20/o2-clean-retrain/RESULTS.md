# RESULTS — O2: Adapter fix SẠCH (lcb_* only) đánh giá trên 45 bài chưa thấy (pi-mono, 20/11/2026)

Thiết kế đăng ký trước: DESIGN.md trong thư mục này (§5).
135 ô (3 nhánh × 45 bài), 1 lượt/ô, max-steps 12, timeout 600s, chấm ngoài
bằng test suite. verify_scoring.py: checked=135, mismatches=0.
Số liệu chi tiết: summary.json; bảng đọc được: summary.md.

**CẢNH BÁO Ô NHIỄM — áp dụng cho mọi bảng dưới đây:** các ô held2 của
`realtool` là Ô NHIỄM (adapter cũ train trên 16 SFT + 4 DPO thuộc held2).
Không dùng số held2 của nhánh cũ để kết luận gì. So sánh mới-vs-cũ chỉ
đọc trên held3+held4 (30 bài), dạng mô tả.

## Phán quyết chính (30 bài thực sự chưa thấy: held3+held4)

| Tiêu chí | clean | base | Ngưỡng | Kết quả |
|---|---|---|---|---|
| C1 — text-only (hành vi) | **0/30** | 4/30 | ≤ 1/30 | **ĐẠT** |
| C2 — Pass@1 (kết quả) | **24/30** | 21/30 | ≥ base | **ĐẠT (+3)** |

- McNemar base vs clean trên 30 bài (KHÁM PHÁ, p<0,05 KHÔNG yêu cầu):
  30 cặp, gains 5, losses 2, same_pass 19, same_fail 4, **p = 0.4531**
  (không có ý nghĩa thống kê — đúng như DESIGN §5.1 đã dự báo với n=30).
- **Phán quyết: C1+C2 ĐẠT — "fix sạch khái quát hóa: hành vi đã sửa trên
  bài chưa thấy, không thua base"** (n=30, 1 lượt/ô).
- Clean KHÔNG hơn base ≥ 4 bài (+3), nên không ghi "lần đầu có thắng
  sạch trên held-out".

## Bảng đủ 45 bài (3 nhánh)

| model | Pass@1 /45 | Wilson 95% | text-only /45 | INFRA |
|---|---|---|---|---|
| base (Qwen2.5-Coder-7B-Instruct) | 33/45 | [0.5896, 0.8404] | 5/45 | 0 |
| **clean (helix-lora-clean, mới)** | **34/45** | [0.6133, 0.8576] | **0/45** | 0 |
| realtool (helix-lora-realtool, cũ) | 35/45 | [0.6373, 0.8746] | 0/45 | 0 |

## Tách theo cohort (mỗi cohort 15 bài)

| model | held2 Pass@1 | held2 text-only | held3 Pass@1 | held3 text-only | held4 Pass@1 | held4 text-only |
|---|---|---|---|---|---|---|
| base | 12/15 | 1/15 | 10/15 | 3/15 | 11/15 | 1/15 |
| clean | 10/15 | 0/15 | 11/15 | 0/15 | 13/15 | 0/15 |
| realtool | 12/15 [Ô NHIỄM] | 0/15 [Ô NHIỄM] | 11/15 | 0/15 | 12/15 | 0/15 |

Wilson 95% theo cohort (xem summary.json): clean held2 [0.4171, 0.8482],
held3 [0.4805, 0.8910], held4 [0.6212, 0.9626]; base held3+held4
[0.5212, 0.8334]; clean held3+held4 [0.6269, 0.9049].

## Các phép thử paired (McNemar exact, 2 phía)

| So sánh | Cặp | gains | losses | same_pass | same_fail | p |
|---|---|---|---|---|---|---|
| base vs clean — CHÍNH (held3+held4, 30) | 30 | 5 | 2 | 19 | 4 | 0.4531 |
| base vs clean — đủ 45 (mô tả) | 45 | 6 | 5 | 28 | 6 | 1.0 |
| base vs realtool — đủ 45 (mô tả; held2 realtool Ô NHIỄM) | 45 | 7 | 5 | 28 | 5 | 0.7744 |
| realtool vs clean — held3+held4, 30 (mô tả) | 30 | 1 | 0 | 23 | 6 | 1.0 |
| base vs clean — held2 | 15 | 1 | 3 | 9 | 2 | 0.625 |
| base vs clean — held3 | 15 | 2 | 1 | 9 | 3 | 1.0 |
| base vs clean — held4 | 15 | 3 | 1 | 10 | 1 | 0.625 |

(gains = FAIL → PASS theo hướng model_b so với model_a; xem summary.json
để biết chiều của từng phép thử.)

## Đọc kết quả — điểm tốt hơn / điểm đạt được

- **Hành vi chuyển sạch:** clean text-only 0/30 trên bài chưa thấy (base
  4/30) và 0/45 toàn bộ — adapter train chỉ từ 20 bài train vẫn sửa được
  hành vi dùng tool, không phải ghi nhớ từng bài. Đây chính là câu hỏi
  của thí nghiệm (mắt xích yếu W1) và đáp án là CÓ.
- **Không thua base về kết quả:** clean 24/30 vs base 21/30 trên bài chưa
  thấy (+3); toàn bộ 45 bài clean 34/45 vs base 33/45.
- **Ngang adapter cũ trên bài chưa thấy:** clean 24/30 vs realtool 23/30
  (paired gains 1, losses 0, p=1.0) — adapter sạch (24 SFT + 5 DPO) đạt
  ngang adapter cũ (40 SFT + 9 DPO) trên tập held-out thật, dù train ít
  hơn gần một nửa.
- Clean viết file ở 43/45 ô (base 40/45, realtool 45/45); mọi ô clean
  đều gọi ≥1 tool.

## Giới hạn / điểm chưa đạt (báo cáo nguyên trạng)

- **+3 bài không có ý nghĩa thống kê** (p=0.4531, n=30, CI chồng lấn
  rộng): chỉ được nói "không thua base", không được nói "hơn base".
  Đây là giới hạn đã đăng ký trước trong DESIGN §5.1.
- **1 lượt/ô:** phương sai chưa đo — đó là việc của O1 (lặp lại sau O2).
- **held2 của clean yếu hơn base** (10/15 vs 12/15, paired gains 1 /
  losses 3): held2 là so sánh PHỤ (adaptation — held2 đã định hình thiết
  kế fix), nhưng ghi rõ ở đây, không giấu. Trên 2 cohort chính (held3,
  held4) clean đều hơn base (11 vs 10; 13 vs 11).
- Base tự trôi giữa các đợt chạy là hiện tượng đã biết; mọi so sánh trên
  đây đều trong cùng đợt chạy này — KHÔNG so số clean với số base của
  đợt cũ (23/30 gộp).
- Chỉ pi-mono, chỉ bài hàm LeetCode-style Python assert; không khái quát
  sang harness khác hay kiểu bài khác.

## Chi phí O2

Metered $24.7886 → $26.7575 (sau eval), **+$1.9690**, billed **$0.00**.
Train +$0.0773; deploy + warmup + eval 135 ô + 3 rerun INFRA +$1.8916.
Ngân sách chương trình còn $4.03 cho O3 + O1 + O5 (dự toán $2.28).
