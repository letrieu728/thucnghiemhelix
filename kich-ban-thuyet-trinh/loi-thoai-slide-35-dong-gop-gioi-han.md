# Lời thoại chèn thêm — Slide 35 (deck 37 slide): Đóng góp & giới hạn

**File này để làm gì:** bản deck 37 slide gửi Đặng Anh Thư
(`Bao_cao_HELIX-v2-so-lieu-vong2-cong-hien-gioi-han-KPDL.pptx`) có slide 35 mới
"Đóng góp & giới hạn", nhưng kịch bản nửa sau v2 viết theo deck 36 slide nên
chưa có lời thoại cho slide này. File này chỉ là lời thoại chèn thêm — không
sửa kịch bản gốc hay deck.

**Đã kiểm chứng (14/11, đọc text trực tiếp từ file KPDL):** slide 35 có đúng
3 khối — "Dùng mã gốc của tác giả" (fork HKUDS/HELIX, 0 dòng code upstream bị
sửa; Helix Builder/CLI, recipe, atoms/ports; ý tưởng co-evolution và
sibling-record từ paper), "Nhóm tự xây" (pipeline closed-loop script 01–04 +
test; 4 harness MÔ PHỎNG bằng prompt, không phải harness lắp thật; 35 bài tự
viết: 20 train + 15 held-out v2; trích sibling + train LoRA, tác giả không
train), "Giới hạn" (520 trace vs 6.500 lượt của paper; 25 record train vs 438;
p = 0,0703; held-out p = 0,4531; smoke test ghép harness thật chưa thành công
— proxy streaming, tool call XML; chưa dùng LiveCodeBench thật). Mọi số dưới
đây lấy đúng từ slide, không thêm số mới.

## Đọc nguyên văn (~45–50 giây, khoảng 125 từ)

> Slide này trả lời: phần nào là của tác giả, phần nào là của nhóm em.
>
> Của tác giả: fork HKUDS/HELIX nguyên vẹn, không sửa một dòng code upstream —
> Helix Builder, recipe, atoms và ports, cùng ý tưởng co-evolution và
> sibling-record, đều từ paper.
>
> Nhóm em tự xây pipeline closed-loop — bốn script cộng test — bốn harness mô
> phỏng bằng prompt, chưa phải harness lắp thật; 35 bài tự viết, 20 train và
> 15 held-out mới; và việc trích sibling rồi train LoRA, điều tác giả không làm.
>
> Giới hạn, nói thẳng: mẫu nhỏ — 520 trace so với 6.500 lượt của paper, 25
> record train so với 438; mức tăng chưa có ý nghĩa thống kê, p bằng 0,07 và
> 0,45; smoke test ghép harness thật vẫn chưa thành công. Chi tiết em nói rõ ở
> slide sau.

## Lưu ý khi đọc

- **Đừng đọc lại chi tiết giới hạn ở đây:** slide 36 (Hạn chế & lưu ý) đã có
  lời thoại sẵn trong kịch bản v2 (mục "Slide 35 — Hạn chế & lưu ý", 45 giây)
  và đi sâu hơn (12 bước train, 101 symlink, 3 artifact FAIL). Ở slide 35 chỉ
  nêu giới hạn ở mức liệt kê, rồi chuyển sang slide 36.
- **Giọng:** chậm, thẳng thắn — đây là slide thầy thường đánh giá cao nếu
  trình bày trung thực, giống tinh thần của slide 36.

## Đánh số lại khi dùng với deck 37 slide

Kịch bản v2 viết theo deck 36 slide, nên khi trình bày deck 37 slide:

- Mục "Slide 35 — Hạn chế & lưu ý" trong kịch bản v2 thực ra là **slide 36**
  của deck 37 slide.
- Mục "Slide 36 — Kết thúc" trong kịch bản v2 thực ra là **slide 37**.
- Lời thoại trên đây chèn vào giữa hai mục đó.

## Ảnh hưởng tới thời lượng

Kịch bản nửa sau v2 đang đúng 8 phút 00 giây (480 giây) cho deck cũ. Thêm
~45–50 giây này thì nửa sau thành khoảng **8 phút 45 giây**, vượt suất ~8
phút/người. Muốn giữ đúng 8 phút thì cắt chừng đó ở chỗ khác — gợi ý dễ cắt
nhất là slide 22 (55 giây, bảng BUILD2 vs REBUILD2) hoặc slide 26 (45 giây,
chi tiết train LoRA): bỏ 1–2 câu chi tiết, giữ lại số headline. Chưa cắt hộ
vì còn chờ Triệu + Việt chốt ai nói nửa nào.
