# KỊCH BẢN RÚT GỌN — HELIX, NỬA SAU — BẢN NHÁP v3 (deck 37 slide, ~8 phút)

**Mục đích:** đưa nửa sau về đúng ~8 phút sau khi chèn lời thoại slide 35 mới.
Bản v2 đúng 8:00 cho deck 36 slide; thêm slide 35 (~45–50 giây) thì thành
~8:45. Bản v3 này cắt ~50 giây ở ba chỗ dưới đây để về lại ~7:50–8:00.

**Trạng thái — ĐỌC TRƯỚC KHI DÙNG:**
- Đây là BẢN NHÁP v3, chưa phải bản chính thức. Nó chỉ thay đổi 3 mục so với
  v2 (`kich-ban-helix-nua-sau-8-phut-DRAFT-v2.md`); mọi mục khác giữ nguyên
  lời thoại v2. Deck PPTX, kịch bản docx gốc và báo cáo văn bản **không đụng
  tới**. File lời thoại slide 35 riêng
  (`loi-thoai-slide-35-dong-gop-gioi-han.md`) cũng không đụng tới — v3 chỉ
  chèn nó vào đúng vị trí.
- Giả định vẫn như v2: Triệu nói nửa sau (slide 19–37 deck mới), Việt nói nửa
  đầu (1–18). Nếu Việt nhận nửa sau thì đổi người đọc, nội dung giữ nguyên.
  Chưa có xác nhận ai nói nửa nào.
- Số liệu vẫn là số vòng 2 cuối cùng, đã kiểm chứng: BUILD2 60/80 →
  REBUILD2 66/80 (McNemar p = 0,07), held-out v2 50/60 → 53/60 (p = 0,45),
  train 19 SFT + 6 DPO (SFT 9 bước 1,00 → 0,49; DPO 3 bước 0,693 → 0,660).
- Thời lượng là ước tính theo v2 (khoảng 150 từ/phút khi đọc chậm, rõ).
  Cần tập đọc một lượt để chốt giờ thật trước buổi thuyết trình.

## Bảng giờ (deck 37 slide)

| Đoạn | V2 | V3 | Đổi |
|---|---|---|---|
| Slide 19–21 | 60 giây | 60 giây | giữ nguyên |
| Slide 22 — BUILD2 vs REBUILD2 | 55 giây | ~30 giây | **cắt ~25 giây**: bỏ đọc từng hàng Minimal/Pi/Hermes/OpenCode, chỉ giữ tổng + chiều lật + p = 0,07 |
| Slide 23–25 | 60 giây | 60 giây | giữ nguyên |
| Slide 26 — Train LoRA vòng 2 | 45 giây | ~25 giây | **cắt ~20 giây**: bỏ chi tiết cấu hình (rank 16, alpha 32, dropout 0,05, backup adapter), chỉ giữ dữ liệu + loss + mục đích |
| Held-out v2 (slide mới, deck: slide 25) | 30 giây | 30 giây | giữ nguyên — đọc sau slide 26 như v2, dù trong deck nó nằm ở slide 25 |
| Slide 27 — Dashboard Modal | 15 giây | 0 giây | **bỏ lời thoại**: chỉ chiếu ảnh, không nói — ảnh đã cũ, app đã dừng sau vòng 2 |
| Slide 28–34 | 155 giây | 155 giây | giữ nguyên |
| **Slide 35 (mới) — Đóng góp & giới hạn** | — | **~45–50 giây** | **thêm**: đọc nguyên văn file `loi-thoai-slide-35-dong-gop-gioi-han.md` |
| Slide 36 (v2: slide 35) — Hạn chế & lưu ý | 45 giây | 45 giây | giữ nguyên |
| Slide 37 (v2: slide 36) — Kết thúc | 20 giây | 20 giây | giữ nguyên |
| **Tổng** | **~8:00 + 0:48 = ~8:48** | **~7:50–8:00** | **cắt ~50 giây** |

## Đổi 1 — Slide 22, bản rút gọn (~30 giây, đọc nguyên văn)

> Đây là bảng kết quả trung tâm, trên cùng 20 bài: model gốc 60 trên 80,
> model gắn LoRA vòng 2 lên 66 trên 80 — tăng ròng 6 trace: 7 bài lật từ
> trượt thành đậu, chỉ 1 bài lật ngược lại. Nhóm em nói thẳng: kiểm định
> McNemar cho p bằng 0,07 — chưa đạt mức ý nghĩa 0,05, nên mức tăng này gợi
> ý chứ chưa chứng minh được học thật.

*▸ Đã bỏ: từng hàng Minimal 14→17, Pi Mono 15→16, Hermes 14→15, OpenCode
17→18 và câu về bài lật ngược lcb_009. Số tổng và p = 0,07 vẫn đủ để trả lời
câu hỏi "tăng 6 có nghĩa gì?". Nếu thầy hỏi sâu từng harness thì trả lời
bằng bảng trên slide, không cần đọc trước.*

## Đổi 2 — Slide 26, bản rút gọn (~25 giây, đọc nguyên văn)

> Chi tiết lần train vòng 2: dữ liệu toàn bộ là live — 19 mẫu SFT và 6 cặp
> DPO, trích từ 20 bài train; lượt sampling nhiệt độ 0,7 tạo được cặp đối
> lập cho 4 bài. Train 9 bước SFT, loss từ 1,00 xuống 0,49; 3 bước DPO, loss
> từ 0,693 xuống 0,660. Mục đích là kiểm chứng vòng lặp khép kín được với
> provenance đầy đủ, chứ chưa nhằm tối đa hóa điểm số.

*▸ Đã bỏ: model gốc Qwen2.5-Coder-7B-Instruct, nạp 4-bit, Unsloth + PEFT,
LoRA rank 16, alpha 32, dropout 0,05, và câu backup adapter vòng 1. Các chi
tiết này vẫn nằm trên slide và trong báo cáo nếu thầy hỏi.*

## Đổi 3 — Slide 27: không đọc, chỉ chiếu ảnh

Slide dashboard Modal đã cũ (credit trên ảnh là số cũ, app đã dừng sau vòng
2, chi phí vòng 2 khoảng 4,3 đô trong hạn 8 đô). Chuyển slide, dừng 1–2 giây
cho người nghe nhìn ảnh, rồi sang slide 28 luôn, không nói gì thêm.

## Chèn — Slide 35 (mới): đọc nguyên văn file lời thoại slide 35

Chèn giữa mục "Slide 34" và mục "Slide 36 — Hạn chế & lưu ý" (đánh số theo
deck 37 slide). Đọc nguyên văn ~45–50 giây trong file
`loi-thoai-slide-35-dong-gop-gioi-han.md` — phần nào của tác giả, phần nào
của nhóm, giới hạn nói ở mức liệt kê, chi tiết để slide 36 nói sau.

## Đánh số lại khi tập với deck 37 slide

- Mục "Slide 35 — Hạn chế & lưu ý" trong v2 thực ra là **slide 36**.
- Mục "Slide 36 — Kết thúc" trong v2 thực ra là **slide 37**.
- Lời thoại hai mục đó giữ nguyên, chỉ đổi số slide khi đọc mục lục.
