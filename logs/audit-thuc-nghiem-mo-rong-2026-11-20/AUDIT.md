# Kiểm tra thực nghiệm & mở rộng — deck HELIX bản tối (slide 12–17)

- Ngày kiểm tra: 20/11/2026. Trạng thái: **chỉ kiểm tra, không sửa file nào, không chạy GPU**.
- Phạm vi: slide 12–17 trong `~/workspace/your_files/blueprint-16-slide/build_helix_filled_dark.py` (nguồn duy nhất của deck tối), cả chữ trên slide và speaker notes.
- Phương pháp: mọi số headline được tính lại từ `summary.json` / `summary.md` / `RESULTS.md` trong `~/workspace/helix-eval/logs/` (không copy từ trí nhớ). Số phía paper được đối chiếu lại với arXiv HTML v1 (Fan & Huang 2026, arXiv:2608.13951, truy cập 20/11/2026).
- Deck đồng bộ lần cuối 18/11/2026, **trước** khi chương trình evolution (6 bước) hoàn thành cùng ngày. Xem mục (B).

## (A) Kiểm chứng từng slide

### Slide 12 — Thiết kế kiểm chứng (dòng 1018–1047)

| Khẳng định trên slide / notes | Nguồn đối chiếu | Kết quả |
|---|---|---|
| 555 lượt = 210 rebuild + 210 fix + 135 khái quát hóa | `rebuild-driver-2026-11-15/summary.json` (70 lượt) + `rebuild-driver-multiharness-2026-11-16/summary.json` (140 lượt) + `rebuild-fix-lora-tooluse/summary.json` (210 lượt) + `generalisation-check-2026-11-18/summary.json` (135 lượt) | ✅ OK |
| 50 bài tự viết = 20 train + 15 held-out v2 + 15 khái quát hóa | `rebuild-driver-2026-11-15/tasks.json` (35 bài: 20 lcb_ + 15 held2_) + `generalisation-check-2026-11-18/tasks.json` (15 held3_) | ✅ OK (tại thời điểm đồng bộ; nay đã lỗi thời — xem B1) |
| 520 trace live qua harness mô phỏng: vòng 1: 160, vòng 2: 360 | `~/workspace/helix-eval/thucnghiemhelix/RESULTS.md:201,207,236` | ✅ OK |
| 25 record từ trace nhóm, "theo ý tưởng" | `logs/train_round2.log:28` (SFT nạp 19 mẫu) + DPO 6 cặp (vòng 2) → 19 + 6 = 25 | ⚠️ **FLAG nhỏ** — số 25 cộng lại được (19 SFT + 6 DPO), nhưng slide không ghi rõ cách đếm; paper 438 record gồm 5 mục đích (SFT/critic/filter/preference), nhóm chỉ có SFT + DPO, không có critic/filter — phép so sánh "25 vs 438" dễ gây hiểu lầm là cùng loại. Ngoài ra nay đã thiếu: fix rút thêm 40 SFT + 9 DPO = 49 record nữa, tổng nhóm là 74, không còn là 25 (xem B2) |
| 2 LoRA (vòng 2 + trace-thật), Modal A100 | `rebuild-fix-lora-tooluse/RUN_LOG.md` (adapter `helix-lora-realtool`) | ⚠️ **FLAG (lỗi thời)** — evolution bước 3 train thêm adapter thứ 3 `helix-lora-sftonly`; nay là 3 LoRA (xem B3) |
| "Tìm kiếm harness: Chưa chạy lại (không có lệnh search)" | `rebuild-driver-2026-11-15/RESULTS.md` (CLI chỉ có run/assemble/validate/compose/task-parity) | ⚠️ **FLAG (lỗi thời)** — evolution bước 6 đã chạy mini-search đầu tiên (9 recipe, `runner.mts`); câu này nay sai (xem B4) |
| "101 symlink fixture gãy" (bảng tài nguyên + notes) | Đúng tại thời điểm đồng bộ | ⚠️ **FLAG (lỗi thời)** — fixture đã tái tạo 94 thư mục thật ngày 18/11 và đã đánh giá 32 lượt (bước 5); "101 symlink gãy" không còn mô tả đúng hiện trạng (xem B5) |
| Paper: 6.500 slot + 3.000 lặp lại + 550 SWE | arXiv HTML v1 §5.2–5.3: 6.500 = 65 ứng viên × 100 bài (L829); 3.000 = 3 thành viên × 10 lượt × 100 bài (L835–841); 550 = 5 thành viên × 2 lượt × 55 bài (L851–859) | ✅ OK — phân rã "3 thành viên × 1.000" trong notes là đúng |
| Paper: 100 bài LCB + 55 SWE-bench; 438 record; MiniMax-M2.7-highspeed | arXiv HTML v1 §5–6, Table 3 (63/56/52/113/154) | ✅ OK |
| "Mỗi ô 1 lần chạy • Chấm ngoài bằng test suite" (dải cuối slide) | Đúng với mọi lượt chạy đã làm | ✅ OK — và là giới hạn quan trọng nhất còn tồn tại (xem C) |
| Notes: "upstream_git_status_after.txt rỗng — không sửa code tác giả" | `rebuild-driver-2026-11-15/upstream_git_status_after.txt` = 0 byte (kiểm tra 20/11) | ✅ OK |

### Slide 13 — Thực nghiệm tái lập (dòng 1048–1077)

| Khẳng định | Nguồn | Kết quả |
|---|---|---|
| "Chạy harness thật (210 lượt)" = bước 2 (70 lượt pi-mono) + bước 3 (140 lượt opencode + hermes) | `rebuild-driver-2026-11-15/summary.json` + `rebuild-driver-multiharness-2026-11-16/summary.json` | ✅ OK — đúng cho riêng pha tái lập; nhưng người nghe dễ tưởng 210 là tổng số lượt của nhóm (tổng thật là 555, nay 1.262 — xem B6) |
| "0 lỗi hạ tầng" (notes) | Cả 4 ô summary.json bước 2–3: `n_infra: 0` | ✅ OK |
| "pi-mono + minimal lắp đạt 08/11 (303/176 atom, 96 cổng)" (notes) | `upstream/docs/site/index.html:12676,12688` (pi-mono 303 atoms, 96 ports; minimal 176 atoms, 96 ports) | ✅ OK |
| "Bước 1 ghép nối: 1 bài bug-fix đạt cả 4 tiêu chí cam kết trước" (notes) | `rebuild-step1-2026-11-15/RESULTS.md:6` ("THÀNH CÔNG — cả 4 tiêu chí đều đạt") | ✅ OK |
| "Lệnh assemble chính xác không file nào ghi lại nên slide không bịa" (notes) | Không có file nào ghi lệnh assemble trong logs bước 1–3 | ✅ OK — trung thực, không bịa |
| Ảnh Builder là "ảnh GHÉP từ 2 lần chụp thật … không sửa pixel nội dung nào" (notes) | Ghi trong notes; ảnh không kiểm chứng bằng pixel trong audit này | ⚠️ **Không kiểm chứng được từ text** — tin theo ghi chú, không có bằng chứng độc lập trong logs/ |

### Slide 14 — Đối chiếu định lượng (dòng 1078–~1110)

| Khẳng định | Nguồn | Kết quả |
|---|---|---|
| Lắp ghép: paper "CLI + Builder, 65 ứng viên" | arXiv HTML v1 §5–6 (65 ứng viên) | ✅ OK |
| Chạy benchmark: paper "6.500 lượt, MiniMax" | arXiv HTML v1 §5.2 (L829) | ✅ OK |
| Sibling: paper "438 từ 200 slot" | arXiv HTML v1 §6.3 (L1157–1161) | ✅ OK |
| Train model: paper "Không (§9.5)" | arXiv HTML v1 §9.5 (paper chỉ materialize dữ liệu, không train) | ✅ OK |
| Tìm kiếm: paper "Chọn theo từng bài" | arXiv HTML v1 §6.1 (chọn theo từng bài là post-hoc) | ✅ OK |
| Nhóm: "555 lượt, Qwen 7B" | Như slide 12 | ✅ OK (nay lỗi thời — xem B6) |
| Nhóm: "25 từ trace nhóm" | Như slide 12 | ⚠️ Như slide 12: nay tổng là 74 record, không còn 25 |
| Thẻ KHỚP: "verification đạt, fingerprint khớp Builder, transcript tool-call thật" | `rebuild-step1-2026-11-15/RESULTS.md:6` (4 tiêu chí đạt); fingerprint `pi-mono@0.1.0:f87e68defe775bb6` vừa có trong Builder HTML (`upstream/docs/site/index.html`) vừa là giá trị kỳ vọng của probe CLI (`evolution-2026-11-18/step6-mini-search/DESIGN.md:253-255`) | ✅ OK |
| Thẻ LỆCH: "benchmark lớn + tìm kiếm harness chưa chạy lại — 101 symlink gãy, MiniMax không có" | Benchmark lớn vẫn chưa chạy lại ✅; MiniMax vẫn không có ✅ | ⚠️ **FLAG (lỗi thời một nửa)** — "tìm kiếm harness chưa chạy lại" nay sai (mini-search bước 6 đã chạy); "101 symlink gãy" nay sai (fixture đã tái tạo 94 thư mục). Chỉ còn "benchmark lớn chưa chạy lại" và "MiniMax không có" là đúng |

### Slide 15 — Kết quả mở rộng (1): LoRA vòng 2 (khối Slide 15)

| Khẳng định | Nguồn | Kết quả |
|---|---|---|
| "66/80 – 60/80, Vòng 2: LoRA – base (p = 0,0703)" | Vòng 2: BUILD2 60/80 → REBUILD2 66/80, McNemar 7 thắng/1 thua, p = 0,0703 | ✅ OK |
| "53/60 – 50/60, Held-out v2: LoRA – base (p = 0,4531)" | Held-out v2: base 50/60 → LoRA 53/60, p = 0,4531 | ✅ OK |
| "15/35 – 25/35, Harness thật: LoRA – base (p = 0,0063)" | `rebuild-driver-2026-11-15/summary.md:15` (base 25/35 vs LoRA 15/35, gains 1/losses 11, p = 0,0063) | ⚠️ **FLAG nhỏ (mơ hồ)** — số này chỉ đúng trên **pi-mono** nhưng thẻ không ghi tên harness; người nghe có thể tưởng là "harness thật" nói chung. Trên opencode cả hai 0/35, hermes 0/35 vs 1/35 — rất khác |
| "Khi có ghi file: LoRA 15/21 (71%), base 25/31 (81%)" (notes) | `rebuild-driver-2026-11-15/RESULTS.md:25-27` (LoRA 15/21 = 71,4%; base 25/31 = 80,6%) | ✅ OK |
| "LoRA r=16, α=32; SFT 9 bước 1,00→0,49; DPO 3 bước 0,693→0,660; seed 42" | `logs/train_round2.log`: SFT loss 0,9999 → 0,494 (dòng 59, 94); DPO 0,6931 → 0,6595 (dòng 143, 154); `thucnghiemhelix/closed-loop/ROUND2_DESIGN.md:126` (seed 42) | ✅ OK |
| "opencode 0/35 cả hai, hermes 0/35 so với 1/35" (notes) | `rebuild-driver-multiharness-2026-11-16/summary.json` (opencode base 0/35, lora 0/35; hermes base 0/35, lora 1/35) | ✅ OK |
| "Sampling temp 0,7 tạo cặp đối lập cho 4 bài (ROUND2_DESIGN.md)" (notes) | `ROUND2_DESIGN.md:60-61` (sampling temp 0,7, n=2) | ⚠️ **FLAG nhỏ** — temp 0,7 có nguồn; riêng con số "4 bài" không đối chiếu lại được trong audit này (không rõ 4 bài nào trong file thiết kế) |
| "Biểu đồ: Pass@1 + Wilson 95% CI, temp 0.0 baseline cells only" (notes) | Ảnh `round2_comparison_plot_toi.png` — không kiểm chứng bằng pixel trong audit này | ⚠️ **Không kiểm chứng được từ text** — chi tiết cấu trúc biểu đồ chỉ tin theo notes |
| Notes: "Caveat: mỗi ô 1 lần chạy — không kết luận LoRA nhìn chung kém hơn" | Đúng, và nay càng đúng hơn: base pi-mono đã trôi 25→20→22→23 qua 4 lần chạy (xem B7) | ✅ OK — nhưng **base drift không xuất hiện trên mặt slide nào** (xem B7) |

### Slide 16 — Kết quả mở rộng (2): fix + khái quát hóa (khối Slide 16)

| Khẳng định | Nguồn | Kết quả |
|---|---|---|
| Thẻ "0/35 → 0/15, Text-only pi-mono: cũ → mới (C1, G1)" | `rebuild-fix-lora-tooluse/summary.json` (realtool pi-mono no_tool 0/35); `generalisation-check-2026-11-18/summary.json` (realtool pi-mono no_tool 0/15) | ⚠️ **FLAG (nhãn gây hiểu lầm)** — hai số đều là của **LoRA mới** trên hai tập bài khác nhau (fix 35 bài → gen 15 bài), không phải "cũ → mới". Số của LoRA cũ (14/35 fix, 3/15 gen) chỉ nằm trong hộp vàng bên dưới. Người nghe dễ đọc thành "text-only giảm từ 0/35 xuống 0/15" |
| Thẻ "28/35 – 15/35, Fix pi-mono: mới – cũ (p = 0,001)" | `rebuild-fix-lora-tooluse/summary.md:186` (gains 14/losses 1, p = 0,001); realtool 28/35, old 15/35 | ✅ OK |
| Thẻ "13/15 – 10/15, Bài mới pi-mono: mới – cũ (n = 15)" | `generalisation-check-2026-11-18/summary.md:139` (gains 3/losses 0, p = 0,25) | ✅ OK |
| Bảng bài mới: Pi Mono 11/10/13; OpenCode 0/0/5; Hermes 1/1/6 | `generalisation-check-2026-11-18/summary.json` (pi-mono base 11, lora 10, realtool 13; opencode 0/0/5; hermes 1/1/6) | ✅ OK |
| "Text-only (base / cũ / mới): pi-mono 1 / 3 / 0; opencode 15 / 15 / 10; hermes 7 / 13 / 6" | `generalisation-check-2026-11-18/summary.json` (no_tool_mechanism từng ô — khớp cả 9 số) | ✅ OK |
| "LoRA mới: SFT 40 + DPO 9 từ trace thật; SFT 1,15→0,40; DPO 0,69→0,57" | `rebuild-fix-lora-tooluse/RUN_LOG.md:60-61` (SFT 15 bước 1,1516→0,3951, 40 mẫu; DPO 6 bước 0,6931→0,5679, 9 cặp) | ✅ OK |
| "G1 + G2 đạt trên pi-mono (tiêu chí đăng ký trước)" | `generalisation-check-2026-11-18/summary.md:139` (G2 p = 0,25) | ✅ OK — nhưng p = 0,25 (không ý nghĩa) chỉ nằm trong hộp vàng + notes, không nằm cạnh thẻ "13/15 – 10/15" |
| Hộp vàng: "n = 15 nhỏ, khoảng tin cậy chồng lấn (p = 0,25). LoRA cũ chỉ text-only 3/15 trên bài mới — thấp hơn 14/35 trên bài cũ" | `generalisation-check-2026-11-18/summary.json` (lora no_tool 3/15); `rebuild-driver-2026-11-15/RESULTS.md:25` (lora text-only 14/35) | ✅ OK — đây là caveat quan trọng nhất của slide và đã được ghi đúng chỗ |
| Notes: "Fix … 210 lượt: pi-mono mới 28/35 so với cũ 15/35 (p = 0,001) và base 20/35 (p = 0,0386); text-only 0/35 (C1 đạt); opencode 7/35, hermes 13/35" | `rebuild-fix-lora-tooluse/summary.json` + `summary.md:143,186` (new vs base p = 0,0386; new vs old p = 0,001) | ✅ OK |
| Notes: "Caveat: dữ liệu train là trace của đúng 35 bài đánh giá" | `rebuild-fix-lora-tooluse/data/sft_data.jsonl` (40 mẫu) + `dpo_pairs.jsonl` (9 cặp) — task_id đều thuộc 35 bài đánh giá | ✅ OK — caveat ô nhiễm đã được ghi, nhưng chỉ trong notes, không lên mặt slide |
| Notes: "G1 đạt — text-only pi-mono 0/15 (≤ 3/15)… G2 đạt — 13/15 so với 10/15 (McNemar p = 0,25…)" | `generalisation-check-2026-11-18/summary.md:139` | ✅ OK |

### Slide 17 — Phân tích sâu (khối Slide 17)

| Khẳng định | Nguồn | Kết quả |
|---|---|---|
| Hộp H3b: "Bước 2–3: H3b KHÔNG ủng hộ với LoRA vòng 2 (p = 0,0063; cả hai chạm sàn)" | Bước 2 p = 0,0063; bước 3 opencode 0/35 cả hai, hermes 0/35 vs 1/35 | ✅ OK |
| Hộp H3b: "Fix từ trace thật: H3b ủng hộ có điều kiện — 0/35, 28/35; bài mới 0/15, 13/15 (p = 0,25; n nhỏ)" | Như slide 16 | ✅ OK |
| "Cơ chế: dữ liệu sibling dạy viết code, không dạy hành vi tool" | Kết luận từ bước 2 + fix | ✅ OK — nhưng nay đã có con số tách hành vi/chất lượng (71%/29%) mà slide chưa có (xem B8) |
| Notes: "LoRA không dùng tool ở 14/35 bài so với base 4/35" | `rebuild-driver-2026-11-15/RESULTS.md:25,69,91` | ✅ OK |
| Notes: "opencode không-dùng-tool 35/35 cả hai; hermes 24/35 base, 29/35 LoRA" | `rebuild-driver-multiharness-2026-11-16/summary.json` (hermes base no_tool 24/35, lora 29/35; opencode 35/35 cả hai) | ✅ OK |
| Notes: "lần lật duy nhất là lcb_016" | `rebuild-driver-multiharness-2026-11-16/summary.md:41` (bảng flip hermes: chỉ lcb_016 FAIL→PASS; opencode không có flip nào) | ✅ OK |
| Notes: "Bảng 3 harness … ảnh 19 gói bằng chứng" | Ảnh `19_bang-ket-qua-3-harness.png` — không kiểm chứng bằng pixel trong audit này; notes ghi nguồn đếm là per-task `result.json` (tồn tại trong `rebuild-driver-2026-11-15/runs/*/result.json`) | ⚠️ **Không kiểm chứng được từ text** — số trong ảnh tin theo notes |
| Hai biểu đồ (a) cơ chế, (b) khi có ghi file | Ảnh `helix_khong_dung_tool.png`, `helix_pass_khi_ghi_file.png` — không kiểm chứng bằng pixel trong audit này | ⚠️ **Không kiểm chứng được từ text** |

## (B) Lỗi thời so với kết quả evolution (hoàn thành 18/11, sau lần đồng bộ deck)

Tổng số lượt chạy harness thật nay là **1.262** (555 cũ + 707 evolution: bước 1: 345, bước 3: 105, bước 4b: 135, bước 5: 32, bước 6: 90), không còn 555. Chi phí evolution +$6,00 (metered $18,7938 → $24,7943, billed $0,00 — `evolution-2026-11-18/billing-final.json`).

| # | Phát hiện evolution chưa có trên slide | Thuộc về | Trạng thái hiện tại trên deck |
|---|---|---|---|
| B1 | Gen mở rộng lên **n = 30** bài mới (held3 + held4): pi-mono G1+G2 đạt, **26/30 vs 17/30, p = 0,0039** (held4 riêng: 13/15 vs 7/15, p = 0,0312) — lần đầu đạt ý nghĩa thống kê | Slide 16 (bảng bài mới + hộp vàng) | Slide 16 chỉ có n = 15, p = 0,25. Con số mạnh nhất của nhóm (p = 0,0039) chưa lên slide |
| B2 | **Tổng record nhóm rút ra nay là 74, không phải 25**: fix rút thêm 40 SFT + 9 DPO từ trace thật | Slide 12 + 14 (hàng "Sibling record") | Ghi "25" — thiếu 49 record của fix |
| B3 | Adapter thứ 3 **`helix-lora-sftonly`** (bước 3) | Slide 12 (hàng "Train model") | Ghi "2 LoRA" — nay là 3 |
| B4 | **Mini-search đã chạy** (bước 6): 9 recipe, recipe tốt nhất cố định R4 7/10 vs baseline R0 6/10 (p = 1,0, nhiễu); mọi recipe dùng prompt opencode đều 0/10, mọi recipe dùng prompt pi đều 4–7/10; oracle post-hoc 8/10 | Slide 12 + 14 (hàng "Tìm kiếm harness") và slide 17 (cơ chế) | Ghi "Chưa chạy lại (không có lệnh search)" — nay sai. Phát hiện prompt (0/10 vs 4–7/10) là bằng chứng cơ chế mạnh nhất cho slide 17 nhưng chưa có |
| B5 | **Fixture v6 đã tái tạo** (94 thư mục thật) và đã đánh giá: base 0/16, realtool 1/16 (p = 1,0); 30/32 file là seed lỗi nguyên vẹn — thất bại không-tham-gia, kết quả hành vi không chuyển sang bài sửa lỗi | Slide 12 + 14 ("101 symlink gãy") và slide 17 (kết quả âm tính) | Ghi "101 symlink gãy" — nay sai về hiện trạng; kết quả âm tính v6 chưa có trên slide nào |
| B6 | **Tổng lượt chạy 1.262** (thay 555) | Slide 2 (lộ trình), 12, 14 | Mọi chỗ vẫn ghi 555 |
| B7 | **Base drift**: pi-mono base 25/35 (bước 2) → 20/35 (fix) → 22/35 (lặp lại bước 1) → 23/35 (ablation bước 3). Base tự trôi ±3 bài giữa các lần chạy cùng giao thức | Slide 15 (thẻ 15/35–25/35) + slide 16 (so với base 20/35) | Không nhắc tới trên mặt slide hay notes nào của slide 12–17. Điều này làm yếu mọi so sánh "mới vs base" dùng một lần chạy |
| B8 | **Tách hành vi/chất lượng** (bước 4a): tăng fix trên pi-mono +37,14pp = **71% hành vi / 29% chất lượng** (phụ thuộc thứ tự 71–82%, quan sát không nhân quả); 0/336 lượt không-ghi-file nào đậu | Slide 17 (cơ chế) | Slide 17 chỉ nói định tính ("dữ liệu sibling dạy viết code, không dạy hành vi tool") — chưa có con số tách |
| B9 | **Lặp lại xác nhận cả 4 phán quyết** (bước 1): C1 0/35, C2 29/35 vs 15/35 (p = 0,0005), G1 0/15 vs 5/15, G2 13/15 vs 9/15 (p = 0,2188). Lưu ý: nhánh cũ tự trôi (gen: cũ 10/15→9/15, text-only 3/15→5/15) | Slide 16 (xác nhận fix + gen) | Chưa có; slide 16 chỉ có số gốc (28/35, 13/15) |
| B10 | **Ablation SFT-only** (bước 3): base 23/35, SFT-only 30/35, realtool 25/35, p = 0,1797 — **không kết luận được**; phát hiện sạch: sửa hành vi không cần DPO | Slide 15–16 (vai trò DPO) | Chưa có; deck hiện không nói gì về việc DPO có thêm giá trị hay không (slide 15 chỉ ghi "DPO 3 bước" như một chi tiết train) |
| B11 | **Chẩn đoán harness** (bước 2): opencode text-only 169/185 do prompt + payload (prompt 8,9KB không hề nhắc công cụ sửa file); hermes 114/185 do model + prompt chung (41% "script fantasy"); shim là đường gọi tool duy nhất (429 call, 0 native) nhưng hiếm khi là nút thắt (4/310 lỗi parser) | Slide 17 (cơ chế) + slide 18 (hướng phát triển: "chẩn đoán phía harness" — nay đã làm xong) | Chưa có; slide 17 không giải thích *vì sao* opencode/hermes text-only |
| B12 | Caveat gộp n = 30: nhánh cũ tự trôi giữa hai cohort (10/15→7/15) nên biên rộng hơn của held4 một phần do nhánh so sánh trôi, không phải chỉ do nhánh mới tốt lên | Slide 16 (nếu thêm B1) | Chưa có — phải đi kèm B1 nếu đồng bộ, nếu không sẽ phóng đại |

Ngoài ra, slide 2 (lộ trình) bước 04 ghi "555 lượt" — cùng lỗi thời B6.

## (C) Mở rộng của nhóm còn yếu ở đâu — và cải tiến được gì

### C1. Các điểm yếu hiện tại (có bằng chứng)

| # | Điểm yếu | Bằng chứng |
|---|---|---|
| W1 | **Adapter fix không có đánh giá held-out sạch**: headline 28/35 và 0/35 đo trên đúng 35 bài mà adapter đã train (40 SFT: 24 train + 16 heldout2; 9 DPO: 5 train + 4 heldout2 — `rebuild-fix-lora-tooluse/data/sft_data.jsonl`, `dpo_pairs.jsonl`) | Slide 16 notes đã thừa nhận ("dữ liệu train là trace của đúng 35 bài đánh giá") nhưng chỉ trong notes |
| W2 | **Bằng chứng held-out sạch còn nhỏ và nhiễu**: gen held3 n = 15 (p = 0,25, không ý nghĩa); gộp n = 30 thì p = 0,0039 nhưng nhánh cũ tự trôi 10/15→7/15 giữa hai cohort | `generalisation-check-2026-11-18/summary.md:139`; `evolution-2026-11-18/step4b-gen-extension/combined_summary.md:7-10` |
| W3 | **Mỗi ô chỉ 1 lần chạy; base tự trôi ±3 bài** (25→20→22→23/35 trên pi-mono) nên mọi chênh lệch dưới ~5 bài đều nằm trong nhiễu | `rebuild-driver-2026-11-15/summary.json` (25/35); `rebuild-fix-lora-tooluse/summary.json` (20/35); `evolution-2026-11-18/step1-replication/summary.md:18` (22/35); `step3-sftonly-ablation/summary.md:5` (23/35) |
| W4 | **Sửa hành vi không chuyển sang opencode/hermes ở mức G1**: gen mới text-only vẫn 10/15 (opencode) và 6/15 (hermes); gộp n = 30 thì G1 ngoài pi-mono KHÔNG đạt | `generalisation-check-2026-11-18/summary.json`; `evolution-2026-11-18/step4b-gen-extension/RESULTS.md` |
| W5 | **Không chuyển sang bài sửa lỗi (v6)**: base 0/16, realtool 1/16; 30/32 file là seed lỗi nguyên vẹn — model không đọc/sửa file | `evolution-2026-11-18/step5-v6-fixtures/RESULTS.md:36`; `summary.md:7,14-15` |
| W6 | **Giá trị của DPO chưa chứng minh được**: SFT-only 30/35 > realtool (SFT+DPO) 25/35, p = 0,1797; trước đó bổ sung hàng 5 (DPO 6→19 cặp) cũng không tăng Pass@1 (65/80; 51/60) | `evolution-2026-11-18/step3-sftonly-ablation/RESULTS.md:13-15,48`; slide 18 notes (hàng 5) |
| W7 | **Một model 7B, một recipe, một kiểu bài**: toàn bộ bằng chứng là Qwen2.5-Coder-7B-Instruct, r=16/α=32, bài LeetCode-style tự viết, test assert | Toàn bộ summary.json các đợt |
| W8 | **Chưa đo chất lượng code khi đã ghi file một cách độc lập**: tách 71%/29% là quan sát, không nhân quả; chưa có đo chất lượng code (độ đúng, độ gọn) tách khỏi hành vi | `evolution-2026-11-18/step4a-decomposition/DECOMPOSITION.md:38-39` |

### C2. Lựa chọn cải tiến (mỗi lựa chọn: làm gì — nỗ lực — chi phí ước tính — khẳng định mới được phép nói)

Cơ sở giá: evolution 707 lượt GPU + 2 lần train = +$6,00 metered (`billing-final.json`: $18,7938 → $24,7943, billed $0,00). Tức khoảng **$0,007–0,009/lượt** gồm deploy; một lần train LoRA nhỏ khoảng $0,50–0,80 (bước 3: train + 105 lượt = $1,20). Ngân sách evolution $10 còn $4. **Tất cả lựa chọn GPU dưới đây đều cần Triệu cấp lại token Modal trong trình duyệt trước (token hết hạn 19/11 10:25 +07) và cần cậu duyệt riêng — KHÔNG được tự chạy.**

| # | Cải tiến | Nỗ lực | Chi phí ước tính | Khẳng định mới được phép nói |
|---|---|---|---|---|
| O1 | **Lặp lại các ô then chốt để đo phương sai**: chạy lại pi-mono fix (base + realtool × 35 bài) thêm 2 lần + gen pi-mono (3 nhánh × 30 bài) thêm 1 lần = 230 lượt | GPU nhỏ (dùng lại `run_driver.py`, không code mới) | ~$1,80–2,10 | "28/35 và 13/15 giữ được trong khoảng X–Y qua 3 lần chạy; base trôi ±Z bài" — thay câu "mỗi ô 1 lần chạy" bằng một dải tin cậy thật |
| O2 | **Train lại adapter fix sạch (chỉ từ 20 bài train) rồi đánh giá trên 45 bài chưa thấy**: dùng lại 24 SFT + 5 DPO thuộc bài train trong `data/` (không cần rút dữ liệu mới), train lại, đánh giá base vs adapter-sạch trên heldout2 (15) + held3 (15) + held4 (15), chỉ pi-mono = 90 lượt | GPU vừa (1 lần train + 90 lượt; cần DESIGN đăng ký trước) | ~$1,60–1,90 | "Fix khái quát hóa sang bài chưa thấy: X/45 vs base Y/45" — bỏ được caveat ô nhiễm W1, điểm yếu lớn nhất |
| O3 | **Can thiệp prompt opencode theo chẩn đoán bước 2**: thêm 1 dòng nêu rõ công cụ sửa file vào prompt opencode (recipe mới qua `runner.mts` đã có từ bước 6), chạy 2 recipe × 10 bài = 20 lượt | GPU rất nhỏ (code đã có, chỉ thêm recipe) | ~$0,20–0,30 | "Text-only opencode giảm từ 10/15 xuống X/10 khi prompt nêu tên tool" — biến chẩn đoán thành phát hiện cơ chế thứ hai, trực tiếp sửa W4 |
| O4 | **Mở rộng gen thêm 15 bài mới (held5)**: viết + kiểm tra test trước GPU (offline, nặng nhất là công viết bài), rồi 135 lượt (3 nhánh × 3 harness) | Offline nặng (viết/kiểm tra bài) + GPU nhỏ | ~$1,20 (GPU) | "Gộp n = 45: 26+X/45 vs 17+Y/45, p = …" — khoảng tin cậy hẹp hơn, giảm phụ thuộc vào một cohort |
| O5 | **Theo dõi v6: thử prompt pi-mono trên fixture sửa lỗi** — chạy realtool + base trên 16 fixture v6 bằng recipe pi-prompt (đã có) thay vì prompt mặc định, 32 lượt | GPU rất nhỏ | ~$0,25–0,30 | "Thất bại v6 là do prompt hay do bản chất bài sửa lỗi" — làm rõ W5 thay vì để một kết quả âm tính chưa giải thích |
| O6 | **Đồng bộ evolution vào deck (offline, $0)**: thêm B1, B4, B8, B9, B10, B11 vào slide 16–17 và sửa các số lỗi thời B2/B3/B5/B6/B7 | Offline (sửa `build_helix_filled_dark.py`, không chạy GPU) | $0 | Không cần khẳng định mới — chỉ làm deck đúng với bằng chứng đã có; **nên làm trước mọi lựa chọn GPU** |
| O7 | **Phân tích offline từ dữ liệu đã có ($0)**: tính tỉ lệ đậu khi-có-ghi-file trên toàn bộ 1.262 lượt (thay vì chỉ 555) + tỉ lệ đậu theo độ khó trên held3+held4 | Offline (script phân tích trên summary.json đã có) | $0 | "Khi đã ghi file, LoRA mới đậu X% trên 1.262 lượt" — củng cố tách hành vi/chất lượng mà không tốn GPU |

**Không khuyến nghị**: vòng 3 / model lớn hơn / benchmark 6.500 lượt của tác giả / thêm cặp DPO khi chưa có giả thuyết (bước 3 + hàng 5 đã cho thấy DPO không thêm giá trị trong thiết kế hiện tại) / bất kỳ lựa chọn nào "làm đẹp" số bằng cách chọn lại nhánh so sánh hay gộp test sau khi thấy kết quả.

### C3. Xếp hạng theo giá trị/nỗ lực cho bài thuyết trình trên lớp

Thầy chấm theo mạch gap → RQ → phương pháp → thực nghiệm → kết quả → kết luận, và đánh giá cao kết quả âm tính trung thực. Thứ tự nên làm:

1. **O6 — Đồng bộ evolution vào deck ($0, làm ngay)**: giá trị cao nhất trên mỗi công sức. Deck hiện thiếu chính con số mạnh nhất (p = 0,0039) và còn ghi sai 3 chỗ (2 LoRA, "chưa search", "101 symlink gãy"). Không cần Triệu cấp token.
2. **O3 — Can thiệp prompt opencode (~$0,25, GPU rất nhỏ)**: rẻ nhất trong các lựa chọn GPU mà cho ra một phát hiện cơ chế mới, nối thẳng chẩn đoán bước 2 → sửa được → đo lại. Đúng mạch luận cứ → giả thuyết → thước đo của thầy, và sửa điểm yếu W4 ngay trên slide 17.
3. **O2 — Adapter fix sạch (~$1,80, GPU vừa)**: đắt hơn nhưng xử lý đúng điểm yếu lớn nhất (W1 — headline 28/35 đang đo trên bài đã train). Nếu chỉ được chọn một thí nghiệm GPU thì chọn cái này, vì nó thay đổi được câu kết luận của RQ3 từ "ủng hộ có điều kiện" thành "ủng hộ trên bài chưa thấy".
4. **O1 — Lặp lại ô then chốt (~$2,00)**: nên làm sau O2 (hoặc gộp chung một đợt deploy để tiết kiệm phí deploy). Một mình O1 chỉ thu hẹp nhiễu, không sửa được caveat ô nhiễm.
5. **O4/O5 — tùy ngân sách còn lại**: O4 tăng n lên 45 (tốt cho độ tin cậy, nhưng công viết bài nặng); O5 làm rõ kết quả âm tính v6 (tốt cho phần giới hạn, nhưng là nhánh phụ).

Tổng chi phí nếu làm O2 + O3 + O1 gộp: khoảng **$3,50–4,20**, vừa trong $4 còn lại của ngân sách evolution — nhưng vẫn cần Triệu duyệt ngân sách mới + cấp lại token Modal trước, vì ngân sách $10 đó là của chương trình evolution đã kết thúc.

## (D) Kết luận

**Phần thực nghiệm/kết quả trên slide 12–17 về cơ bản là chắc chắn**: mọi số headline kiểm tra được đều khớp với `summary.json` / `RESULTS.md` (555 lượt, 28/35 vs 15/35 p = 0,001, 13/15 vs 10/15 p = 0,25, 15/35 vs 25/35 p = 0,0063, 14/35 vs 4/35 text-only, 66/80 và 53/60 vòng 2), số phía paper đối chiếu đúng với arXiv HTML v1 (6.500 / 3.000 / 550 / 438 / 96 cổng), và các caveat quan trọng (n = 15, p = 0,25, mỗi ô 1 lần chạy, train trên đúng 35 bài đánh giá) đã được ghi — phần lớn trong notes, một phần trên mặt slide. Không phát hiện số nào sai hẳn; các flag chỉ là: 1 nhãn gây hiểu lầm (thẻ "0/35 → 0/15" slide 16), 1 thẻ thiếu tên harness (slide 15), 2 chi tiết không đối chiếu lại được ("4 bài" temp 0,7; số trong ảnh 19 và biểu đồ slide 15), và phép so sánh "25 vs 438 record" chưa ghi rõ cách đếm.

**Vấn đề lớn nhất không phải số sai, mà là lỗi thời**: deck dừng ở 18/11 trước khi evolution xong, nên thiếu con số mạnh nhất (gộp n = 30, p = 0,0039), thiếu 3 phát hiện cơ chế (chẩn đoán harness, tách 71%/29%, mini-search prompt 0/10 vs 4–7/10), thiếu ablation SFT-only, và còn ghi sai 3 chỗ (2 LoRA thay vì 3; "chưa chạy search"; "101 symlink gãy"). Ngoài ra **base drift (25→20→22→23/35) không xuất hiện ở đâu**, dù nó làm yếu mọi so sánh một-lần-chạy với base.

**Mắt xích yếu nhất: W1 — headline của fix (28/35, 0/35) đo trên chính 35 bài mà adapter đã train.** Gen n = 30 là bằng chứng sạch duy nhất, nhưng nhỏ và nhánh so sánh tự trôi. Muốn câu chuyện mạnh lên thật thì làm O2 (adapter sạch, ~$1,80) sau khi làm O6 (đồng bộ deck, $0) và O3 (prompt opencode, ~$0,25). Không cần vòng 3, không cần model lớn hơn.
