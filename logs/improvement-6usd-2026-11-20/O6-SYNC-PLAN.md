# KẾ HOẠCH O6 — Đồng bộ kết quả evolution vào deck HELIX bản tối (CHỈ KẾ HOẠCH, chưa sửa)

Ngày viết: 2026-11-20. Trạng thái: **chỉ kế hoạch — KHÔNG sửa file build,
không sửa slide nào**.
Nguồn: AUDIT.md 20/11/2026 (mục B1–B12) + EVOLUTION_REPORT.md 18/11/2026 +
`build_helix_filled_dark.py` (đọc lại 20/11/2026, dòng ghi trong từng mục).

## 0. Nguyên tắc + thời điểm

- **Thời điểm: SAU KHI chương trình GPU $6 (O2+O3+O1+O5) hoàn thành.**
  Lý do: tổng số lượt chạy và kết quả O2/O3/O1/O5 sẽ đổi nữa — đồng bộ
  hai lần thì lần đầu lỗi thời ngay. Mọi số đánh dấu **[RECOMPUTE]** dưới
  đây PHẢI tính lại từ `summary.json` cuối cùng trước khi sửa, không lấy
  số trong kế hoạch này làm số cuối.
- **Chỉ sửa `build_helix_filled_dark.py`** (nguồn duy nhất của deck tối).
  KHÔNG bao giờ tái sinh từ `build_dark_filled.py` / `build_helix_filled.py`
  (mất hết thay đổi dark-only). KHÔNG sửa tay file PPTX. Backup script
  sang /tmp trước khi sửa; sửa bằng script thay chuỗi chính xác (như lần
  đồng bộ 18/11); build bằng `~/workspace/pptx-venv/bin/python`; PDF qua
  soffice; preview contact sheet 5×4; **kiểm tra render đủ 21–22 slide ở
  độ phân giải đầy đủ, không tràn chữ** trước khi giao.
- Deck nhẹ (16 slide), báo cáo viết, kịch bản, Canva KHÔNG nằm trong kế
  hoạch này (quyết riêng).
- Cập nhật cả comment đầu file build (dòng 548–560: "20 slides since the
  18/11/2026 sync…") thành số slide mới + ngày đồng bộ + danh sách thay đổi.

## 1. Thay đổi theo từng slide (số slide tính theo deck hiện tại, 20 slide)

### Slide 2 — Lộ trình (dòng 671–695)
- Thẻ 04 "555 lượt" → **"[RECOMPUTE] lượt"** (1.262 trước chương trình $6;
  sau chương trình: 1.262 + 364 lượt mới + rerun INFRA — tính lại từ log).
- Notes dòng 692: "555 lượt = rebuild bước 2–3 (210) + fix (210) + khái
  quát hóa (135)" → thêm "+ evolution (707) + chương trình $6 ([RECOMPUTE])".

### Slide 12 — Thiết kế kiểm chứng (dòng 1018–1047)
- Bảng 1, hàng "Chạy bài": "555 lượt, Qwen 7B, lệnh run" → **"[RECOMPUTE]
  lượt, Qwen 7B, lệnh run"**.
- Bảng 1, hàng "Sibling record": "25 từ trace nhóm, theo ý tưởng" →
  **"74 từ trace nhóm, theo ý tưởng"** (25 vòng 2 + 49 fix; O2 không thêm
  record mới vì tái dùng 24+5 của fix — kiểm tra lại lúc đồng bộ).
- Bảng 1, hàng "Train model": "2 LoRA (vòng 2 + trace-thật), Modal A100" →
  **"4 LoRA (vòng 2 + trace-thật + SFT-only + sạch), Modal A100"**
  (3 LoRA sau evolution; +1 adapter sạch sau O2 — đếm lại từ volume
  `helix-adapters` lúc đồng bộ).
- Bảng 1, hàng "Tìm kiếm harness": "Chưa chạy lại (không có lệnh search)" →
  **"Mini-search 9 recipe (bước 6); CLI không có lệnh search"**.
- Bảng 2, hàng "Bài và lượt chạy": "50 bài tự viết; 555 lượt thật + 520
  trace mô phỏng" → **"65 bài tự viết; [RECOMPUTE] lượt thật + 520 trace
  mô phỏng"** (50 + 15 held4).
- Bảng 2, hàng "Dữ liệu và công cụ": "25 record; cùng CLI + Builder;
  101 symlink fixture gãy" → **"74 record; cùng CLI + Builder; fixture v6
  tái tạo 94 thư mục"**.
- Notes: cập nhật 50 bài → 65 bài; 555 lượt → [RECOMPUTE]; 25 record →
  74 record; "101 symlink fixture gãy" → "fixture v6 tái tạo 94 thư mục
  thật (18/11), đã đánh giá 32 lượt (bước 5)"; "không có lệnh tìm
  kiếm/evolve" → thêm "mini-search đã chạy (bước 6, 9 recipe)".

### Slide 13 — Thực nghiệm tái lập (dòng 1050–1077)
- Không đổi chữ trên mặt slide ("210 lượt" ở phase 3 là đúng cho riêng pha
  tái lập). Notes: thêm một câu "Tổng lượt nhóm nay là [RECOMPUTE]
  (xem slide 12); 210 lượt ở đây chỉ là pha tái lập bước 2–3" để người
  nghe không tưởng 210 là tổng.

### Slide 14 — Đối chiếu định lượng (dòng 1080–1110)
- Bảng, hàng "Chạy benchmark": "555 lượt, Qwen 7B" → **"[RECOMPUTE] lượt,
  Qwen 7B"**.
- Bảng, hàng "Sibling record" (nhóm): "25 từ trace nhóm" → **"74 từ trace
  nhóm"**.
- Bảng, hàng "Tìm kiếm harness": "Chưa chạy lại" → **"Mini-search 9 recipe"**.
- Thẻ LỆCH: "Quy mô nhỏ hơn nhiều; benchmark lớn + tìm kiếm harness chưa
  chạy lại — 101 symlink gãy, MiniMax không có." → **"Quy mô nhỏ hơn nhiều;
  benchmark lớn chưa chạy lại — MiniMax không có."** (bỏ 2 mệnh đề sai).
- Notes dòng 1095: "555 lượt = …" → [RECOMPUTE]; "25 …" → "74 …".

### Slide 15 — Kết quả mở rộng (1) (dòng 1102–1140)
- Thẻ 3: "Harness thật: LoRA – base (p = 0,0063)" → **"Harness thật
  pi-mono: LoRA – base (p = 0,0063)"** (thêm tên harness — audit flag).
- Notes: thêm 2 dòng — (a) "Base pi-mono tự trôi 25→20→22→23/35 qua 4 lần
  chạy cùng giao thức (bước 2, fix, lặp lại bước 1, ablation bước 3) —
  chênh lệch dưới ~5 bài nằm trong nhiễu"; (b) "Ablation SFT-only (bước 3):
  base 23/35, SFT-only 30/35, realtool 25/35, p = 0,1797 — không kết luận
  được; phát hiện sạch: sửa hành vi không cần DPO".
- Không đổi số 66/80, 53/60, 15/35–25/35 (đã kiểm chứng đúng).

### Slide 16 — Kết quả mở rộng (2) (dòng 1144–1185)
- **Sửa nhãn gây hiểu lầm (audit flag):** thẻ 1 ("0/35 → 0/15",
  "Text-only pi-mono: cũ → mới (C1, G1)") → **("0/35 • 0/15",
  "Text-only pi-mono, LoRA mới: 35 bài fix + 15 bài mới (C1, G1)")**.
  Hai số đều là của LoRA mới trên hai tập bài khác nhau — không được viết
  như "cũ → mới".
- Bảng bài mới (held3): thêm dòng gộp dưới bảng hoặc dòng text dưới bảng:
  **"Gộp n = 30 (held3+held4, pi-mono): mới 26/30 vs cũ 17/30
  (p = 0,0039); base 23/30"** + caveat trong hộp vàng: "nhánh cũ tự trôi
  10/15→7/15 giữa hai cohort nên biên rộng hơn một phần do nhánh so sánh
  trôi".
- Hộp vàng: thêm "Lặp lại bước 1 xác nhận cả 4 phán quyết (C1 0/35;
  C2 29/35 vs 15/35, p = 0,0005; G1 0/15 vs 5/15; G2 13/15 vs 9/15,
  p = 0,2188)".
- Notes: thêm số gộp n = 30 + caveat nhánh cũ trôi + kết quả lặp lại;
  cập nhật "kiểm tra khái quát hóa dựa vào 15 bài mới (n nhỏ, p = 0,25)"
  → "nay gộp n = 30 (held3+held4), p = 0,0039".
- **Sau chương trình $6:** thêm kết quả O2 vào slide này (adapter sạch trên
  45 bài — số [RECOMPUTE] từ O2 RESULTS.md; phán quyết C1/C2 của O2).
  Vị trí: một dòng dưới bảng bài mới hoặc trong hộp vàng (tùy chỗ trống
  lúc build — nếu tràn thì đưa vào notes + slide evolution mới, xem §2).

### Slide 17 — Phân tích sâu (dòng 1187–1213)
- Hộp H3b (phải, dưới): thêm sau đoạn fix hiện có một đoạn ngắn (giữ trong
  khung 4,14 × 1,5 — **nếu tràn thì chỉ giữ 1 dòng trên mặt slide, phần
  còn lại vào notes**):
  **"Tách hành vi/chất lượng (bước 4a): +37,14pp = 71% hành vi / 29%
  chất lượng (quan sát, không nhân quả — không trích riêng). Chẩn đoán
  harness (bước 2): opencode text-only 169/185 do prompt; hermes 41%
  'script fantasy'; shim hiếm khi là nút thắt (4/310). Mini-search:
  prompt opencode 0/10, prompt pi 4–7/10."**
- Notes: thêm 2 dòng — (a) "Ablation SFT-only: DPO không chứng minh được
  thêm giá trị (30/35 vs 25/35, p = 0,1797)"; (b) "v6: hành vi không
  chuyển sang bài sửa lỗi (base 0/16, realtool 1/16; 30/32 file nguyên
  seed)".
- Ảnh bảng 3 harness (`19_bang-ket-qua-3-harness.png`) là số bước 2–3 —
  giữ nguyên, đã ghi trong notes ("Bảng này là số bước 2–3"). Không tái
  vẽ trong kế hoạch này (tái vẽ từ pool 1.262 lượt là phân tích offline
  O7, $0, làm riêng nếu Triệu muốn).

### Slide 18 — Giới hạn (dòng 1214–1249; sẽ thành slide 19/20 sau khi chèn)
- Giới hạn 1: "Mỗi ô 1 lần chạy; khái quát hóa n = 15" → **[RECOMPUTE theo
  O1: nếu O1 chạy đủ thì "Mỗi ô 2 lần chạy; khái quát hóa n = 30"; nếu O1
  bị cắt thì giữ "Mỗi ô 1 lần chạy" và ghi rõ]**. Mô tả đi kèm cập nhật
  theo: "p = 0,0063 là của mẫu đơn" → thêm base drift + kết quả O1.
- Giới hạn 6: "Chưa chạy benchmark lớn" / "101 symlink gãy + không có
  MiniMax + CLI không có lệnh search" → **"Fixture v6 tái tạo nhưng hành
  vi không chuyển sang bài sửa lỗi (0/16 vs 1/16); MiniMax không có;
  benchmark lớn chưa chạy lại"**.
- Dải hướng phát triển: bỏ "chẩn đoán phía harness opencode/hermes"
  (đã làm xong bước 2) → **"Hướng phát triển: mở rộng bài mới (held5) •
  đo chất lượng code tách khỏi hành vi • can thiệp prompt opencode
  theo chẩn đoán [cập nhật theo kết quả O3]"**.
- Notes: cập nhật "kiểm tra khái quát hóa dựa vào 15 bài mới (n nhỏ,
  p = 0,25)" → "gộp n = 30 (p = 0,0039)"; thêm "Fix train từ trace của
  đúng 35 bài đánh giá — O2 train lại adapter sạch từ 20 bài train
  [ghi kết quả O2]".

### Slide 19 — Kết luận (dòng 1250–1285; sẽ thành slide 20/21 sau khi chèn)
- RQ2: "555 lượt qua 3 harness thật bằng lệnh run" → **"[RECOMPUTE] lượt
  qua 3 harness thật bằng lệnh run"**.
- RQ3: "H3b: không ủng hộ (LoRA vòng 2); ủng hộ có điều kiện (LoRA
  trace-thật: 28/35, 13/15 bài mới)" → **"H3b: không ủng hộ (LoRA vòng 2);
  ủng hộ có điều kiện (LoRA trace-thật: 28/35; bài mới gộp n = 30:
  26/30 vs 17/30, p = 0,0039); SFT-only cho thấy sửa hành vi không cần
  DPO [cập nhật phán quyết O2 nếu O2 đổi kết luận]"**.
- Take-home + đóng góp nhóm: giữ nguyên.

### Slide 20 — Cảm ơn / Tài liệu (dòng 1287–1304; sẽ thành slide 21/22)
- Dòng footer "Vòng 2 (12/11) + rebuild (15–16/11) + fix & khái quát hóa
  (18/11/2026)" → thêm **"+ evolution (18/11) + chương trình $6
  ([RECOMPUTE ngày])"**.
- Không đổi danh sách tài liệu tham khảo (chỉ 5 dòng hiện có).

## 2. Slide MỚI — "Tiến hóa 6 bước" (chèn SAU slide 17)

- Vị trí: sau slide 17 (Phân tích sâu), trước slide Giới hạn. Kicker đề
  xuất: "Phần 3 — Mở rộng". Tiêu đề đề xuất: **"Tiến hóa 6 bước: phán
  quyết lặp lại được, khái quát hóa lên n = 30"**. Số slide: 18 (nếu chỉ
  có evolution) — xem §3 về đánh số khi có cả P8.
- Nội dung đề xuất (3 thẻ stat trên + 1 bảng/hộp dưới + dải amber):
  - Thẻ 1: "26/30 – 17/30" / "Bài mới gộp n = 30, pi-mono: mới – cũ
    (p = 0,0039)".
  - Thẻ 2: "4/4" / "Phán quyết fix + gen lặp lại được (bước 1)".
  - Thẻ 3: "71% / 29%" / "Tăng fix: hành vi / chất lượng (quan sát)".
  - Hộp dưới (2 cột hoặc 5 dòng): "Chẩn đoán harness: opencode 169/185
    do prompt • Mini-search: prompt opencode 0/10, prompt pi 4–7/10 •
    SFT-only 30/35 vs realtool 25/35 (p = 0,1797, DPO chưa chứng minh) •
    v6: base 0/16, realtool 1/16 — hành vi không chuyển sang bài sửa lỗi".
  - Dải amber: "Giới hạn: mọi ô 1 lần chạy [hoặc 2 lần sau O1]; base trôi
    25→20→22→23/35; nhánh cũ trôi 10/15→7/15 giữa hai cohort gen".
- Speaker notes: đầy đủ 6 bước + nguồn từng số (EVOLUTION_REPORT.md +
  từng step summary.json) + caveat.
- **Sau chương trình $6:** thêm 1–2 dòng kết quả O2/O3/O1/O5 vào hộp
  dưới (hoặc thay dòng v6 bằng kết quả O5 nếu O5 đổi kết luận) — số
  [RECOMPUTE], không viết trước.

## 3. Đánh số lại + vị trí slide P8 (LIÊN HỆ — đã duyệt, KHÔNG thuộc kế hoạch này)

- Chỉ evolution (không P8): deck 20 → **21 slide**. Slide cũ 18→19
  (Giới hạn), 19→20 (Kết luận), 20→21 (Cảm ơn). Slide evolution mới là 18.
- Cả evolution + P8: deck 20 → **22 slide**. Thứ tự theo form đã chốt
  (kết quả → liên hệ → giới hạn → kết luận): slide 17 Phân tích sâu →
  **18 Evolution** → **19 LIÊN HỆ (P8)** → 20 Giới hạn → 21 Kết luận →
  22 Cảm ơn. **P8 đi SAU slide evolution, không phải trước** — nếu ai
  chèn P8 ngay sau slide 17 thì thứ tự sai.
- P8 do Triệu duyệt riêng và thực hiện riêng (đã duyệt 20/11, tạm dừng
  chờ rà soát xong) — kế hoạch này chỉ quy định vị trí tương đối của nó,
  không viết nội dung P8.
- Cập nhật số slide trong `header(...)` của các slide bị dời + comment
  đầu file + mọi chỗ trong notes ghi "slide 16/17/18" theo số mới
  (kiểm tra bằng grep "slide 1[6-9]" và "slide 20" sau khi sửa).

## 4. Những gì KHÔNG sửa

- Slide 1, 3–11, 13: đã kiểm chứng đúng (AUDIT.md §A) — không động vào.
- Deck nhẹ, báo cáo viết, kịch bản, Canva: quyết riêng.
- Không thêm ảnh trang trí, không thêm hình robot/stock (luật thầy).
- Không sửa số nào chưa [RECOMPUTE] từ file tổng kết cuối cùng.

## 5. Checklist trước khi giao (người thực hiện tự kiểm)

1. Mọi số [RECOMPUTE] đã tính lại từ summary.json cuối (ghi nguồn từng số).
2. Build PPTX + PDF + preview; render-check đủ slide, không tràn chữ
   (đặc biệt slide 16, 17, slide evolution mới).
3. Tổng số slide đúng (21 nếu chỉ evolution; 22 nếu + P8); số trong vòng
   tròn header khớp thứ tự.
4. Không còn chuỗi "555 lượt", "25 record", "2 LoRA", "Chưa chạy lại",
   "101 symlink gãy", "0/35 → 0/15" trong file build (grep kiểm tra).
5. Backup file build cũ còn ở /tmp; commit không đụng tới (KHÔNG commit/push).
