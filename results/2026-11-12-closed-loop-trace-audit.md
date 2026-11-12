# Kiểm tra chéo trace closed-loop (2026-11-12)

Ngày kiểm tra: 2026-11-12. Nguồn: fork `Vietng-XPrince7/HELIX`, commit
`cc44b7b7cafa9352f51d4e2b65f9a002c892e8b7`, thư mục `closed-loop/`.
Phương pháp: chỉ đọc file đã commit và chạy lại verifier sandbox trên máy
cục bộ, không gọi model, không dùng API key, không tốn chi phí inference.
Đây là kiểm tra chéo offline, cùng phạm vi với repo này; phần chạy live và
train lại thuộc về fork (xem runbook trong fork).

## Câu hỏi kiểm tra

Commit `a090aba` của fork ghi "finish 40 live runs on modal vllm" và
`REBUILD_REPORT.md` (bản trước 12/11) trình bày BUILD như 40 lượt chạy live.
Kiểm tra này đối chiếu lời ghi đó với chính nội dung 80 trace đã commit.

## Phương pháp

1. Đọc toàn bộ 80 file `data/raw_traces/*.json`: `timestamp`,
   `latency_sec`, `steps`, `raw_helix_transcript`, `model`, `passed`,
   `assistant_solution`, và sự có mặt của trường `test_result`/`mode`.
2. So sánh từng `assistant_solution` của BUILD với bảng đáp án viết tay
   `_DRY_RUN_SOLUTIONS` trong `closed-loop/scripts/02_run_helix_eval.py`
   (so khớp từng ký tự sau khi bỏ fence ```python).
3. Chạy lại toàn bộ 80 solution qua đúng hàm `run_test_cases` của runner
   (subprocess sandbox, timeout 5 giây/bài) và đối chiếu cờ `passed`.
4. Đối chiếu từng record trong `sft_data.jsonl`/`dpo_pairs.jsonl` với trace
   nguồn theo `(task_id, harness)` để xác định record nào lấy từ trace live,
   record nào lấy từ trace dry-run.

## Kết quả 1: BUILD chỉ có 9 live + 31 dry-run

| Nhóm trace | Số lượng | Bằng chứng |
| --- | --- | --- |
| Live | 9 | `lcb_001` × 4 harness, `lcb_002` × 4, `lcb_003` minimal. Timestamp 18:32:21–18:39:13 UTC ngày 28/10/2026, giãn cách theo latency; transcript 1–5 bước; latency 3,3–118,0 giây, khác nhau từng lượt. |
| Dry-run mock | 31 | `lcb_003` pi-mono/hermes/opencode + `lcb_004`–`lcb_010` × 4. Toàn bộ ghi trong ~1,3 giây (18:30:49.13–18:30:50.46 UTC), cách nhau ~40 ms; transcript rỗng; latency và steps đúng y hệt hằng số mock trong `_dry_run_solution` (opencode 1,2 s/1 bước; hermes-agent 2,1 s/2; pi-mono 3,4 s/3; minimal 5,8 s/5); solution giống từng ký tự với đáp án viết tay trong script. |

Cả 31 trace dry-run đều không có trường `mode` và `test_result` (hai trường
này chỉ xuất hiện ở các commit sau). REBUILD thì khác: cả 40 trace đều có
transcript, latency 4,1–157,9 giây, ghi trong 29 phút ngày 29/10/2026,
model `helix-lora`, không trace nào trùng đáp án dry-run — phù hợp với chạy
live thật, nhưng chưa đủ để kết luận độc lập về việc adapter có được serve
đúng hay không (không có log health-check/inference trong repo).

## Kết quả 2: dữ liệu train chủ yếu lấy từ code viết tay

Script trích xuất cũ chọn, mỗi task, trace đạt có ít bước nhất. Trace
dry-run của OpenCode luôn ghi 1 bước nên luôn thắng:

- SFT (9 record): 8/9 lấy từ trace dry-run của OpenCode; chỉ `lcb_001`
  lấy từ trace live.
- DPO (8 cặp): cả 8 `chosen` lấy từ trace dry-run của OpenCode; 7/8
  `rejected` cũng dry-run (chỉ `rejected` của `lcb_003`, từ trace live
  của Minimal, là output thật của model).

Chạy lại script trích xuất sau khi thêm guard live-only (xem dưới) trên
đúng dữ liệu đã commit cho ra **1 record SFT và 0 cặp DPO** — đó là kích
thước thật của tập dữ liệu live đã kiểm chứng được. Không đủ để train;
BUILD cần chạy lại live toàn bộ trước khi train lại.

## Kết quả 3: cờ `passed` và số học trong báo cáo đều đúng

- Chạy lại sandbox trên 80 solution: **0 lệch** so với cờ `passed` đã ghi.
  Verifier chấm đúng; vấn đề nằm ở nguồn gốc trace và ở việc train trùng
  với eval, không nằm ở khâu chấm.
- Bảng §3 của `REBUILD_REPORT.md` khớp đúng từng con số với trace: Minimal
  30% → 60%; Pi/Hermes/OpenCode 90% → 70%; gap 60 điểm → 10 điểm.
- Hạn chế diễn giải: REBUILD đánh giá đúng 10 bài đã train; 3 bài Minimal
  chuyển FAIL → PASS (`lcb_004`, `lcb_006`, `lcb_010`) đều có đáp án trong
  file SFT. Kết quả này chứng minh adapter dùng được đáp án đã train, chưa
  chứng minh khái quát hoá. Paper HELIX §9.3 cũng yêu cầu tách task
  evolution và task đánh giá cuối; §4.3 yêu cầu không để sibling group rò
  rỉ qua ranh giới train/dev.
- Hạn chế về harness: 4 "harness" trong runner chỉ là 4 system prompt khác
  nhau + vòng lặp chat gọi trực tiếp API OpenAI-compatible, có phản hồi lỗi
  test cho 3 harness nâng cao. Runner không gọi CLI HELIX, không dùng
  recipe đã assemble, không có tool/session/permission thật. Kết quả so
  sánh scaffold prompt, không phải so sánh harness HELIX đã assemble.

## Việc đã làm sau kiểm tra (trong fork, branch riêng)

1. Runner `02_run_helix_eval.py` ghi thêm trường `"mode": "live"|"dry-run"`
   cho mọi trace; thêm `--problem-set {train,heldout}` và
   `--phase heldout` (bắt buộc chỉ rõ `--model`).
2. Thêm `data/heldout_problems.json`: 10 bài mới (`held_001`–`held_010`,
   4 dễ / 6 trung bình), ID không trùng task train, test case đã kiểm chứng
   bằng đáp án tham chiếu chạy offline (đáp án tham chiếu không commit).
3. Script trích xuất `03_extract_pairs.py` mặc định chỉ lấy trace live;
   trace dry-run bị bỏ qua và được liệt kê; `--allow-dry-run` chỉ dùng cho
   smoke test, cấm train trên output đó; record trích xuất ghi thêm tên
   file trace nguồn.
4. `REBUILD_REPORT.md`/`README.md` trong fork đã thêm hộp hiệu chỉnh, sửa
   số mẫu cho khớp §3, bỏ khẳng định "ít token hơn 60% / nhanh gấp 2 lần"
   (không có số liệu token; latency REBUILD thực tế tăng lên).
5. Thêm `PROVENANCE_AUDIT.md` (bản tiếng Anh của kiểm tra này, trong fork)
   và `HELDOUT_RUNBOOK.md` (lệnh chạy lại BUILD live, train lại, đánh giá
   held-out, kèm lệnh kiểm chứng sau mỗi bước).

## Phần còn thiếu (cần Modal, không làm offline được)

1. Chạy lại BUILD live đủ 40/40 trên model gốc, kiểm chứng 40 trace đều
   `mode: live` và có transcript.
2. Trích xuất lại live-only, train lại, và commit `loss_history.json`
   (hoặc run-id + loss từng stage) để run train kiểm chứng được từ repo.
3. Chạy lại REBUILD live và đánh giá held-out cho cả model gốc lẫn LoRA;
   báo cáo số held-out tách riêng với số trên task train, kèm bảng từng
   bài (n=10 mỗi harness, một bài = 10 điểm, không phóng đại chênh lệch
   nhỏ).
4. Sửa câu chữ "40 live runs" trong slide, kịch bản thuyết trình và báo cáo
   văn bản cho khớp với hiệu chỉnh trên.

## Diễn giải đúng

Kiểm tra này **không** kết luận nhóm không train model (script train là
thật, adapter có tồn tại ngoài repo), và **không** kết luận số REBUILD bịa
đặt (verifier chấm đúng, trace REBUILD phù hợp với chạy live). Kết luận
đúng là: baseline BUILD bị trộn mock/live, dữ liệu train chủ yếu là code
viết tay, và đánh giá chưa có held-out — nên mức tăng của Minimal chưa
được chứng minh là khái quát hoá. Các bản sửa trong fork ngăn việc trộn
lẫn tái diễn; phần chạy live còn lại cần làm theo runbook mới gỡ được
các hạn chế này.
