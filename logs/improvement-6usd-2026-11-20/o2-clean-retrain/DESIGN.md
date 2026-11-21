# DESIGN — O2: Train lại adapter fix SẠCH (chỉ từ 20 bài train) rồi đánh giá trên 45 bài chưa thấy

Ngày viết: 2026-11-20. Thiết kế đăng ký trước (pre-registered) TRƯỚC khi chạy bất kỳ lệnh GPU nào.
Chương trình: cải thiện HELIX $6 (ngân sách còn lại ~$6,00 credit, tài khoản $30).
Người duyệt thiết kế: Triệu (chưa duyệt chạy — chỉ duyệt thiết kế thì mới được chạy).

## 0. Vấn đề (đã xác minh — mắt xích yếu nhất W1 trong AUDIT.md 20/11/2026)

Headline của fix — pi-mono LoRA-mới 28/35, text-only 0/35 — đo trên đúng 35 bài
mà adapter đã train. Phân tách đã xác minh từ dữ liệu gốc
(`rebuild-fix-lora-tooluse/data/sft_data.jsonl` + `dpo_pairs.jsonl`, đếm lại 20/11/2026):

| Nguồn | Tổng | Từ 20 bài train (`lcb_*`) | Từ 15 bài heldout2 (`held2_*`) |
|---|---|---|---|
| SFT | 40 | **24** (15 bài lcb khác nhau) | 16 (11 bài held2 khác nhau) |
| DPO | 9 | **5** (5 bài lcb) | 4 (4 bài held2) |

Toàn bộ SFT đều từ harness pi-mono; DPO đều loại `tool_use_contrast`
(chosen = trace PASS của base, rejected = trace FAIL 0-tool của LoRA-cũ).
Bằng chứng held-out sạch duy nhất hiện nay là gen n = 30 (held3+held4:
mới 26/30 vs cũ 17/30, p = 0,0039 — nhưng đó là so với LoRA-cũ, không phải
so với base; mới vs base trên 30 bài là 26/30 vs 23/30, p = 0,375).

Thí nghiệm này trả lời: **fix hành vi có khái quát hóa sang bài chưa thấy
không, khi adapter CHƯA TỪNG thấy trace của bài đánh giá?**

## 1. Giả thuyết

**H-clean:** Adapter train chỉ từ trace của 20 bài train vẫn sửa được hành vi
text-only và không thua base về Pass@1 trên các bài chưa thấy (pi-mono),
vì hành vi dùng tool là một kỹ năng chung, không phải ghi nhớ từng bài.

## 2. Dữ liệu train — lọc lại từ dữ liệu fix, KHÔNG rút dữ liệu mới

- Lọc offline ($0): từ `sft_data.jsonl` giữ lại 24 mẫu có `task_id` bắt đầu
  bằng `lcb_`; từ `dpo_pairs.jsonl` giữ lại 5 cặp có `task_id` bắt đầu bằng
  `lcb_`. Loại bỏ 16 SFT + 4 DPO thuộc `held2_*`.
- Script lọc ghi `data-clean/manifest.json`: số lượng từng loại, danh sách
  task_id giữ lại/loại bỏ, và xác nhận (a) không còn task_id `held2_*` nào,
  (b) mọi mẫu giữ lại đều nằm trong 15 bài lcb đã liệt kê ở §0,
  (c) shim vẫn parse được mọi mẫu giữ lại (tập con của dữ liệu đã kiểm
  chứng 49/49 trong fix RUN_LOG — kiểm tra lại bằng cùng parser, ghi kết quả).
- Không thu thập thêm trace. Không dùng trace held3/held4 cho train
  (chúng là tập đánh giá chính — dùng chúng để train sẽ tái tạo đúng lỗi
  đang sửa).

## 3. Huấn luyện — công thức giống hệt adapter fix, chỉ thay DATA

- Base `Qwen/Qwen2.5-Coder-7B-Instruct`, Unsloth 4-bit QLoRA + TRL
  SFT-rồi-DPO, r=16, alpha=32, max_seq 4096, seed 42, epochs 3,
  lr SFT 2.0e-4, lr DPO 5.0e-6, batch SFT 2×grad-accum 4, batch DPO 1×8
  — cùng script `train_lora_realtool.py` của fix (copy sang thư mục này,
  diff-verified trước khi chạy; chỉ thay đường dẫn dữ liệu).
- Lệnh: `modal run train_lora_clean.py --stage sft_then_dpo --epochs 3`
  (như fix RUN_LOG: `modal run train_lora_realtool.py --stage sft_then_dpo --epochs 3`).
- Adapter mới tên riêng **`helix-lora-clean`** trên volume `helix-adapters`.
  Adapter `helix-lora-realtool` và `helix-lora-final` giữ nguyên, không động vào.
- Số bước kỳ vọng (tính từ công thức, KHÔNG phải tiêu chí): SFT 24 mẫu × 3
  epoch / batch hiệu dụng 8 ≈ 9 bước; DPO 5 cặp × 3 epoch / 8 ≈ 2 bước
  (fix: SFT 15 bước, DPO 6 bước — ghi số bước thực tế từ log, không ép khớp).
  Chỉ ghi log loss; không tune siêu tham số sau khi thấy loss.
- Nếu loss DPO không giảm hoặc train lỗi: báo cáo nguyên trạng, không đổi
  recipe, không train lại với epoch khác (một lần train duy nhất, đăng ký trước).

## 4. Đánh giá — pi-mono, 45 bài, 3 nhánh, 1 lượt/ô

- Bài: 45 bài = 15 held2 + 15 held3 + 15 held4. Nguồn task:
  held2 từ `rebuild-driver-2026-11-15/tasks.json` (15 bài `held2_*`),
  held3 từ `generalisation-check-2026-11-18/tasks.json` (15 bài),
  held4 từ `evolution-2026-11-18/step4b-gen-extension/tasks.json` (15 bài).
  Kiểm tra offline TRƯỚC GPU: hợp của 45 task_id không chứa task `lcb_*`
  nào (adapter sạch train trên lcb — tập đánh giá phải có 0 bài lcb);
  định nghĩa bài + test case byte-identical với các file nguồn (sha256 ghi lại).
  Các bài này đã được kiểm tra test trước GPU trong các đợt trước
  (gen TASK_AUDIT, step4b TASK_AUDIT) — không viết bài mới, không sửa test.
- Nhánh (3): base (`Qwen/Qwen2.5-Coder-7B-Instruct`) vs `helix-lora-clean`
  (mới) vs `helix-lora-realtool` (cũ). Chạy mới CẢ 3 nhánh (không tái dùng
  số cũ): cùng đợt chạy, cùng deployment, so sánh cặp theo bài mới hợp lệ.
- Harness: pi-mono duy nhất (như tiêu chí C1/C2 gốc của fix; opencode/hermes
  không chạy ở đây — hành vi trên đó là việc của O3, và chi phí không cho phép).
- Giao thức: deployment variant C (proxy+shim), driver `run_driver.py` của fix
  (copy, diff-verified), `prompt_template.txt` byte-identical, max-steps 12,
  timeout 600 s, chấm ngoài bằng test suite, 1 lượt/ô.
- Tổng: 3 nhánh × 45 bài = **135 lượt**.
- Chấm điểm: `verify_scoring.py` của fix (adapted) phải cho 0 mismatch
  (không thì báo cáo mismatch).
- Quy tắc INFRA/rerun như fix (tối đa 1 rerun/ô INFRA, ghi REPLACEMENTS.log).

## 5. Phân tích — đăng ký trước (không đổi sau khi thấy kết quả)

### 5.1 So sánh CHÍNH: mới vs base trên 30 bài thực sự chưa thấy (held3+held4)

Cả hai nhánh đều chưa từng thấy 30 bài này dưới bất kỳ dạng nào
(không train, không tham gia quyết định thiết kế fix). Held2 là so sánh
PHỤ (xem §5.2) vì held2 nằm trong tập đánh giá 35 bài đã định hình thiết kế
fix (adaptation), dù adapter sạch chưa từng train trên held2.

- **C1 (hành vi, chính):** text-only pi-mono của `helix-lora-clean` trên
  30 bài ≤ 1/30. (Tham chiếu lập kế hoạch — KHÔNG phải so sánh: realtool
  đạt 0/30, base 1/30 trên đúng 30 bài này trong các đợt trước.)
- **C2 (kết quả, chính):** Pass@1 của `helix-lora-clean` ≥ base trên
  30 bài (không thua). McNemar exact 2-phía báo cáo dạng KHÁM PHÁ
  (exploratory), KHÔNG yêu cầu p < 0,05 để kết luận "không thua":
  với n = 30 và base ~23/30, một chênh lệch thật +3 bài cũng chỉ cho
  p ≈ 0,375 trong trường hợp discordant tốt nhất — đòi p < 0,05 là
  đặt tiêu chí không thể đạt.
- **Phán quyết:**
  - C1 + C2 đạt → "fix sạch khái quát hóa: hành vi đã sửa trên bài chưa
    thấy, không thua base" — được phép thay câu "ủng hộ có điều kiện"
    trên slide 19 bằng câu này (với đầy đủ caveat n = 30, 1 lượt/ô).
  - C1 đạt + C2 thiếu ≥ 2 bài → "hành vi chuyển được, kết quả không —
    kết quả HỖN HỢP, báo cáo như vậy, không giấu".
  - C1 không đạt (text-only ≥ 2/30) → "fix hành vi không chuyển sạch
    sang bài chưa thấy" — kết quả âm tính, báo cáo nguyên trạng.
- Nếu mới hơn base ≥ 4 bài trên 30 bài: báo cáo McNemar và ghi "lần đầu
  có thắng sạch trên held-out" — nhưng không nâng ngôn từ phán quyết
  quá "ủng hộ khái quát hóa trên bài hàm pi-mono" (không khái quát
  sang harness khác hay kiểu bài khác).

### 5.2 So sánh PHỤ: bảng đủ 45 bài (mới vs base vs cũ)

- Bảng đủ 45 bài (3 nhánh × Pass@1 + text-only + Wilson 95% CI) + tách
  theo cohort (held2 / held3 / held4, mỗi cohort 15 bài).
- **Cảnh báo ô nhiễm — ghi trên mọi bảng có nhánh cũ:** các ô held2 của
  `helix-lora-realtool` là Ô NHIỄM (adapter cũ train trên 16 SFT + 4 DPO
  thuộc held2) — không được dùng số held2 của nhánh cũ để kết luận gì.
  So sánh mới-vs-cũ chỉ được đọc trên held3+held4 (30 bài), dạng mô tả.
- So sánh mới-vs-base trên đủ 45 bài: mô tả (held2 sạch cho cả hai nhánh
  về mặt train, nhưng là phụ vì lý do adaptation ở §5.1).
- KHÔNG gộp test qua các cohort, KHÔNG test qua harness (chỉ có pi-mono).

## 6. Chi phí ước tính (từ các lần chạy trước, không phải cam kết)

- Train: fix train +$0,108 (SFT 15 bước + DPO 6 bước); ablation SFT-only
  train +$0,209. Dự toán O2 train: **~$0,20** (lấy mức cao).
- Đánh giá: 135 lượt pi-mono × $0,012/lượt = **$1,62**.
  (Căn cứ: ablation 105 lượt pi-mono +$0,98 ≈ $0,0093/lượt; gen pi-mono
  45 lượt +$0,50 ≈ $0,0111/lượt — lấy $0,012 làm mức dự toán thận trọng.
  Trường hợp bi quan: fix pi-mono +$1,23/70 lượt ≈ $0,0176/lượt → 135 lượt
  ≈ $2,38 — xem quy tắc dừng ở §8.)
- Deploy dùng chung 1 lần cho cả chương trình (xem PROGRAM_BUDGET.md):
  phần O2 **$0,15**.
- **Tổng O2 ≈ $1,97** (khoảng dự toán $1,80–2,00).

## 7. Rủi ro

- Tập train nhỏ hơn fix (24 SFT + 5 DPO so với 40 + 9): adapter sạch có
  thể yếu hơn adapter cũ — đó chính là điều thí nghiệm đo, không phải lỗi.
  Nếu C1/C2 không đạt, đó là đáp án (fix không khái quát hóa sạch), không
  phải lý do train lại với dữ liệu khác.
- DPO chỉ 5 cặp: nếu loss DPO không giảm, ghi nguyên trạng; không thêm cặp,
  không đổi lr.
- Base tự trôi giữa các lần chạy (25→20→22→23/35 trên pi-mono): so sánh
  mới-vs-base trong cùng đợt chạy này mới hợp lệ; KHÔNG so số mới với số
  base của đợt cũ (23/30 gộp) để kết luận.
- 1 lượt/ô: phương sai chưa đo — đó là việc của O1 (lặp lại sau O2).

## 8. Quy tắc sàn + dừng (tuyệt đối, không ngoại lệ)

- Token Modal đã hết hạn (19/11 10:25 +07, xác minh 20/11 20:11).
  CHỈ chạy GPU sau khi Triệu cấp lại quyền trong trình duyệt của mình.
  Nếu auth lỗi: DỪNG GPU ngay, làm phần offline, báo cáo.
- Snapshot `modal billing summary --json` TRƯỚC mọi GPU, sau train,
  sau đánh giá, sau khi dừng app. Nếu billed_cost > $0,00 ở bất kỳ lần
  kiểm tra nào: DỪNG toàn bộ GPU ngay lập tức.
- Trước khi deploy: `modal app list`; chỉ deploy khi 0 task đang chạy;
  KHÔNG BAO GIỜ dừng app của người khác. Sau mỗi lượt: dừng app + tự kiểm
  tra `modal app list` = 0 task.
- Quy tắc dừng theo chi phí: sau 45 ô đánh giá đầu, nếu $/lượt quan sát
  được × số ô còn lại dự báo tổng chương trình vượt $6,00 thì dừng sau
  ô hiện tại, dừng app, báo cáo phần đã xong (quy tắc này viết trước,
  không điều chỉnh sau khi thấy kết quả).
- Upstream git-clean (HEAD b5adffa) kiểm tra trước deploy đầu và sau GPU
  cuối; fork ghi trạng thái trước/sau (kỳ vọng không đổi: 94 D + 2 ??).
  KHÔNG commit/push ở đâu. KHÔNG sửa slide/Drive/GitHub/Canva.

## 9. Tái dùng (diff-verified trước GPU; ghi vào RUN_LOG §0)

| File | Nguồn | Kiểm tra |
|---|---|---|
| train_lora_clean.py | fix `train_lora_realtool.py` | copy, chỉ thay đường dẫn dữ liệu → `data-clean/`; diff ghi lại |
| 01_modal_vllm_rebuild_C_clean.py | fix `01_modal_vllm_rebuild_C_realtool.py` | byte-identical trừ danh sách adapter (thêm `helix-lora-clean`); sha256 ghi lại |
| warmup.py | fix `warmup.py` | byte-identical (sha256 892a96b4…) |
| run_driver.py | fix `run_driver.py` | logic chấm/parser/đếm/health/phân loại/rerun giữ nguyên; chỉ thay danh sách task + model |
| compute_stats.py | fix `compute_stats.py` | `wilson` + `mcnemar_exact` copy verbatim; gom theo (pi-mono, model, cohort) |
| verify_scoring.py | fix `verify_scoring.py` | cùng logic re-grade + hash-check |
| tasks.json (45 bài) | 3 file nguồn ở §4 | byte-identical từng task; sha256 ghi lại |
| prompt_template.txt | fix `prompt_template.txt` | byte-identical (sha256 3e100f24…) |

## 10. Deliverables (dưới thư mục này)

DESIGN.md (file này), `data-clean/` (24 SFT + 5 DPO đã lọc + manifest.json),
RUN_LOG.md, RESULTS.md, summary.json, summary.md, train script + log,
billing JSONs (before/train/after/delayed), app-list logs, git-status
snapshots, `runs/pi-mono/<model>/<task>/` (135 ô).
