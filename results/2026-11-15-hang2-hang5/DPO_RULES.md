# Luật trích cặp DPO mở rộng — đợt bổ sung hàng 2+5 (HELIX)

Ngày viết: 2026-11-15. Trạng thái: đăng ký trước (pre-registered) — luật này
được viết TRƯỚC khi trích, và script trích (`extract_dpo_expanded.py`) chỉ
được phép thực thi đúng luật này. Không nới lỏng luật sau khi thấy số lượng.
Nếu luật cho dưới 15 cặp thì báo cáo thiếu hụt đúng như vậy, không bù bằng
cách nới cap hay thêm nguồn.

Đợt này gọi là **"đợt bổ sung hàng 2+5"**, KHÔNG gọi là vòng 3. SFT giữ
nguyên 19 mẫu của vòng 2 — không trích lại SFT, không sửa SFT.

## 0. Cổng provenance (bắt buộc, chạy trước mọi trích xuất)

Không cặp nào được trích nếu bất kỳ kiểm tra nào dưới đây thất bại.
Script trích phải dừng (abort) thay vì trích một phần.

1. **Đọc `data/processed/provenance.json` hiện tại** và xác nhận:
   `allow_dry_run == false`, `run_tag_filter == ["build2"]`,
   `live_traces_kept == 160`, và SHA-256 trong manifest khớp với hai file
   `sft_data.jsonl` / `dpo_pairs.jsonl` đang có (tính lại hash, không tin
   con số trong manifest một cách mù quáng). SFT kỳ vọng 19, DPO cũ 6.
2. **Tự suy ra lại tập trace đủ điều kiện** từ `data/raw_traces/` bằng
   đúng logic của `03_extract_pairs.py` (dùng lại hàm `is_dry_run_trace`
   và `_heldout_task_ids` của script đó, không viết lại logic phân loại):
   chỉ lấy trace có `phase == "build"`, `run_tag == "build2"`, không phải
   dry-run, và `task_id` không thuộc bất kỳ tập held-out nào
   (`heldout_problems.json`, `heldout2_problems.json`). Kỳ vọng: đúng 160
   trace, 0 dry-run, 0 trace mang ID held-out.
3. **Mọi trace ngoài tập trên đều bị loại**, không có ngoại lệ: trace
   rebuild, trace heldout, trace vòng 1 (không tag), trace dry-run/mock,
   trace demo, solution tham chiếu viết tay, code do người viết thêm.
   Cả `chosen` lẫn `rejected` đều phải là output nguyên văn của model
   (xem §3), không bao giờ chỉnh sửa.
4. Script phải in và ghi vào audit: số trace quét, số trace đủ điều kiện,
   số trace dry-run bị loại (kỳ vọng 0 trong `build2`), số trace held-out
   bị chặn (kỳ vọng 0), và kết quả kiểm tra hash manifest.

## 1. Nguồn và phạm vi

- Nguồn duy nhất: 160 trace `build2` (80 baseline nhiệt độ 0.0 + 80
  sampling nhiệt độ 0.7 trên `minimal`/`opencode`). Trace sampling là
  live và đã thuộc phạm vi trích của vòng 2, nên được dùng như trace
  baseline, không phân biệt đối xử theo nhiệt độ trong luật chọn
  (§2–§3). Nhiệt độ và chỉ số mẫu được ghi lại trong mỗi cặp để đối
  chiếu, giống schema cũ.
- Không trộn vòng: không dùng trace vòng 1, không dùng trace rebuild2 /
  heldout2 làm nguồn train dưới bất kỳ hình thức nào (kể cả làm
  `rejected`).
- Không dùng nhãn heuristic hay nhãn judge để chọn/loại cặp DPO. Việc
  chọn cặp chỉ dựa trên flag `passed` đã re-verify của vòng 2 và code
  trong trace. (Nhãn critic là phân tích hàng 2, độc lập với train.)

## 2. Luật A — cặp sibling cùng task (mở rộng, có cap)

**Định nghĩa:** trong cùng một `task_id`, một cặp (chosen, rejected) với
chosen là solution của một trace PASS, rejected là solution của một trace
FAIL khác (harness này đỗ + harness kia trượt, hoặc hai mẫu sampling
khác nhau của cùng harness — khác trace là đủ, không yêu cầu khác
harness). Đây là mở rộng của Case 1 ("correctness_contrast") của
`03_extract_pairs.py`, khác ở chỗ: **tối đa 3 cặp mỗi task** thay vì 1,
và thứ tự chọn là xác định hoàn toàn (không phụ thuộc thứ tự glob).

**Ứng viên thô:** mọi cặp (trace PASS, trace FAIL) cùng task, cả hai đều
có `assistant_solution` không rỗng. Loại ngay ứng viên có text chuẩn hóa
của chosen bằng text chuẩn hóa của rejected (chuẩn hóa = strip + gộp mọi
dãy whitespace thành một khoảng trắng; so sánh này mạnh hơn `.strip()`
của script cũ và bao hàm yêu cầu `chosen != rejected` của `04`).

**Thứ tự sắp xếp ứng viên (xác định, dùng để chọn):** sắp xếp theo khóa
(chosen_steps tăng dần, chosen_latency_sec tăng dần, rejected_steps giảm
dần, rejected_latency_sec giảm dần, chosen_source_trace tăng dần,
rejected_source_trace tăng dần). Khóa này ưu tiên chosen ít bước nhất
(giống script cũ) và rejected nhiều bước nhất (giống script cũ), phá
tie bằng latency rồi tên file để hai lần chạy cho cùng một kết quả.

**Chọn tham lam tối đa phủ (greedy coverage), cap 3/task:** duyệt ứng
viên theo thứ tự trên; lấy một ứng viên nếu (a) text chuẩn hóa của
chosen chưa từng được dùng cho task này, HOẶC (b) mọi text chosen phân
biệt của task đã được dùng hết và text chuẩn hóa của rejected chưa từng
được dùng cho task này; dừng khi đủ 3 cặp cho task. Mục đích: không để
một solution chosen duy nhất chiếm toàn bộ cặp của task khi còn chosen
khác, và không lặp lại cùng một rejected khi còn rejected khác.
Cap 3/task là giới hạn a priori: giữ mỗi task ≤ ~16% tập DPO (khi tổng
~19 cặp) và tránh nhân bản quá mức một chosen đơn lẻ.

**Loại trừ ghi vào audit:** mọi ứng viên thô không được chọn đều ghi một
dòng với lý do `cap_or_coverage` (không được chọn bởi luật tham lam/cap)
hoặc `identical_text` (chosen trùng rejected sau chuẩn hóa).

**Task không có tương phản:** task toàn PASS (không có trace FAIL) hoặc
toàn FAIL (không có trace PASS) cho 0 cặp theo luật A — ghi rõ lý do
`no_contrast_all_pass` / `no_contrast_all_fail` trong audit theo task.
Không "chế" tương phản từ task toàn PASS bằng luật hiệu suất (xem §5).

## 3. Luật B — cặp fail→fixed trong cùng một trace (qua các bước feedback)

**Định nghĩa:** trong một trace `build2` duy nhất có `steps >= 2` và
`passed == true`, rejected là code ở một bước trung gian đã được xác
minh là FAIL, chosen là solution cuối cùng (PASS) của chính trace đó.
Cặp này ghi lại đúng chuyển đổi fail→fixed mà harness feedback tạo ra.

**Điều kiện đủ điều kiện (tất cả đều bắt buộc):**

1. Trace thuộc tập đủ điều kiện ở §0, `passed == true`, `steps >= 2`,
   và `len(raw_helix_transcript) == steps`.
2. Code ở mỗi bước trung gian được trích bằng đúng hàm
   `extract_python_code` của `02_run_helix_eval.py` (không viết lại
   logic trích). Bước không trích được code thì bỏ qua (không phải ứng
   viên rejected).
3. Mỗi code trung gian được **chạy lại sandbox** bằng đúng hàm
   `run_test_cases` của `02` với test cases của task đó (timeout 5s
   như script gốc). Chỉ code nào sandbox trả về FAIL mới đủ điều kiện
   làm rejected. Không suy luận "bước trung gian chắc chắn fail" từ
   ngữ nghĩa vòng lặp — phải chạy thật.
4. Rejected được chọn là code của **bước FAIL cuối cùng** (chỉ số bước
   cao nhất < bước cuối mà sandbox xác minh FAIL) — tương phản gần nhất
   với bản fixed, nhiều thông tin nhất. Nếu một bước trung gian sandbox
   trả về PASS thì bước đó không đủ điều kiện (và nếu không còn bước
   FAIL nào thì trace cho 0 cặp).
5. Text chuẩn hóa của rejected khác text chuẩn hóa của chosen (code
   cuối). Nếu trùng thì 0 cặp.
6. Tối đa **1 cặp mỗi trace**.

**Text ghi vào cặp:** chosen = `assistant_solution` nguyên văn của trace;
rejected = code trung gian được bọc đúng định dạng của `save_trace`:
`"```python\n" + code + "\n```"`. Prompt = `prompt` của trace. Ghi thêm
`rejected_step` (chỉ số bước 1-based trong transcript) và
`rejected_source_trace` = cùng tên file trace (cả chosen lẫn rejected
cùng một nguồn — đây là điểm khác luật A, phải ghi rõ).

**Lưu ý về điều kiện sinh rejected (ghi nhận trung thực):** code trung
gian được sinh ra trong ngữ cảnh có feedback lỗi test của các bước
trước, trong khi trường `prompt` của cặp DPO là prompt gốc của task
(theo đúng quy ước của script cũ: prompt lấy từ trace của chosen).
Sự lệch ngữ cảnh này là có thật và được ghi nhận ở đây; nó cũng đúng
với mọi cặp DPO từ trace nhiều bước trong pipeline này, và là lý do
luật B bị cap 1 cặp/trace thay vì lấy mọi bước trung gian.

**Loại trừ ghi vào audit:** mỗi trace `build2` có `steps >= 2` đều có
một dòng disposition: `selected` (kèm step), `final_not_passed`,
`no_failing_intermediate`, `no_intermediate_code`, hoặc
`identical_text`. Trace 1 bước không cần dòng disposition (không có
bước trung gian theo định nghĩa).

## 4. Định dạng file đầu ra và kiểm tra cuối

- File: `dpo_pairs_expanded.jsonl`, một cặp một dòng JSON, schema mirror
  schema cũ của `dpo_pairs.jsonl` cộng thêm trường phân biệt luật:
  `task_id`, `preference_type` (`"correctness_contrast"` cho cả hai luật
  — cả hai đều là tương phản đúng/sai), `extraction_rule`
  (`"A_sibling"` hoặc `"B_fail_to_fixed"`), `pair_id` (duy nhất, dạng
  `A-<task>-<n>` / `B-<task>-<n>`), `system`, `prompt`, `chosen`,
  `rejected`, `chosen_harness`, `rejected_harness`, `chosen_steps`,
  `rejected_steps`, `chosen_source_trace`, `rejected_source_trace`,
  `chosen_temperature`, `chosen_sample_index`, `rejected_temperature`,
  `rejected_sample_index`, `run_tag`, và riêng luật B thêm
  `rejected_step`.
- Sắp xếp file: theo (`task_id`, `extraction_rule`, `pair_id`) để ổn
  định giữa các lần chạy.
- Kiểm tra cuối (script phải thực hiện và in kết quả, dừng nếu lỗi):
  mọi cặp có đủ 4 trường text không rỗng (`system`, `prompt`, `chosen`,
  `rejected`); `chosen != rejected` (so sánh thô, như validator của
  `04`); không trùng lặp cặp theo (task_id, norm(chosen),
  norm(rejected)); không `task_id` nào thuộc tập held-out; mọi
  `*_source_trace` đều là file có trong tập đủ điều kiện §0; đếm cặp
  theo luật và theo task khớp với audit.
- Đối chiếu với DPO cũ: đếm số cặp cũ (6 cặp trong
  `data/processed/dpo_pairs.jsonl`) còn xuất hiện nguyên văn (cùng task,
  cùng chosen/rejected thô) trong file mới; ghi con số vào audit. File
  mới THAY THẾ file cũ cho đợt bổ sung — không yêu cầu giữ nguyên 6 cặp
  cũ, nhưng độ chồng lấp phải được báo cáo.
- Kèm theo file `dpo_extraction_audit.json`: cổng provenance (§0), bảng
  theo task (số trace, số PASS/FAIL, số ứng viên thô luật A, số cặp đã
  chọn theo luật, lý do 0 cặp nếu có), danh sách đầy đủ ứng viên luật A
  bị loại + lý do, disposition luật B cho mọi trace nhiều bước, kết quả
  kiểm tra cuối, và SHA-256 của file JSONL đầu ra.

## 5. Những gì KHÔNG làm (đã quyết trước, không thay đổi khi trích)

- **Không trích lại SFT.** SFT giữ nguyên 19 mẫu vòng 2, hash
  `4f4d6ad8…`. Bất kỳ worker GPU nào cũng phải train với đúng file SFT
  đó (xem `GPU_RUN_PLAN.md` về staging + manifest).
- **Không dùng luật efficiency_contrast (Case 2 của script cũ).** Luật
  đó chỉ kích hoạt khi task không có trace FAIL nào và đối chiếu hai
  solution cùng PASS theo số bước — không phải tương phản đúng/sai, và
  với cap 4 bước + đa số trace PASS ở 1 bước, tín hiệu của nó gần như
  không có. Script trích mới không trích cặp efficiency nào; số cặp
  efficiency theo luật cũ (kỳ vọng 0) được tính riêng để báo cáo, không
  đưa vào file DPO.
- **Không dùng bước trung gian của trace FAIL làm rejected cho chosen
  sibling.** Cả hai đầu đều fail (bước trung gian) hoặc lệch ngữ cảnh
  feedback mà không có tương phản đúng/sai trong cùng trace — không đủ
  điều kiện theo §2 hay §3. Đã cân nhắc và loại trừ có chủ đích.
- **Không dùng trace rebuild/heldout, không dùng solution tham chiếu,
  không sửa text solution, không nới cap để đạt số lượng.** Mục tiêu
  15–30 cặp là mục tiêu, không phải hạn ngạch: nếu luật cho ít hơn 15,
  báo cáo đúng số đó và dừng.
