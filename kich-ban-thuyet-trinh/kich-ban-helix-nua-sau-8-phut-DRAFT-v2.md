# KỊCH BẢN RÚT GỌN — HELIX, NỬA SAU (slide 19–36) — BẢN NHÁP v2 (số vòng 2)

**Mục đích:** bản rút gọn ~8 phút cho người trình bày nửa sau, để vừa suất 20–25 phút/nhóm
đã gồm hỏi đáp (mỗi người ~8 phút). Kịch bản gốc nửa sau dài ~13,4 phút (805 giây);
bản này ~8 phút 00 giây (480 giây).

**Trạng thái — ĐỌC TRƯỚC KHI DÙNG:**
- Đây là BẢN NHÁP v2, chưa phải bản chính thức. Nó **thay thế bản nháp v1** (số vòng 1:
  BUILD 28/40, REBUILD 31/40) — vòng 2 đã xong và Triệu chốt **không làm vòng 3**, nên
  số dưới đây là số cuối để trình bày.
- Mọi con số dưới đây là **số vòng 2 cuối cùng, đã kiểm chứng** (nguồn:
  `~/workspace/helix-slide-kit/06_Dung-rieng-cho-slide/bang-so-lieu-cho-slide.md`
  và `claim-va-caveat.md`; repo thucnghiemhelix, commit vòng 2 `ffb49ab`):
  360 trace live, BUILD2 60/80 → REBUILD2 66/80, held-out v2 base 50/60 → LoRA 53/60,
  train 19 SFT + 6 DPO (SFT 9 bước 1,00 → 0,49; DPO 3 bước 0,693 → 0,660).
  Các con số cũ (Minimal 30% → 60%, gap 60% → 10%, 9 SFT / 8 DPO) đã bị thu hồi —
  KHÔNG dùng nữa.
- Deck PPTX, kịch bản gốc (`kich-ban-thuyet-trinh-helix.docx`) và báo cáo văn bản
  **vẫn giữ số liệu cũ — chưa sửa**. Bản này chỉ là kịch bản nói; muốn gửi slide cho
  thầy thì phải sửa deck theo bảng số liệu ở slide-kit trước.
- **MỚI (Canvas, tối 12/11):** lớp quay lại thứ tự thuyết trình theo đăng ký ban đầu,
  và các nhóm phải **gửi slide cho Đặng Anh Thư trước buổi thuyết trình 2 ngày** để
  chuyển thầy góp ý. Ngày thuyết trình của nhóm 5 vẫn chưa chốt — kiểm tra file đăng ký
  đính kèm mail Canvas để tính hạn gửi slide, rồi chốt bản này trước hạn đó.
- Còn cần Triệu + Việt chốt ai nói nửa nào. Bản này viết cho nửa sau (19–36) vì đó
  là phần việc của chính nhóm, Triệu nắm chắc nhất — nếu Việt nhận nửa sau thì
  đổi người đọc, nội dung giữ nguyên.
- Slide mới nên chèn sau slide 26: **held-out v2** (base 50/60 → LoRA 53/60) — xem mục
  "Slide mới" dưới đây. Deck hiện chưa có slide này.
- Slide 27 (ảnh dashboard Modal) đã lỗi thời: credit và trạng thái app trên ảnh là
  số cũ; app đã dừng sau vòng 2. Nên thay ảnh mới hoặc bỏ slide này khi sửa deck.

## Cách đọc

Đọc gần như nguyên văn. Số trong ngoặc là thời lượng gợi ý từng slide.
Tổng: 480 giây ≈ 8 phút 00 giây.

---

### Slide 19 — Mục 4 — Thực nghiệm của nhóm (~10 giây)

Đến mục bốn — phần thực nghiệm của nhóm em. Nhóm em làm hai việc: khép kín vòng lặp
mà tác giả để dở, bằng cách train LoRA thật và đánh giá rebuild; và chạy lại phần
lắp ghép harness bằng Helix Builder cùng lệnh CLI tương ứng.

*▸ Slide ngăn cách mục nhưng có nội dung — đọc cả hai việc nhóm đã làm.*

### Slide 20 — Tổng quan về mã nguồn (~25 giây)

Nhóm em đặt mục tiêu thực tế: tái lập các kiểm tra offline, miễn phí và chạy lại
được của HELIX — và không tuyên bố tái lập các benchmark phải dùng LLM trả phí.
Repo thực nghiệm là github.com/letrieu728/thucnghiemhelix, chạy verify ở chế độ
chỉ đọc. Song song, nhóm chạy trọn vòng closed-loop trên bản fork, hai vòng:
vòng 1 trên 10 bài, vòng 2 mở rộng lên 20 bài train và 15 bài held-out mới —
tổng cộng 360 trace live ở vòng 2, không còn lỗi hạ tầng nào.

*▸ Nói thẳng giới hạn phạm vi ngay từ đầu giúp phần hỏi đáp dễ hơn.*

### Slide 21 — Pipeline closed-loop (~25 giây)

Pipeline gồm năm thành phần. File 01 dựng server vLLM trên Modal, hỗ trợ
multi-LoRA. File 02 chạy đánh giá 20 bài LiveCodeBench tự viết nhân 4 harness.
File 03 trích các cặp SFT và DPO từ các quỹ đạo chị em — chỉ lấy trace live, có ghi
provenance, và ở vòng 2 có thêm lượt sampling nhiệt độ 0,7 để tạo cặp đối lập.
File 04 train LoRA bằng Unsloth và TRL trên GPU A100. Và notebook
evaluate_rebuild so sánh BUILD với REBUILD và vẽ biểu đồ.

*▸ Đọc tên file chậm vừa phải — đây là bằng chứng pipeline có thật.*

### Slide 22 — Kết quả trung tâm: BUILD2 vs REBUILD2 (~55 giây)

Đây là bảng kết quả trung tâm, trên cùng 20 bài, model gốc so với model gắn LoRA
vòng 2. Minimal tăng từ 14 lên 17 trên 20 bài. Pi Mono từ 15 lên 16. Hermes giữ
nguyên đà tăng nhẹ, từ 14 lên 15. OpenCode từ 17 lên 18. Tổng cộng 60 trên 80
lên 66 trên 80 — tăng ròng 6 trace: 7 bài lật từ trượt thành đậu, chỉ 1 bài lật
ngược lại. Nhóm em nói thẳng: kiểm định McNemar cho p bằng 0,07 — chưa đạt mức
ý nghĩa 0,05, nên mức tăng này gợi ý chứ chưa chứng minh được học thật — và sẽ
nói rõ vì sao ở slide thống kê sau.

*▸ Đọc bảng theo hàng. Không giấu chiều lật ngược (lcb_009, OpenCode — lại là bài
có trong dữ liệu DPO).*

### Slide 23 — Harness Gap và hợp tập (~30 giây)

Về khoảng cách harness: trung bình 3 harness nâng cao trừ Minimal là 6,7 điểm
phần trăm ở BUILD2, xuống âm 3,3 điểm ở REBUILD2 — tức ở vòng rebuild, Minimal
vượt trung bình các harness phức tạp, gap đóng lại và đảo chiều. Nhưng cỡ mẫu
chỉ 20 bài, một bài đã là 5 điểm phần trăm, nên đừng đọc quá sâu vào dấu âm này.
Câu chuyện cũ "gap thu hẹp từ 60% xuống 10%" là sai — nó xuất phát từ baseline
BUILD cũ bị trộn trace mock — nhóm em đã thu hồi. Hợp tập kiểu paper (ít nhất
một harness giải được): 17 trên 20 bài ở BUILD2, lên 19 trên 20 ở REBUILD2 —
con số mô tả, không phải bằng chứng học được.

*▸ Câu thu hồi là bắt buộc phải nói — đừng bỏ qua.*

### Slide 24 — Số bước và độ trễ (~20 giây)

Số bước gần như không đổi: Minimal giữ 1,0 bước cả hai vòng; Pi Mono giảm nhẹ
từ 1,75 xuống 1,60; Hermes từ 1,90 xuống 1,75; OpenCode từ 1,50 xuống 1,30.
Độ trễ cũng không cải thiện một cách hệ thống — Minimal nhanh hơn, từ 17,9 giây
xuống 13,5 giây, nhưng Pi Mono lại chậm hơn, từ 42,1 lên 48,1 giây. Nhóm em
không kể đây là cải thiện: mô hình và harness chỉ hợp nhau hơn ở vài bài, không
phải nhanh hơn một cách hệ thống.

*▸ Kết bằng câu về "cặp model–harness" — quay lại luận điểm của bài báo.*

### Slide 25 — Harness Gap, nhắc lại một dòng (~10 giây)

Slide này chỉ tách riêng chỉ số gap vừa nói: 6,7 điểm phần trăm xuống âm 3,3
điểm phần trăm theo cách tính trung bình của báo cáo. Cả hai cách đều cho cùng
kết luận: gap đóng lại sau vòng distill thứ hai, nhưng cỡ mẫu nhỏ nên chưa kết
luận được.

*▸ Slide này trùng nội dung slide 23 — khi sửa deck nên gộp hai slide làm một,
lấy chỗ chèn slide held-out v2.*

### Slide 26 — Train LoRA vòng 2 (~45 giây)

Chi tiết lần train vòng 2: mô hình gốc Qwen2.5-Coder-7B-Instruct, nạp 4-bit,
Unsloth kết hợp PEFT, LoRA rank 16, alpha 32, dropout 0,05. Dữ liệu train toàn
bộ là live: 19 mẫu SFT và 6 cặp DPO, trích từ 20 bài train — lượt sampling
nhiệt độ 0,7 tạo được cặp đối lập cho 4 bài mà lượt chuẩn không tạo được. Train
9 bước SFT, loss từ 1,00 xuống 0,49 — lần này loss giảm rõ, không còn phẳng như
vòng 1; 3 bước DPO, loss từ 0,693 xuống 0,660. Adapter vòng 1 đã được backup
trước khi ghi đè. Mục đích của lần train này là kiểm chứng vòng lặp khép kín
được với provenance đầy đủ, chứ chưa nhằm tối đa hóa điểm số.

*▸ Nhấn mục đích: kiểm chứng vòng lặp khép kín, không phải tối đa hóa điểm.*

### Slide mới — Held-out v2: bài mới chưa từng thấy (~30 giây)

*(Chèn sau slide 26 — deck hiện chưa có slide này.)*

Đây là thước đo đáng tin nhất của nhóm em: 15 bài hoàn toàn mới, chưa từng thấy
trong lúc học, kiểm tra rò rỉ sạch. Model gốc đạt 50 trên 60, model gắn LoRA
đạt 53 trên 60 — và không tụt ở harness nào. Nhưng kiểm định McNemar cho
p bằng 0,45, nên chưa chứng minh được khái quát hóa. Bài khó nhất,
next_permutation, cả hai model đều 0 trên 4. Hợp tập kiểu paper giữ nguyên
14 trên 15 ở cả hai model. Kết luận trung thực: LoRA không làm tệ đi trên bài
mới, nhưng giỏi lên thật hay chưa thì cần quy mô lớn hơn mới trả lời được.

*▸ Slide quan trọng nhất để trả lời câu "model có giỏi lên thật không?" — đọc chậm,
nghiêm túc.*

### Slide 27 — Adapter đã serve trên Modal (~15 giây)

Ảnh này là dashboard Modal đợt đánh giá rebuild: ứng dụng helix-vllm-engine chạy
vLLM, adapter helix-lora-final được mount qua multi-LoRA để phục vụ đánh giá.
Lưu ý: ảnh chụp trước đợt chạy live, con số credit trên ảnh đã cũ — app đã dừng
hẳn sau vòng 2, chi phí vòng 2 khoảng 4,3 đô, cả hai vòng vẫn trong hạn 8 đô
nhóm đặt ra, không động tới thẻ.

*▸ Slide bằng chứng triển khai — nói ngắn. Cần thay ảnh mới khi sửa deck.*

### Slide 28 — Helix Builder — lắp ghép harness (~25 giây)

Phần cuối của thực nghiệm nhóm là Helix Builder — trang lắp ghép harness của chính
tác giả, một file dài hơn 14 nghìn dòng. Quy trình: chọn preset và slot, bấm
Validate, xuất recipe dạng JSON, rồi chạy lệnh CLI tương ứng để lắp ghép thật.
Nhóm em đã chạy lại bước lắp ghép này bằng CLI trên chính repo fork của nhóm.

*▸ Phân biệt rõ: Builder là giao diện của tác giả; phần nhóm chạy lại là CLI.*

### Slide 29 — Giao diện Helix Builder (~20 giây)

Giao diện gồm ba bước: một, Choose a base; hai, Customize; ba, Validate and
export. Sáu preset có sẵn là OpenCode, Pi Mono, Nanobot, Hermes Agent, Minimal
và Hybrid Mix. Hai ảnh chụp ở hai slide sau được chụp thật từ docs server chạy
cục bộ — mở file qua đường dẫn raw trên GitHub thì chỉ thấy mã nguồn dạng text.

*▸ Giải thích luôn vì sao phải chạy server local — tránh câu hỏi vặn.*

### Slide 30 — Ảnh chụp: giao diện Helix Builder (~10 giây)

Ảnh chụp thật giao diện Helix Builder từ docs server cục bộ: bước một, Choose a
base, với đủ sáu preset. Mỗi preset là một điểm khởi đầu để tùy biến từng slot
ở bước hai.

*▸ Slide ảnh chụp thật — chỉ vào 6 preset.*

### Slide 31 — Ảnh chụp: lắp ghép Pi Mono (~30 giây)

Ảnh này là bước hai, Customize, với preset Pi Mono. Bên trái là thư viện module;
ở giữa là harness hiện tại; cột Review bên phải báo READY — tất cả các cổng bắt
buộc đều đã có linh kiện. Chi tiết nhóm em tâm đắc nhất: mã fingerprint của
harness là f87e68defe775bb6 — khớp chính xác với fingerprint mà lệnh CLI assemble
của nhóm cho ra. Giao diện web và công cụ dòng lệnh độc lập cho cùng một dấu vân
tay: hai nguồn kiểm chứng lẫn nhau rằng cùng một recipe cho ra cùng một harness.

*▸ Đây là slide "đinh" của phần Builder — đọc chậm mã fingerprint.*

### Slide 32 — Repo fork Vietng-XPrince7/HELIX (~15 giây)

Đây là repo fork của nhóm trên GitHub, rẽ nhánh từ HKUDS/HELIX. Fork là pipeline
chính thức của nhóm; các bản sửa provenance và held-out đã chuẩn bị thành patch
v2 để Việt xem qua rồi mới merge, vì push trực tiếp bị chặn.

*▸ Không đọc lại dòng commit cũ về "80 trace" — con số đó thuộc đợt đánh giá cũ.*

### Slide 33 — Kết quả lắp ghép (~25 giây)

Kết quả lắp ghép nhóm chạy lại ngày 8 tháng 11: hai recipe đều cho kết quả OK.
Recipe pi-mono lắp được 303 atom, đủ 96 cổng, và cả 96 trên 96 cổng bắt buộc đều
đã bind. Recipe minimal lắp 176 atom, cũng trên 96 cổng, trong đó 32 trên 96 là
cổng bắt buộc đã bind — đúng với triết lý tối giản của nó.

*▸ Đọc bảng theo từng hàng. Cụm cần thuộc: pi-mono 303 atom, 96/96 cổng bắt buộc.*

### Slide 34 — Kết quả lắp ghép, chi tiết (~30 giây)

Chi tiết hơn: pi-mono gồm 303 atom, fingerprint f87e68defe775bb6 — chính là mã
trên ảnh chụp Builder ở slide 31. Minimal gồm 176 atom, fingerprint
cb3fc879b66eaf2b. Cả hai đều có summary và verification bằng true. Và nhóm em
nói rõ: đây là kiểm tra lắp ghép tĩnh theo hợp đồng — nó chứng minh recipe hợp
lệ và đủ cổng, chứ không chứng minh điểm LiveCodeBench.

*▸ Câu phân biệt "lắp ghép tĩnh ≠ benchmark" là bắt buộc.*

### Slide 35 — Hạn chế & lưu ý (~45 giây)

Nhóm em xin nêu thẳng các hạn chế. Một, mẫu đánh giá chỉ có 20 bài train và
15 bài held-out mới, chưa đủ để kết luận khái quát; McNemar cho mức tăng 60 lên
66 cho p bằng 0,07, và held-out v2 cho p bằng 0,45 — đều chưa đạt ý nghĩa thống
kê. Hai, 4 "harness" của nhóm thực chất là system prompt cộng vòng lặp chat,
chưa phải recipe đã assemble thật — nhóm đã thử ghép model đã train với harness
lắp thật trong một smoke test, nhưng kẹt ở hai lỗi kỹ thuật (proxy làm hỏng
streaming, model sinh tool call XML mà parser không nhận), nên đây vẫn là hướng
phát triển. Ba, train chỉ 12 bước trên 19 mẫu SFT và 6 cặp DPO, DPO mới nhích
nhẹ. Bốn, nhóm đã chốt không làm vòng 3, và 101 symlink fixture của tác giả vẫn
gãy nên một phần kiểm chứng cassette chưa chạy được.

*▸ Nói chậm, nghiêm túc — slide này thường được thầy đánh giá cao nếu trình bày thẳng thắn.*

### Slide 36 — Kết thúc (~20 giây)

Phần trình bày về bài báo HELIX của nhóm em xin kết thúc tại đây. Tóm lại trong
một câu: năng lực của AI agent nằm ở cả mô hình lẫn harness, và nhóm em đã tự
tay khép kín vòng lặp đó hai lần bằng dữ liệu live có provenance — train một LoRA
adapter, thấy điểm tăng từ 60 lên 66 trên 80, gap đóng lại từ 6,7 xuống âm 3,3
điểm phần trăm, held-out mới tăng từ 50 lên 53 trên 60 — tất cả đều trong khoảng
nhiễu, và lắp ghép thành công hai harness hợp lệ bằng chính công cụ của tác giả.
Em cảm ơn thầy và các bạn đã lắng nghe. Nhóm em sẵn sàng trả lời câu hỏi.

*▸ Dừng, nhìn lên, mời câu hỏi.*

---

## Câu hỏi dự kiến (giữ lại từ kịch bản gốc, cập nhật số vòng 2)

1. **Vì sao REBUILD chỉ tăng 6 bài, có phải LoRA không học được gì?**
   Đúng là chưa chứng minh được học thật: 7 bài lật lên, 1 bài lật xuống, p = 0,07.
   Ô thua duy nhất (lcb_009, OpenCode) lại là bài có trong dữ liệu DPO — kiểu đó
   giống nhiễu lấy mẫu hơn là học được. Tín hiệu đi đúng hướng ở cả hai vòng, nhưng
   cần quy mô lớn hơn mới kết luận.
2. **Held-out 53/60 có phải đã chứng minh tổng quát?** Không. Tập held-out v2 khó
   hơn v1 và đã phân biệt được (base 50/60), nhưng McNemar p = 0,45. Nó chứng minh
   adapter không làm tệ đi trên bài mới và pipeline held-out chạy sạch, không rò rỉ —
   không chứng minh khái quát hóa.
3. **Harness Gap 60% → 10% đâu rồi?** Con số đó sai, đã thu hồi: baseline BUILD cũ
   bị trộn 31 trace dry-run mock, Minimal đo được 30% là số ảo. Số live thật vòng 2
   là 6,7% → âm 3,3% (trung bình), tức gap đóng lại và đảo chiều, nhưng cỡ mẫu nhỏ.
4. **Vì sao train ít dữ liệu thế?** Vòng 2 đã mở rộng lên 20 bài train và thêm
   sampling nhiệt độ 0,7, nhưng tổng dữ liệu vẫn chỉ 19 SFT + 6 DPO — còn rất xa
   438 record của tác giả. Đây là giới hạn quy mô, không phải lỗi pipeline.
