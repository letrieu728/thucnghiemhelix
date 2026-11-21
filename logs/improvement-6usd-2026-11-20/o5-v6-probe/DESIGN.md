# DESIGN — O5: Thăm dò v6 — prompt có cứu được "không tham gia" trên bài sửa lỗi?

Ngày viết: 2026-11-20. Thiết kế đăng ký trước (pre-registered) TRƯỚC khi chạy bất kỳ lệnh GPU nào.
Chương trình: cải thiện HELIX $6 (ngân sách còn lại ~$6,00 credit, tài khoản $30).
Người duyệt thiết kế: Triệu (chưa duyệt chạy — chỉ duyệt thiết kế thì mới được chạy).

## 0. Quy tắc nhãn (tuyệt đối, áp dụng cho mọi tài liệu trong thư mục này)

Các fixture dưới `fork/packages/conformance/fixtures/tasks/livecodebench-v6-*/`
là **NỘI DUNG NHÓM TÁI TẠO** (nhóm dựng lại từ khóa `test6.jsonl` + builder
spec sau khi phát hiện symlink của tác giả gãy, bản gốc không khôi phục
được). Chấm trên **PUBLIC TEST CASE ONLY** (2–4 case/fixture). KHÔNG BAO GIỜ
gọi chúng là bản gốc của tác giả. KHÔNG BAO GIỜ gọi lần chạy này là benchmark
của tác giả hay đánh giá LiveCodeBench. So sánh với kết quả bài hàm tự viết
chỉ là MÔ TẢ (kiểu bài khác, cách chấm khác; không test thống kê qua các
tập bài, không gộp số).

## 1. Vấn đề (đã xác minh — bước 5, RESULTS.md)

Trên 16 fixture v6 tái tạo, pi-mono, base + realtool: base **0/16**, realtool
**1/16** (McNemar 1/0, p = 1,0); text-only 14/16 vs 10/16. Đọc cả 32 transcript:
đây là thất bại **KHÔNG THAM GIA**, không phải thất bại code — 30/32 file
`solution.py` cuối là seed lỗi nguyên vẹn. Mẫu hành vi chiếm ưu thế là
Pattern A (24/32 lượt): model trả lời bằng text, bảo "hãy đưa nội dung
`solution.py` cho tôi xem" như đang chat, rồi dừng. Mẫu C (6 lượt): model
đọc file, chẩn đoán đúng, viết code sửa TRONG TEXT rồi dừng — không gọi
edit/write, không chạy test. Chỉ 2 lượt (Pattern D, đều realtool) tham gia
đầy đủ read → write → bash.

Câu hỏi O5: **thất bại không-tham-gia này có phải do prompt không?**
Cụ thể: prompt v6 (problem statement dài + Task list 4 bước + execution
hints) có phải là thứ kéo model về chế độ chat "hỏi người dùng" — trong khi
prompt bài hàm (mệnh lệnh ngắn: viết code vào solution.py, chạy để kiểm tra)
lại cho hành vi dùng tool tốt (realtool 0/35 text-only)?

## 2. Can thiệp — 2 biến thể prompt (viết trước, nguyên văn)

Can thiệp thực hiện Ở DRIVER (`run_v6_driver.py` của bước 5, thêm cờ
`--prompt-variant`): prompt fixture (`prompt.md` + execution hints, xây
đúng như `loadTask` trong task-parity.ts) được sửa theo biến thể TRƯỚC KHI
truyền cho CLI. Nội dung fixture (`prompt.md`, `solution.py`, test) KHÔNG
đổi; fork KHÔNG bị ghi. Prompt cuối của mỗi ô lưu vào `prompt.txt` + sha256
như bước 5.

- **V1 — chỉ dẫn chống-hỏi, gắn CUỐI prompt (sau execution hints):**
  Thêm sau 3 bullet execution hints:
  `"Start by reading solution.py with the read tool. Do not ask the user for file contents — the file is in your workspace. Then edit solution.py with the edit or write tool, and run python3 test_solution.py with bash to verify."`
  Nhắm thẳng Pattern A (24/32 lượt hỏi người dùng).
- **V2 — phong cách mệnh lệnh ngắn, gắn ĐẦU prompt (trước prompt.md):**
  Thêm trước toàn bộ prompt.md:
  `"Fix the bug in solution.py. Only modify solution.py. When done, run python3 test_solution.py to verify it works.\n\n"`
  rồi giữ nguyên prompt.md + execution hints phía sau. Nhắm câu hỏi
  "phong cách prompt": liệu mệnh lệnh ngắn kiểu bài hàm có cứu được
  tham gia trên bài sửa lỗi không (chuyển phong cách, không chuyển nội dung).

V1 và V2 khác nhau về cả vị trí (cuối vs đầu) lẫn nội dung (chống-hỏi cụ
thể vs mệnh lệnh ngắn chung) — đây là thăm dò, không phải thí nghiệm tách
cơ chế sạch; kết quả chỉ được đọc là "biến thể nào (nếu có) cứu được tham
gia", không được đọc là "yếu tố X trong prompt là nguyên nhân".

## 3. Nhánh, fixture, giao thức

- Nhánh (2): base + realtool (`helix-lora-realtool`). Không chạy LoRA-cũ
  (như bước 5 — câu hỏi là base-vs-realtoool trên kiểu bài mới).
- Fixture: ĐÚNG 16 fixture của bước 5 (stride 6 từ danh sách eligible,
  abc387–400 + arc191/193 — xem bước 5 DESIGN §2). `fixtures.json` copy
  từ bước 5, byte-identical. Không fixture mới, không sửa fixture.
- Biến thể (2): V1, V2. Tổng: 2 biến thể × 2 nhánh × 16 fixture = **64 lượt**,
  1 lượt/ô, pi-mono duy nhất (như bước 5 — harness của pilot; không thêm
  harness thứ hai).
- Thứ tự chạy: FIXTURE-MAJOR trong mỗi biến thể (mỗi fixture: base rồi
  realtool), biến thể V1 trước, V2 sau. Lý do: nếu dừng giữa chừng thì
  phần xong vẫn là các cặp fixture đầy đủ.
- Baseline TÁI DÙNG (không chạy lại): bước 5 — base 0/16, text-only 14/16,
  tham gia (≥1 tool call) 2/16; realtool 1/16, text-only 10/16, tham gia
  6/16. Cùng fixture, cùng giao thức, cùng model. Ghi rõ việc tái dùng +
  caveat khác đợt chạy trong RESULTS.md.
- Giao thức: `helix run` pi-mono, deployment variant C, `run_v6_driver.py`
  của bước 5 (chỉ thêm cờ `--prompt-variant`; logic chấm/parser/đếm/health/
  phân loại/rerun giữ nguyên), workspace cố định (không xóa sau chạy),
  seed fixture copy byte-for-byte + sha256, chấm ngoài bằng verifier gốc
  (pristine test_solution.py, exit 0 + marker `<fixture-id> tests passed`).
- Pilot gate: 2 ô đầu (fixture 000, base + realtool, V1) chạy trước; kiểm
  tra bằng tay transcript/workspacce/chấm điểm được lưu đầy đủ rồi mới
  chạy tiếp (như bước 5 §4.6). Pilot là một phần của 64 lượt, không thêm.
- Chấm điểm: `verify_scoring.py` của bước 5 (adapted) phải cho 0 mismatch.
- Quy tắc INFRA/rerun như bước 5 (tối đa 1 rerun/ô INFRA, ghi REPLACEMENTS.log).

## 4. Phân tích — đăng ký trước (không đổi sau khi thấy kết quả)

- Mỗi (biến thể × nhánh): Pass@1 + Wilson 95% CI, text-only + Wilson CI,
  bảng 16 fixture × 2 nhánh (PASS/FAIL/INFRA, tools, đổi file?, marker?).
- **Số liệu CHÍNH: tỉ lệ tham gia** = số lượt có ≥1 tool call đọc HOẶC
  sửa `solution.py` (read/edit/write chạm solution.py) HOẶC chạy test
  (bash `test_solution.py`). Đây là số liệu trực tiếp đo câu hỏi "có tham
  gia không" — Pass@1 là phụ (n = 16, code có thể đúng mà vẫn không tham gia
  theo nghĩa hành vi, và ngược lại).
- **Tiêu chí "cứu được tham gia" (cho từng nhánh):** tham gia ≥ 8/16
  (so với baseline bước 5: base 2/16, realtool 6/16).
- Pass@1: mô tả thuần (không test ý nghĩa; n = 16, CI rộng).
  McNemar base-vs-realtoool TRONG từng biến thể báo cáo mô tả (như bước 5).
- Bảng cơ chế theo transcript (như bước 5 §3): đếm lượt đọc / sửa /
  chạy test / thấy marker theo từng (biến thể × nhánh); ghi chú hành vi
  ngắn cho các lượt đổi mẫu (đặc biệt: Pattern A có còn xuất hiện không?).
- Phán quyết:
  - Một biến thể đạt tiêu chí tham gia ở ≥1 nhánh → "prompt cứu được
    tham gia trên bài sửa lỗi (ở mức này)" + ghi rõ biến thể nào, nhánh nào.
  - Không biến thể nào đạt tiêu chí ở nhánh nào → "không-tham-gia robust
    trước hai kiểu sửa prompt này — kết quả âm tính; thất bại v6 không phải
    artifact của câu chữ prompt ở mức này" (và đó vẫn là đáp án có giá trị
    cho phần giới hạn của deck).
  - V1 đạt nhưng V2 không (hoặc ngược lại) → báo cáo đúng như vậy, không
    gộp hai biến thể thành "prompt nói chung có tác dụng".
- KHÔNG so sánh thống kê với kết quả bài hàm (kiểu bài khác — chỉ mô tả
  cạnh nhau như bước 5 §4). KHÔNG gọi đây là đánh giá LiveCodeBench.

## 5. Chi phí ước tính

- 64 lượt × $0,007/lượt = **$0,45** (căn cứ: bước 5, 32 lượt + 1 deploy
  = +$0,22 ≈ $0,0069/lượt — dù mỗi lượt v6 chạy lâu hơn (pilot 246 s),
  tỉ lệ $/lượt quan sát được vẫn là $0,0069).
- Deploy dùng chung với cả chương trình (xem PROGRAM_BUDGET.md):
  phần O5 **$0,10**.
- **Tổng O5 ≈ $0,55** (khoảng dự toán $0,50–0,60).

## 6. Rủi ro

- Cả hai biến thể đều có thể thất bại (Pattern A có thể là xu hướng mạnh
  của model 7B trên prompt dài, không sửa được bằng 1–2 câu) — đó là đáp
  án âm tính đã đăng ký trước, không phải lỗi.
- n = 16, 1 lượt/ô: mọi kết luận đều mô tả.
- V2 thêm mệnh lệnh ngắn TRƯỚC problem statement dài: model có thể bỏ
  qua phần đầu khi đọc statement dài — nếu V2 thất bại trong khi V1 thành
  công, đó là thông tin về vị trí chỉ dẫn, ghi rõ, không diễn giải quá.

## 7. Quy tắc sàn + dừng (tuyệt đối, không ngoại lệ)

- Token Modal đã hết hạn (19/11 10:25 +07, xác minh 20/11 20:11).
  CHỈ chạy GPU sau khi Triệu cấp lại quyền trong trình duyệt của mình.
  Nếu auth lỗi: DỪNG GPU ngay, làm phần offline, báo cáo.
- Snapshot `modal billing summary --json` TRƯỚC mọi GPU, sau mỗi biến thể,
  sau khi dừng app. Nếu billed_cost > $0,00 ở bất kỳ lần kiểm tra nào:
  DỪNG toàn bộ GPU ngay lập tức.
- Trước khi deploy (nếu cần deploy riêng): `modal app list`; chỉ deploy
  khi 0 task đang chạy; KHÔNG BAO GIỜ dừng app của người khác. Sau mỗi
  lượt: dừng app + tự kiểm tra `modal app list` = 0 task. (O5 chạy trong
  cùng phiên deploy với O2/O3/O1 nếu còn up — xem PROGRAM_BUDGET.md §2.)
- Upstream git-clean (HEAD b5adffa) kiểm tra trước deploy đầu và sau GPU
  cuối; fork ghi trạng thái trước/sau (kỳ vọng không đổi: 94 D + 2 ??).
  KHÔNG commit/push ở đâu. KHÔNG sửa slide/Drive/GitHub/Canva.
- Checkpoint chi tiêu: sau pilot V1 (2 ô) và sau mỗi 16 ô; nếu dự báo
  tổng chương trình vượt $6,00 thì dừng sau ô hiện tại (thứ tự fixture-major
  giữ phần xong luôn là các cặp đầy đủ).

## 8. Tái dùng (diff-verified trước GPU; ghi vào RUN_LOG §0)

| File | Nguồn | Kiểm tra |
|---|---|---|
| run_v6_driver.py | bước 5 `run_v6_driver.py` | chỉ thêm cờ `--prompt-variant`; còn lại verbatim |
| compute_stats.py | bước 5 `compute_stats.py` | gom theo (biến thể, model, fixture); `wilson` + `mcnemar_exact` verbatim |
| verify_scoring.py | bước 5 `verify_scoring.py` | cùng logic re-grade + hash-check |
| fixtures.json | bước 5 `fixtures.json` | byte-identical |
| 01_modal_vllm_rebuild_C_realtool.py, warmup.py | fix | byte-identical (sha256 c9bd2403… / 892a96b4…) |

## 9. Deliverables (dưới thư mục này)

DESIGN.md (file này), RUN_LOG.md, RESULTS.md, summary.json, summary.md,
fixtures.json, billing JSONs, app-list logs, git-status snapshots,
`runs/pi-mono/<biến thể>/<model>/<fixture>/` (64 ô).
