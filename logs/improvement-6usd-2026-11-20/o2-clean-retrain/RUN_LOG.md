# RUN_LOG — O2: Train lại adapter fix SẠCH (lcb_* only) + đánh giá 45 bài (20/11/2026)

Múi giờ ghi log: UTC trong file (giờ +07 = UTC+7). Thiết kế đăng ký trước:
DESIGN.md trong thư mục này (Triệu duyệt thiết kế; chạy theo chương trình $6).

## Giai đoạn 0 — Token + billing + git

- Token Modal FRESH (cấp lại 20/11 20:37 +07, profile letrieu728, verified).
- Billing baseline (billing_before_train.json): metered **$24.78857824**,
  credits −$23.86, billed **$0.00**. Trần chương trình: $6.00 metered
  (tức trần tuyệt đối $30.78857824).
- `modal app list` trước train: 0 app, 0 task.
- Upstream git clean trước GPU (HEAD b5adffa, status trống);
  fork 94 D + 2 ?? (đúng kỳ vọng). Xem upstream_git_status_before.txt,
  fork_git_status_before.txt.

## Giai đoạn 1 — Lọc dữ liệu (offline, $0)

- Script: filter_clean_data.py. Nguồn: fix data (sft_data.jsonl 40,
  dpo_pairs.jsonl 9).
- Đếm kiểm chứng TRƯỚC khi lọc: SFT 24 lcb + 16 held2; DPO 5 lcb + 4 held2
  — khớp DESIGN.md §0.
- Kết quả: data-clean/sft_data.jsonl **24 mẫu** (15 bài lcb khác nhau),
  data-clean/dpo_pairs.jsonl **5 cặp** (5 bài lcb, tập con của 15 bài trên);
  loại 16 SFT + 4 DPO thuộc held2_*.
- Kiểm chứng manifest.json: (a) không còn task_id held2_* nào trong dữ
  liệu giữ lại; (b) mọi mẫu giữ lại đều nằm trong 15 bài lcb; (c) shim
  parse được mọi mẫu giữ lại — **29/29** (24 SFT ≥1 tool call; 5 DPO
  chosen ≥1 call, rejected 0 call), dùng cùng parser extract_function_calls
  từ variant C như fix (49/49).
- data-clean/provenance.json: viết mới cho tập đã lọc (counts 24/5 +
  SHA-256 của file đã lọc, allow_dry_run=false, nguồn là tập fix live-only
  + bộ lọc task_id startswith 'lcb_') — script train yêu cầu provenance
  khớp counts/hash, nếu không sẽ từ chối train. Đây là file dữ liệu,
  không phải thay đổi recipe.

## Giai đoạn 2 — Train (Modal A100, 1 lần duy nhất)

- Script: train_lora_clean.py = bản sao train_lora_realtool.py của fix.
  Diff kiểm chứng: CHỈ 3 thay đổi (comment đầu file, LOCAL_DATA_DIR →
  data-clean/, final_adapter_dir → helix-lora-clean). Mọi siêu tham số
  giữ nguyên: epochs 3, lr SFT 2e-4, DPO lr 5e-6, beta 0.1, r=16,
  alpha=32, dropout 0.05, seed 42, max_seq 4096.
- Lệnh: `modal run train_lora_clean.py --stage sft_then_dpo --epochs 3`.
  Run id: **20261120T134052-b464f60f**. Exit 0.
- SFT: **9 bước** (đúng kỳ vọng ~9), loss **1.2489 → 0.6313**
  (1.2489, 1.0694, 1.0942, 0.9286, 0.8249, 0.7992, 0.7346, 0.6702, 0.6313;
  train_loss trung bình 0.8890). 24 mẫu.
- DPO: **3 bước** (kỳ vọng ~2), loss **0.6931 → 0.6285**
  (0.6931, 0.6931, 0.6285; rewards/accuracies 1.0 ở bước cuối).
  Loss DPO CÓ giảm — báo cáo nguyên trạng, không tune thêm.
- Adapter lưu tại volume helix-adapters/**helix-lora-clean** (MỚI).
  helix-lora-realtool và helix-lora-final KHÔNG bị động (kiểm chứng bằng
  volume ls sau train).
- Log đầy đủ: train_clean.log; training_runs/20261120T134052-b464f60f/.
- Billing sau train (billing_after_train.json): metered $24.86586949,
  billed $0.00 (delta **+$0.0773** so với baseline). App train stopped,
  0 task.

## Giai đoạn 3 — Chuẩn bị đánh giá (offline, $0)

- tasks.json: 45 bài = 15 held2 (từ rebuild-driver-2026-11-15/tasks.json)
  + 15 held3 (generalisation-check-2026-11-18/tasks.json) + 15 held4
  (evolution-2026-11-18/step4b-gen-extension/tasks.json). Kiểm chứng:
  hợp 45 task_id KHÔNG chứa lcb_* nào; mỗi task byte-identical với file
  nguồn (sha256 từng task trong tasks_manifest.json).
- 01_modal_vllm_rebuild_C_clean.py = bản sao file deploy của fix, diff
  kiểm chứng: chỉ thêm helix-lora-clean vào danh sách phục vụ (+ fail-loud
  nếu thiếu) và **--max-loras 2 → 3** (bắt buộc để cả 3 adapter cùng load;
  giữ 2 thì adapter thứ 3 không serve được). sha256:
  fix c9bd24037c7b1cfcfd915651194e10a88054be7609923f8b421137fd636e486c;
  clean 20b698cafcdeef61d952835b46850d36aa0b31fd429f55a28b5f5065a9add3ee.
- run_driver.py = bản sao driver fix, diff kiểm chứng: chỉ thay danh
  sách task (assert 45), --model thêm "clean" (MODEL_IDS clean →
  helix-lora-clean), PILOT_IDS = 5 bài held2 đầu (không bài lcb_* nào
  nằm trong tập đánh giá), task_set = cohort từ tiền tố task_id
  (held2/held3/held4). Scoring/parser/health/phân loại/rerun giữ nguyên.
- compute_stats.py: wilson + mcnemar_exact + summarise + no_tool_stats
  copy VERBATIM từ fix (đã kiểm chứng bằng AST-diff); phần gom nhóm viết
  lại cho 3 model × 3 cohort + các phép thử paired đã đăng ký trước
  (§5 DESIGN). Ghi chú: đã thêm sẵn 1 nhánh phán quyết thứ 4 TRƯỚC khi
  thấy kết quả cho trường hợp không nằm trong 3 nhánh của §5.1 (C1 đạt,
  C2 thiếu đúng 1 bài → "HỖN HỢP (nhẹ)") — nhánh này KHÔNG kích hoạt
  trong lần chạy này (C2 đạt, +3).
- verify_scoring.py, warmup.py, prompt_template.txt: copy byte-identical
  từ fix (prompt_template sha256 3e100f24…; warmup sha256 892a96b4…).
  warmup.py kiểm tra realtool + base trong adapters; helix-lora-clean
  được kiểm chứng riêng qua /v1/models (có trong danh sách, xem dưới).

## Giai đoạn 4 — Deploy + warmup

- `modal app list` trước deploy: 0 task đang chạy (app train đã stopped).
- Billing trước deploy (billing_before_deploy.json): metered $24.89586991,
  billed $0.00. LƯU Ý: metered trôi +$0.0300 so với sau train mà KHÔNG
  có GPU nào chạy giữa hai lần đọc — billing lag/điều chỉnh, đã thấy ở
  các bước trước (±$0.01–0.05).
- Deploy 13:45 UTC: `modal deploy 01_modal_vllm_rebuild_C_clean.py`.
  Endpoint giữ nguyên
  https://letrieu728--helix-vllm-engine-vllmserver-serve.us-east.modal.run
- Warmup 94.5s (10 attempts): /health 200, lora_enabled=true,
  adapters=[helix-lora, helix-lora-realtool, helix-lora-clean],
  shim=true; /v1/models liệt kê đủ 4 model id (base + 3 LoRA).
  Xem warmup_pi-mono.json, v1_models_pi-mono.json.

## Giai đoạn 5 — Đánh giá (135 ô, pi-mono, 1 lượt/ô)

Thứ tự chạy (chủ đích: 2 nhánh chính clean → base trước, realtool sau):
pilot clean (3 ô) → sweep clean (45 ô) → checkpoint chi phí → sweep base
(45 ô) → sweep realtool (45 ô). Driver tự skip các ô pilot đã có
result.json; pilot là 1 phần của sweep, không chạy thừa.

- Pilot clean: 1/3 PASS; cả 3 ô đều gọi tool (3/3/2 call). 0 INFRA.
- Sweep clean 45/45: 1 INFRA (held3_010_house_robber, harness_error,
  finish=provider_error, provider 500 sau 3 bước/2 tool call). Rerun
  ĐÚNG 1 lần theo quy tắc INFRA → PASS. Xem REPLACEMENTS.log.
- **Checkpoint chi phí sau 45 ô đầu** (billing_after_clean45.json):
  metered $25.66753226, billed $0.00. Deploy+45 ô = +$0.7717 →
  $/lượt quan sát $0.0138 (chỉ eval, trừ $0.15 deploy share) / $0.0172
  (thận trọng, gộp deploy). Dự báo tổng chương trình (×1.2 + O3/O1/O5
  theo tỉ lệ ngân sách): $29.44–29.80 < trần $30.79 → TIẾP TỤC.
  Tỉ lệ thực tế cao hơn dự toán $0.012/lượt nhưng vẫn trong trần.
- Sweep base 45/45: 0 INFRA, không rerun.
- Sweep realtool 45/45: 2 INFRA (held3_003_majority_element, provider 500
  sau 1 bước/0 tool call; held4_014_candy, provider 500 sau 5 bước/
  4 tool call). Mỗi ô rerun ĐÚNG 1 lần → cả 2 đều PASS.
- Tổng: **135 ô scored, 0 INFRA cuối cùng**; 3 rerun INFRA, tất cả đều
  provider 500 (cùng nguyên nhân như fix). Xem REPLACEMENTS.log
  (3 dòng) + các log rerun_infra_*.
- verify_scoring.py: **checked=135, infra_skipped=0, mismatches=0,
  hash_mismatches=0** (exit 0).
- compute_stats.py → summary.json + summary.md. Số liệu đầy đủ ở
  RESULTS.md.

## Giai đoạn 6 — Billing + dừng app + git sau GPU

- Billing sau eval (billing_after_eval.json): metered **$26.75753263**,
  billed **$0.00**. Delta O2 từ baseline: **+$1.96895** (dự toán ~$1.97).
- Dừng app: `modal app stop --yes helix-vllm-engine` 15:17 UTC
  (lần đầu không --yes bị hỏi xác nhận interactive và abort — chỉ là
  cờ CLI, không phải lỗi). Sau dừng: endpoint trả "modal-http: invalid
  function call" (đúng kỳ vọng); `modal app list` = 2 app stopped,
  **0 task**.
- Billing sau dừng (billing_after_stop.json): metered **$26.70753269**,
  billed **$0.00** — thấp hơn sau eval $0.05 (điều chỉnh/lag, không phải
  chi phí mới). Delta O2 theo lần đọc này: +$1.91895.
- Billing delayed: billing_delayed.json (xem file).
- Upstream git clean sau GPU (HEAD b5adffa, status trống); fork không đổi
  (94 D + 2 ??). Xem upstream_git_status_after.txt,
  fork_git_status_after.txt.
- KHÔNG commit/push ở đâu. KHÔNG động deck/báo cáo/Drive/GitHub/Canva.

## Tổng chi phí O2 (theo lần đọc sau eval)

| Hạng mục | Metered |
|---|---|
| Train (SFT 9 + DPO 3 bước) | +$0.0773 |
| Deploy + warmup + eval 135 ô + 3 rerun | +$1.8916 |
| **Tổng O2** | **+$1.9690** |
| Billed | **$0.00** (mọi checkpoint) |

Ngân sách chương trình còn lại sau O2 (theo lần đọc sau eval):
$30.7886 − $26.7575 = **$4.03** cho O3 + O1 + O5 (dự toán $2.28).
