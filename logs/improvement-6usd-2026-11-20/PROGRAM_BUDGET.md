# SỔ NGÂN SÁCH — Chương trình cải thiện HELIX $6 (O2 + O3 + O1 + O5, O6 offline $0)

Ngày viết: 2026-11-20. Trạng thái: **chỉ kế hoạch — chưa chạy GPU nào**.
Tài khoản Modal $30: metered $24,79, credits −$23,97, billed $0,00
(xác minh 18/11; ~$6,03 credit còn lại). **Trần chương trình: $6,00 metered.
Billed phải = $0,00 ở mọi lần kiểm tra.**

## 1. Tỉ lệ chi phí dùng để dự toán (đã hiệu chuẩn từ các lần chạy thật)

| Hạng mục | Tỉ lệ dự toán | Căn cứ (đã đo) |
|---|---|---|
| Train LoRA nhỏ (SFT+DPO) | $0,20 / lần | Fix train +$0,108; ablation SFT-only train +$0,209 — lấy mức cao |
| Lượt chạy pi-mono (eval) | $0,012 / lượt | Ablation 105 lượt +$0,98 ≈ $0,0093; gen pi-mono 45 lượt +$0,50 ≈ $0,0111 |
| Lượt chạy blend qua runner.mts (O3) | $0,007 / lượt | Bước 6: 90 lượt + 1 deploy = +$0,63–0,64 |
| Lượt chạy v6 pi-mono (O5) | $0,007 / lượt | Bước 5: 32 lượt + 1 deploy = +$0,22 ≈ $0,0069 |
| Deploy phục vụ dùng chung (1 lần) | $0,15 | Slack cho deploy + warmup (các lần trước deploy gần như $0; lấy $0,15 cho chắc) |
| Rerun INFRA (1 ô) | ~$0,01 / ô | Cùng tỉ lệ lượt chạy |

Trường hợp bi quan cho pi-mono: fix pi-mono +$1,23/70 lượt ≈ $0,0176/lượt
(có thể gồm deploy + billing lag). Xem §3 — nếu tỉ lệ thực tế chạm mức này
thì quy tắc cắt giảm O1 kích hoạt, chương trình vẫn trong trần.

## 2. Sổ chi tiết (thứ tự chạy: O2 train → deploy chung → O2 eval → O3 → O1 → O5 → dừng)

| # | Hạng mục | Số lượng | Đơn giá | Chi phí |
|---|---|---|---|---|
| — | Deploy phục vụ dùng chung (base + realtool + clean) | 1 lần | — | $0,15 |
| O2 | Train adapter `helix-lora-clean` (24 SFT + 5 DPO) | 1 lần | — | $0,20 |
| O2 | Đánh giá pi-mono, 3 nhánh × 45 bài | 135 lượt | $0,012 | $1,62 |
| O3 | Can thiệp prompt opencode, 3 nhánh × 10 bài | 30 lượt | $0,007 | $0,21 |
| O1 | Lặp lại toàn bộ 135 ô của O2, 1 lần | 135 lượt | $0,012 | $1,62 |
| O5 | Thăm dò v6, 2 biến thể × 2 nhánh × 16 fixture | 64 lượt | $0,007 | $0,45 |
| | **TỔNG DỰ TOÁN** | **364 lượt + 1 train** | | **$4,25** |
| | **Đệm còn lại (trần $6,00 − dự toán)** | | | **$1,75 (29%)** |

- Tổng số lượt harness thật sau chương trình: 1.262 + 364 = **1.626 lượt**
  (+ rerun INFRA nếu có — tính lại từ log lúc đồng bộ deck, O6).
- Trần mỗi bước $8 (quy tắc đứng) — trần chương trình $6,00 chặt hơn, lấy $6,00.
- Đệm $1,75 bao được ~100 rerun INFRA (tỉ lệ INFRA quan sát: bước 1 có
  4 rerun/345 lượt; các bước khác 0–1) + sai số billing lag (±$0,01–0,05
  mỗi lần đọc, đã thấy ở bước 5–6).

## 3. Trường hợp bi quan + quy tắc cắt giảm (đăng ký trước)

Nếu tỉ lệ pi-mono thực tế là $0,0176/lượt (mức fix): O2+O1 = 270 lượt ×
$0,0176 = $4,75 → tổng chương trình ≈ $5,76, đệm chỉ còn $0,24.
Khi đó kích hoạt cắt giảm O1 theo thứ tự đã đăng ký trong O1/DESIGN.md §5
(cắt nhánh cũ 45 lượt trước → cắt cohort held2 30 lượt → tối thiểu 60 ô
so sánh chính). Cắt giảm CHỈ theo billing (checkpoint §4), không theo kết
quả — và ghi vào RUN_LOG.md kèm số billing tại thời điểm quyết định.
O2, O3, O5 không bị cắt (chúng là lõi của chương trình); O6 offline $0
không bị ảnh hưởng bởi ngân sách GPU.

## 4. Checkpoint billing + quy tắc dừng (tuyệt đối, không ngoại lệ)

- **Điều kiện tiên quyết:** token Modal đã hết hạn (19/11 10:25 +07, xác
  minh 20/11 20:11). CHỈ bắt đầu GPU sau khi Triệu cấp lại quyền trong
  trình duyệt của mình (`modal token new`, Triệu duyệt). Nếu auth lỗi:
  DỪNG GPU ngay, làm phần offline (O6), báo cáo.
- Snapshot `modal billing summary --json` tại mỗi checkpoint, lưu file:
  (1) trước train O2; (2) sau train O2; (3) sau deploy; (4) sau O2 eval;
  (5) sau O3; (6) sau O1; (7) sau O5; (8) sau khi dừng app; (9) delayed
  (billing có lag — đã thấy ±$0,01 ở bước 5–6).
- **Quy tắc sàn:** nếu `billed_cost` > $0,00 ở BẤT KỲ lần kiểm tra nào →
  DỪNG toàn bộ GPU ngay lập tức, dừng app, xác minh 0 task, báo cáo.
- **Quy tắc dự báo:** sau mỗi bước, nếu (metered hiện tại + chi phí ước
  tính phần còn lại theo tỉ lệ quan sát được × 1,2) > $6,00 thì dừng sau
  bước hiện tại, dừng app, báo cáo phần đã xong (không vay ngân sách).
- Trước khi deploy: `modal app list`; chỉ deploy khi 0 task đang chạy;
  KHÔNG BAO GIỜ dừng app của người khác. Sau mỗi bước: dừng app + TỰ kiểm
  tra `modal app list` = 0 task (không tin lời subagent — đã có lần báo sai).
- Upstream git-clean (HEAD b5adffa) kiểm tra trước deploy đầu và sau GPU
  cuối; fork ghi trạng thái trước/sau (kỳ vọng không đổi: 94 D + 2 ??).
  KHÔNG commit/push ở đâu. KHÔNG sửa slide/Drive/GitHub/Canva trong
  chương trình GPU (đồng bộ deck là O6, làm SAU, offline).

## 5. Những gì KHÔNG nằm trong ngân sách này (không được lấy tiền từ đây)

- O6 đồng bộ deck: $0 offline — làm sau chương trình GPU.
- Vòng 3 / model lớn hơn / benchmark 6.500 lượt của tác giả / thêm cặp DPO
  không có giả thuyết: KHÔNG khuyến nghị (AUDIT.md §C2) — không cấp ngân sách.
- Slide P8 (LIÊN HỆ): đã duyệt, thực hiện riêng, không tốn GPU.
- Mọi chi phí phát sinh ngoài 4 bước O2/O3/O1/O5 đều cần Triệu duyệt riêng.

## 6. CHI PHÍ THỰC TẾ (khóa sổ 20/11/2026 ~01:10 +07, kiểm chứng bởi coordinator)

- Baseline trước chương trình: metered $24,78857824, billed $0,00.
- O2 (135 lượt + train sạch): +$1,96 → $26,7475.
- O3 (30 lượt): +$0,46 → $27,1675 (kế hoạch $0,31; +$0,15 do 1 ô timeout + app idle).
- O1 (90 lượt, nhánh cũ cắt theo luật billing §5): +$1,53 → $28,7675.
- O5 (64 lượt): +$0,63 → $29,3075 (kế hoạch $0,55; +$0,08 do V1 chạy nhiều bước).
- **Tổng chương trình: +$4,51 (metered cuối $29,2975 — điều chỉnh −$0,01 sau O5), billed $0,00 suốt chương trình; còn dư $1,49/$6,00, không dùng.**
- Quy tắc sàn không lần nào kích hoạt (billed luôn $0,00). Sau GPU cuối: `modal app list` = 0 task (kiểm chứng bởi coordinator).
- O6 đồng bộ deck: $0 offline, hoàn thành 20/11/2026 (deck v2 → 22 slide).
