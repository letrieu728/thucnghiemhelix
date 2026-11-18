# KỊCH BẢN RÚT GỌN — HELIX, NỬA SAU (slide 19–36) — BẢN NHÁP

**Mục đích:** bản rút gọn ~8 phút cho người trình bày nửa sau, để vừa suất 20–25 phút/nhóm
đã gồm hỏi đáp (mỗi người ~8 phút). Kịch bản gốc nửa sau dài ~13,4 phút (805 giây);
bản này ~7 phút 45 giây (465 giây).

**Trạng thái — ĐỌC TRƯỚC KHI DÙNG:**
- Đây là BẢN NHÁP, chưa phải bản chính thức. Kịch bản gốc
  (`kich-ban-thuyet-trinh-helix.docx`) và deck PPTX vẫn giữ số liệu cũ — chưa sửa.
- Mọi con số dưới đây lấy từ đợt chạy live ngày 12/11/2026, đã ghi trong
  `~/workspace/helix-eval/thucnghiemhelix/closed-loop/REBUILD_REPORT.md`
  (BUILD 28/40, REBUILD 31/40, held-out base 39/40, LoRA 40/40; commit
  f84a03a–bf6fdfc). Các con số cũ (Minimal 30% → 60%, gap 60% → 10%,
  9 SFT / 8 DPO, "3 breakthrough") đã bị thu hồi — KHÔNG dùng nữa.
- Nhóm 1 + 2 nâng điểm HELIX đang chạy (held-out v2 khó hơn, tập train mở rộng).
  Nếu kết quả nhóm 2 thay đổi số liệu, phải cập nhật lại bản này trước buổi trình bày.
- Còn cần Triệu + Việt chốt ai nói nửa nào. Bản này viết cho nửa sau (19–36) vì đó
  là phần việc của chính nhóm, Triệu nắm chắc nhất — nếu Việt nhận nửa sau thì
  đổi người đọc, nội dung giữ nguyên.
- Slide 27 (ảnh dashboard Modal) đã lỗi thời: credit và trạng thái app trên ảnh là
  số cũ; app đã dừng sau đợt chạy 12/11. Nên thay ảnh mới hoặc bỏ slide này khi
  sửa deck.

## Cách đọc

Đọc gần như nguyên văn. Số trong ngoặc là thời lượng gợi ý từng slide.
Tổng: 465 giây ≈ 7 phút 45 giây, chừa ~15 giây đệm chuyển slide.

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
chỉ đọc. Song song, nhóm chạy trọn vòng closed-loop trên bản fork: BUILD live đủ
40 lượt, train LoRA từ dữ liệu live-only, rồi đánh giá rebuild và held-out.

*▸ Nói thẳng giới hạn phạm vi ngay từ đầu giúp phần hỏi đáp dễ hơn.*

### Slide 21 — Pipeline closed-loop (~25 giây)

Pipeline gồm năm thành phần. File 01 dựng server vLLM trên Modal, hỗ trợ
multi-LoRA. File 02 chạy đánh giá 10 bài LiveCodeBench nhân 4 harness. File 03
trích các cặp SFT và DPO từ các quỹ đạo chị em — chỉ lấy trace live, có ghi
provenance. File 04 train LoRA bằng Unsloth và TRL trên GPU A100. Và notebook
evaluate_rebuild so sánh BUILD với REBUILD và vẽ biểu đồ.

*▸ Đọc tên file chậm vừa phải — đây là bằng chứng pipeline có thật.*

### Slide 22 — Kết quả trung tâm: BUILD vs REBUILD (~55 giây)

Đây là bảng kết quả trung tâm, trên cùng 10 bài, model gốc so với model gắn LoRA.
Minimal tăng từ 6 lên 7 trên 10 bài. Pi Mono từ 7 lên 8. Hermes giữ nguyên 7.
OpenCode từ 8 lên 9. Tổng cộng 28 trên 40 lên 31 trên 40 — tăng ròng 3 trace:
4 bài lật từ trượt thành đậu, 1 bài lật ngược lại. Nhóm em nói thẳng: với chỉ
10 bài, mỗi bài là 10 điểm phần trăm, mức tăng này chưa chứng minh được học thật —
và sẽ nói rõ vì sao ở slide thống kê sau.

*▸ Đọc bảng theo hàng. Không giấu chiều lật ngược (OpenCode mất 1 bài).*

### Slide 23 — Harness Gap và hợp tập (~30 giây)

Về khoảng cách harness: trung bình 3 harness nâng cao trừ Minimal là 13,3% ở BUILD,
xuống 10,0% ở REBUILD — giảm 3,3 điểm, tức đúng một bài, không phân biệt được
với nhiễu. Lấy harness tốt nhất trừ Minimal thì gap là 20% ở cả hai vòng, không đổi.
Câu chuyện cũ "gap thu hẹp từ 60% xuống 10%" là sai — nó xuất phát từ baseline
BUILD cũ bị trộn trace mock — nhóm em đã thu hồi. Hợp tập kiểu paper (ít nhất
một harness giải được): 8 trên 10 bài ở BUILD, lên 10 trên 10 ở REBUILD — con số
mô tả, không phải bằng chứng học được.

*▸ Câu thu hồi là bắt buộc phải nói — đừng bỏ qua.*

### Slide 24 — Số bước và độ trễ (~20 giây)

Số bước gần như không đổi: Minimal giữ 1,0 bước; Pi Mono giảm nhẹ từ 2,3 xuống
1,8; Hermes từ 2,2 lên 2,3; OpenCode từ 2,1 lên 2,2. Độ trễ cũng không cải thiện —
Minimal từ 17,2 giây lên 27,0 giây, Hermes từ 47,5 lên 74,6 giây. Nhóm em không
kể đây là cải thiện: mô hình và harness chỉ hợp nhau hơn ở vài bài, không phải
nhanh hơn một cách hệ thống.

*▸ Kết bằng câu về "cặp model–harness" — quay lại luận điểm của bài báo.*

### Slide 25 — Harness Gap, nhắc lại một dòng (~15 giây)

Slide này chỉ tách riêng chỉ số gap vừa nói: 13,3% xuống 10,0% theo cách tính
trung bình của báo cáo, và 20% xuống 20% nếu lấy harness tốt nhất trừ Minimal.
Cả hai cách đều cho cùng kết luận: gap gần như không đổi sau một vòng distill nhỏ.

*▸ Slide này trùng nội dung slide 23 — khi sửa deck nên gộp hai slide làm một.*

### Slide 26 — Train LoRA (~45 giây)

Chi tiết lần train: mô hình gốc Qwen2.5-Coder-7B-Instruct, nạp 4-bit, Unsloth
kết hợp PEFT, LoRA rank 16, alpha 32, dropout 0,05. Dữ liệu train rất nhỏ và
toàn bộ là live: 8 mẫu SFT và chỉ 2 cặp DPO — vì chỉ có 2 bài vừa có lời giải
đúng vừa có lời giải sai. Train 3 bước SFT, loss từ 1,03 xuống 0,95; 3 bước DPO,
loss từ 0,693 xuống 0,683 — gần như phẳng. Adapter cũ (chạy ngày 4/11) đã được
backup trước khi ghi đè. Mục đích của lần train này là kiểm chứng vòng lặp khép
kín được với provenance đầy đủ, chứ chưa nhằm tối đa hóa điểm số.

*▸ Nhấn mục đích: kiểm chứng vòng lặp khép kín, không phải tối đa hóa điểm.*

### Slide 27 — Adapter đã serve trên Modal (~20 giây)

Ảnh này là dashboard Modal đợt đánh giá rebuild: ứng dụng helix-vllm-engine chạy
vLLM, adapter helix-lora-final được mount qua multi-LoRA để phục vụ đánh giá.
Lưu ý: ảnh chụp trước đợt chạy live ngày 12/11, con số credit trên ảnh đã cũ —
app đã dừng hẳn sau đợt chạy, chi phí cả chuỗi khoảng 2 đến 2,5 đô, trong hạn
8 đô nhóm đặt ra, không động tới thẻ.

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
để mở pull request cho Việt xem qua rồi mới merge, vì push trực tiếp bị chặn.

*▸ Không đọc lại dòng commit cũ về "80 trace" — con số đó thuộc đợt đánh giá cũ.*

### Slide 33 — Kết quả lắp ghép (~30 giây)

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

### Slide 35 — Hạn chế & lưu ý (~40 giây)

Nhóm em xin nêu thẳng các hạn chế. Một, mẫu đánh giá chỉ có 10 bài tự viết,
chưa đủ để kết luận khái quát; kiểm định McNemar cho mức tăng 28 lên 31 cho
p bằng 0,375 — không phân biệt được với không thay đổi. Hai, 4 "harness" của
nhóm thực chất là system prompt cộng vòng lặp chat, chưa phải recipe đã assemble
thật. Ba, train chỉ 6 bước trên 8 mẫu SFT và 2 cặp DPO, loss gần như phẳng.
Bốn, tập held-out đã bão hòa: model gốc đậu 39 trên 39 lượt hợp lệ, LoRA 40
trên 40 — bài duy nhất model gốc rớt là lỗi hạ tầng tràn context 4096 token,
không phải giải sai — nên held-out này chứng minh adapter không làm tệ đi,
chứ không chứng minh tổng quát được.

*▸ Nói chậm, nghiêm túc — slide này thường được thầy đánh giá cao nếu trình bày thẳng thắn.*

### Slide 36 — Kết thúc (~20 giây)

Phần trình bày về bài báo HELIX của nhóm em xin kết thúc tại đây. Tóm lại trong
một câu: năng lực của AI agent nằm ở cả mô hình lẫn harness, và nhóm em đã tự
tay khép kín vòng lặp đó bằng dữ liệu live có provenance — train một LoRA adapter,
thấy gap gần như không đổi (13,3% xuống 10,0%, trong khoảng nhiễu), và lắp ghép
thành công hai harness hợp lệ bằng chính công cụ của tác giả. Em cảm ơn thầy và
các bạn đã lắng nghe. Nhóm em sẵn sàng trả lời câu hỏi.

*▸ Dừng, nhìn lên, mời câu hỏi.*

---

## Câu hỏi dự kiến (giữ lại từ kịch bản gốc, cập nhật số)

1. **Vì sao REBUILD chỉ tăng 3 bài, có phải LoRA không học được gì?**
   Đúng là chưa chứng minh được học thật: 4 bài lật lên, 1 bài lật xuống, p = 0,375.
   OpenCode tiến bộ ở đúng 2 bài (lcb_002, lcb_003) mà BUILD không giải được bài nào
   — nên không có trong dữ liệu train — nhưng lại rớt 1 bài vốn có trong dữ liệu
   train (lcb_009). Kiểu đó giống nhiễu lấy mẫu hơn là học được.
2. **Held-out 40/40 có phải đã chứng minh tổng quát?** Không. Tập held-out v1 quá
   dễ — model gốc cũng gần như đậu hết (39/40, 1 lỗi hạ tầng). Nó chỉ chứng minh
   adapter không làm tệ đi và pipeline held-out chạy sạch, không rò rỉ.
3. **Harness Gap 60% → 10% đâu rồi?** Con số đó sai, đã thu hồi: baseline BUILD cũ
   bị trộn 31 trace dry-run mock, Minimal đo được 30% là số ảo. Số live thật là
   13,3% → 10,0% (trung bình) và 20% → 20% (tốt nhất trừ Minimal).
4. **Vì sao train ít dữ liệu thế?** Chỉ có 2 bài vừa có đáp án đúng vừa có đáp án
   sai nên chỉ trích được 2 cặp DPO. Nhóm 2 đang mở rộng tập train lên 20–25 bài
   và thêm sampling để có đủ cặp chosen/rejected.
