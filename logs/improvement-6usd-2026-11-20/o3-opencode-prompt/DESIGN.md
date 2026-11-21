# DESIGN — O3: Can thiệp prompt opencode theo chẩn đoán bước 2 (kiểm chứng F1 thu nhỏ)

Ngày viết: 2026-11-20. Thiết kế đăng ký trước (pre-registered) TRƯỚC khi chạy bất kỳ lệnh GPU nào.
Chương trình: cải thiện HELIX $6 (ngân sách còn lại ~$6,00 credit, tài khoản $30).
Người duyệt thiết kế: Triệu (chưa duyệt chạy — chỉ duyệt thiết kế thì mới được chạy).

## 0. Vấn đề (đã xác minh — chẩn đoán bước 2, DIAGNOSIS.md)

- Opencode text-only 169/185 (91,4%) — nguyên nhân chính (b): prompt hệ thống
  ~8,9KB **không hề nhắc tới công cụ sửa file**, đồng thời "mồi" trả lời ngắn
  dạng chat (quy tắc <4 dòng, ví dụ Q&A trả `4`, `ls` bằng text; dòng "answer
  their question first, and not immediately jump into taking actions") +
  12 tool không có schema tham số.
- Mini-search bước 6 (90 lượt, base cố định, 10 bài): cả 4 recipe dùng prompt
  opencode đều **0/10, text-only 40/40**; cả 4 recipe dùng prompt pi đều
  4–7/10. Cơ chế ĐẰNG SAU hiệu ứng prompt (dài vs nội dung vs schema) chưa
  tách được — bước 6 nói rõ không được kết luận "prompt opencode quá dài".

## 0.1 Đính chính baseline (quan trọng — đọc kỹ trước khi chạy)

Bản giao việc ban đầu viết "baseline R0 0/10" — **SAI**. Đối chiếu lại
`step6-mini-search/RESULTS.md` §2: **R0 (pi-mono stock) đạt 6/10** trên
10 bài này. Baseline 0/10 đúng cho can thiệp này là các recipe dùng prompt
opencode: **R2 = R5 = R6 = R8 = 0/10, text-only 10/10**. Baseline chính dùng
ở đây là **R8** (blend toàn-opencode: prompt/tools/turn opencode — ngăn xếp
opencode đầy đủ nhất trong khung blend). Mọi so sánh trong thiết kế này
đều đối chiếu với R8, không phải R0. Nếu ai viết "R0 0/10" ở đâu thì sửa.

## 1. Giả thuyết

**H-opencode:** Thêm một chỉ dẫn tường minh về công cụ sửa file vào prompt
người dùng (user prompt) sẽ cứu được hành vi dùng tool trên ngăn xếp
opencode — tức text-only giảm mạnh và Pass@1 tăng khỏi sàn — vì nguyên nhân
theo chẩn đoán là model không được bảo phải dùng tool, chứ không phải model
không biết dùng tool.

## 2. Can thiệp — 2 mức liều + 1 nhánh đối chứng (viết trước, nguyên văn)

Can thiệp thực hiện Ở DRIVER, không động vào upstream hay recipe:
driver `run_driver.py` của bước 6 xây user prompt bằng `build_prompt(template,
problem)`; can thiệp = nối thêm một hậu tố (suffix) cố định vào cuối user
prompt đã xây xong, trước khi truyền cho `runner.mts` (`--prompt` truyền
nguyên văn, không sửa gì khác). Recipe file, blend, system prompt, code
upstream KHÔNG thay đổi. Hậu tố là phần duy nhất khác giữa các nhánh.

- **I-full (chỉ dẫn đầy đủ):**
  `"\n\nUse your tools to do this task. First read solution.py with the read tool, then write or edit it with the write or edit tool, then run it with bash to verify. Do not answer with code in chat text — act with tools."`
- **I-min (chỉ dẫn tối thiểu):**
  `"\n\nUse the write tool to write the solution into solution.py, then run it with bash."`
- **Nhánh đối chứng C-pi:** hậu tố I-full gắn trên blend R1 (pi prompt /
  pi tools / pi turn) — kiểm tra xem hậu tố có tự nó làm hỏng (hay giúp)
  một harness đang chạy tốt không. Nếu C-pi rớt ≥ 2 bài so với R1 (4/10)
  thì hậu tố có tác dụng phụ, phải ghi rõ khi diễn giải B1/B2.

### Vì sao KHÔNG có biến thể "prompt opencode rút ngắn"

- Prompt hệ thống opencode là asset của upstream (`default.txt`, 8.528 byte).
  Khung blend chỉ CHỌN builder prompt theo sản phẩm (pi vs opencode) — nó
  không rút ngắn được một builder. Sửa asset = sửa code upstream (CẤM).
  Viết builder prompt tùy chỉnh = code harness mới ngoài khung recipe,
  ngoài phạm vi ngân sách này. Ghi nhận làm follow-up, không giả vờ làm
  được trong thiết kế này. Chẩn đoán F1 (hoán đổi prompt) đã làm ở bước 6;
  O3 kiểm tra cách sửa RẺ NHẤT còn khả thi trong khung hiện có.

## 3. Nhánh, bài, giao thức

- Nhánh (3, model cố định base `Qwen/Qwen2.5-Coder-7B-Instruct`):
  - **B1** = blend R8 + hậu tố I-full.
  - **B2** = blend R8 + hậu tố I-min.
  - **B3** = blend R1 + hậu tố I-full (đối chứng).
- Bài: ĐÚNG 10 bài của bước 6 (DESIGN §4.3, chọn theo quy tắc outcome-blind):
  lcb_001, lcb_002, lcb_005, lcb_010, lcb_015, lcb_020, held2_001, held2_005,
  held2_009, held2_013. `tasks.json` + `prompt_template.txt` copy
  byte-identical từ bước 6 (sha256 ghi lại). Không bài mới, không sửa test.
- Baseline TÁI DÙNG (không chạy lại): R8 0/10, text-only 10/10 và R1 4/10,
  text-only 2/10 từ `step6-mini-search/summary.json` — cùng bài, cùng runner,
  cùng giao thức, cùng model. Ghi rõ việc tái dùng + caveat khác đợt chạy
  (run-epoch) trong RESULTS.md. Tiết kiệm 20 lượt.
- Tổng lượt MỚI: 3 nhánh × 10 bài = **30 lượt**, 1 lượt/ô, max-steps 12,
  timeout 600 s, chấm ngoài bằng test suite (như bước 6).
- Recipe: file recipe R1/R8 copy byte-identical từ bước 6 (`recipes/`,
  sha256 đối chiếu `manifest.json`); kiểm chứng lại theo bước 6 §3 trước
  khi chạy (CLI assemble 52/52 + runtime blend probe 7/7 cho mỗi recipe).
  Driver: `run_driver.py` của bước 6, chỉ thêm cờ `--prompt-suffix`
  (ghi vào header + diff); logic chấm/parser/đếm/health/phân loại/rerun
  giữ nguyên. Kiểm tra offline trước GPU: chạy driver ở chế độ dry-run
  in prompt đã xây của 1 bài, khẳng định hậu tố có mặt và phần còn lại
  byte-identical với prompt gốc (ghi vào RUN_LOG §0).
- Chấm điểm: `verify_scoring.py` của bước 6 (adapted) phải cho 0 mismatch.
- Quy tắc INFRA/rerun như bước 6 (tối đa 1 rerun/ô INFRA, ghi REPLACEMENTS.log).

## 4. Phân tích — đăng ký trước (không đổi sau khi thấy kết quả)

- Mỗi nhánh: Pass@1 + Wilson 95% CI, text-only + Wilson CI, bảng 10 bài ×
  3 nhánh (PASS/FAIL/INFRA), số tool-call theo tool.
- **Tiêu chí "cứu được hành vi dùng tool" (B1/B2 so với R8 10/10 text-only):**
  text-only ≤ 5/10 (ít nhất một nửa số lượt dùng tool).
- **Tiêu chí "cải thiện kết quả" (B1/B2 so với R8 0/10):** Pass@1 ≥ 3/10.
- McNemar exact 2-phía B1-vs-R8 và B2-vs-R8 báo cáo dạng KHÁM PHÁ:
  với R8 ở 0/10, 3 thắng/0 thua cho p = 0,25 — KHÔNG có ý nghĩa thống kê.
  Viết trước điều này để không ai nâng một kết quả 3/10 thành "thắng có
  ý nghĩa". Ngôn từ được phép: "can thiệp mô tả làm giảm text-only từ
  10/10 xuống X/10 trên 10 bài" — không hơn.
- So sánh liều: B1 vs B2 mô tả (liều đầy đủ có hơn liều tối thiểu không?).
- Đối chứng B3 vs R1 (4/10): mô tả; nếu B3 ≤ 2/10 thì ghi "hậu tố làm hại
  harness đang chạy tốt" và thảo luận — không giấu.
- Phán quyết:
  - B1 (hoặc B2) đạt cả hai tiêu chí → "chỉ dẫn tường minh cứu được hành
    vi trên ngăn xếp opencode" — phát hiện cơ chế thứ hai, nối chẩn đoán
    bước 2 → sửa → đo lại (đúng mạch luận cứ → giả thuyết → thước đo).
  - Chỉ đạt tiêu chí hành vi, không đạt tiêu chí kết quả → "model dùng
    tool nhưng vẫn fail — nút thắt chuyển từ hành vi sang chất lượng code".
  - Không nhánh nào đạt tiêu chí hành vi → "không-tham-gia trên opencode
    robust trước chỉ dẫn tường minh ở mức này — kết quả âm tính".
- KHÔNG kết luận "prompt dài là nguyên nhân" (chưa tách được — xem §0);
  KHÔNG gộp test qua các nhánh.

## 5. Chi phí ước tính

- 30 lượt × $0,007/lượt = **$0,21** (căn cứ: bước 6, 90 lượt + 1 deploy
  = +$0,63–0,64). Deploy dùng chung với cả chương trình (xem
  PROGRAM_BUDGET.md): phần O3 **$0,10**.
- **Tổng O3 ≈ $0,31** (khoảng dự toán $0,25–0,35).

## 6. Rủi ro

- Hậu tố ở user prompt có thể bị system prompt 8,9KB "át" (đúng điều chẩn
  đoán nói) — khả năng cao B1/B2 chỉ cải thiện một phần. Đó là đáp án,
  không phải lỗi thiết kế.
- n = 10 bài, 1 lượt/ô: mọi kết luận đều mô tả, không có power thống kê.
- Baseline tái dùng khác đợt chạy: nếu kết quả B1/B2 nằm sát ngưỡng
  (text-only 5–6/10), ghi rõ caveat run-epoch, không tuyên bố cứu được.

## 7. Quy tắc sàn + dừng (tuyệt đối, không ngoại lệ)

- Token Modal đã hết hạn (19/11 10:25 +07, xác minh 20/11 20:11).
  CHỈ chạy GPU sau khi Triệu cấp lại quyền trong trình duyệt của mình.
  Nếu auth lỗi: DỪNG GPU ngay, làm phần offline, báo cáo.
- Snapshot `modal billing summary --json` TRƯỚC mọi GPU, sau mỗi nhánh,
  sau khi dừng app. Nếu billed_cost > $0,00 ở bất kỳ lần kiểm tra nào:
  DỪNG toàn bộ GPU ngay lập tức.
- Trước khi deploy: `modal app list`; chỉ deploy khi 0 task đang chạy;
  KHÔNG BAO GIỜ dừng app của người khác. Sau mỗi lượt: dừng app + tự kiểm
  tra `modal app list` = 0 task. (O3 chạy trong cùng phiên deploy với
  O2/O1/O5 nếu còn up — xem PROGRAM_BUDGET.md §2.)
- Upstream git-clean (HEAD b5adffa) kiểm tra trước deploy đầu và sau GPU
  cuối; fork ghi trạng thái trước/sau (kỳ vọng không đổi: 94 D + 2 ??).
  KHÔNG commit/push ở đâu. KHÔNG sửa slide/Drive/GitHub/Canva.

## 8. Tái dùng (diff-verified trước GPU; ghi vào RUN_LOG §0)

| File | Nguồn | Kiểm tra |
|---|---|---|
| runner.mts | bước 6 `runner.mts` | byte-identical (sha256 ghi lại) |
| run_driver.py | bước 6 `run_driver.py` | chỉ thêm cờ `--prompt-suffix`; còn lại verbatim |
| compute_stats.py | bước 6 `compute_stats.py` | gom theo nhánh (B1/B2/B3) thay vì recipe; `wilson` + `mcnemar_exact` verbatim |
| verify_scoring.py | bước 6 `verify_scoring.py` | cùng logic re-grade + hash-check + recipe-sha |
| recipes R1/R8 | bước 6 `recipes/` | byte-identical; CLI assemble 52/52 + blend probe 7/7 lại |
| tasks.json, prompt_template.txt | bước 6 | byte-identical (sha256 ghi lại) |
| 01_modal_vllm_rebuild_C_realtool.py, warmup.py | fix | byte-identical (sha256 c9bd2403… / 892a96b4…) |

## 9. Deliverables (dưới thư mục này)

DESIGN.md (file này), RUN_LOG.md, RESULTS.md, summary.json, summary.md,
recipes/ (R1/R8 + manifest + assemble outputs), probes/, runner.mts,
run_driver.py, compute_stats.py, verify_scoring.py, billing JSONs,
app-list logs, git-status snapshots, `runs/<nhánh>/<task>/` (30 ô).
