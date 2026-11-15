# Nhật ký chạy GPU — đợt bổ sung hàng 2+5 (HELIX), 2026-11-15

Đợt này KHÔNG phải vòng 3. Số vòng 2 giữ nguyên làm lịch sử, không sửa
hồi tố. Mọi giờ dưới đây là giờ +07 (Asia/Ho_Chi_Minh) trừ khi ghi UTC.

## 0. Kiểm tra trước khi chạy (C0 — đạt)

- Test suite: 17/17 (modal-venv), chạy lại sau đợt chạy vẫn 17/17.
- Checksum 520 trace cũ ghi vào `trace_checksums_before_suppl.txt`;
  sau đợt chạy verify lại: 520/520 OK, không file cũ nào đổi.
- Staging (§3 kế hoạch): backup 3 file `data/processed/` vào
  `staging-backup/` (hash khớp manifest vòng 2: SFT `4f4d6ad8…`, DPO cũ
  `a40fa5b1…`); chép `dpo_pairs_expanded.jsonl` đè `dpo_pairs.jsonl`
  (hash `47b8e075…`, 19 dòng); viết lại manifest bằng script mới
  `stage_supplement_provenance.py` (chỉ đổi `generated_at`, `extractor`,
  `counts` {19,19}, hash DPO; mọi trường khác giữ nguyên). Cổng
  provenance local: gọi đúng `validate_data()` của `04` — PASS
  (SFT 19 / DPO 19). KHÔNG dùng `--allow-unverified-data` ở bất kỳ đâu.
- Adapter vòng 2 sao lưu: volume V1 không hỗ trợ `cp -r` nên chép từng
  file (12 file) `helix-lora-final` →
  `helix-lora-final-round2-20261112`; verify 12 file / 177.423.312 byte
  khớp nguồn. Lệnh: `modal volume cp helix-adapters <src> <dst>` từng file.

## 1. Endpoint lần 1 + judge (A10G)

- Deploy: `modal deploy closed-loop/scripts/01_modal_vllm.py`,
  18:33:28–18:33:31. URL:
  `https://letrieu728--helix-vllm-engine-vllmserver-serve.us-east.modal.run`
- Verify: `/health` 200, `lora_enabled: true`; `/v1/models` có 2 model,
  base `max_model_len: 8192`; routing: completion với id base trả về id
  base, với `helix-lora` trả về `helix-lora`. Cold start lần đầu ~71s.
- Judge runner: `run_judge.py` — prompt lấy nguyên văn từ 2 block
  ```text của `JUDGE_PROMPT.md` lúc chạy (không gõ lại); base model,
  temp 0.0, max_tokens 512, seed 20261115; parse JSON nghiêm ngặt +
  retry đúng 1 lần; append-only JSONL.
- **Lệch khỏi bản nháp đầu (đã ghi nhận, không sửa prompt/nhãn):**
  validator bản đầu yêu cầu trường `evidence` phải là string; model bỏ
  hẳn key này khi nhãn clean (giá trị quy định cho clean là `""`) nên 3
  ô pilot bị `unparseable`. Sửa validator theo đúng 4 kiểm tra liệt kê
  ở `JUDGE_PROMPT.md` §5 (evidence không rỗng CHỈ bắt buộc khi
  degenerate; thiếu/null → `""`). File 3 dòng cũ giữ nguyên tại
  `judge_runs/2026-11-15/judge_results_pilot_validator-v1.jsonl`; 3 ô
  chạy lại với cùng request nguyên văn cho raw response giống hệt từng
  byte (đã verify) — chỉ quyết định parse đổi, nhãn lấy từ model.
- Pilot 10 ô: toàn `clean`, 0 retry, latency trung bình 2,33s/ô
  (ước tính 15s). **Checkpoint C1:** chiếu tổng ≈ $4,99 < $7,20 → full 169.
- Judge full 169 ô: 18:36:24–18:42:34 (pilot tính vào tổng, không chấm
  lại). Kết quả: **167 clean, 0 suspicious, 0 degenerate, 2 unparseable
  (1,18%)**. Latency tổng 392,6s, trung bình 2,323s, 3 retry. 2 ô
  unparseable đều là JSON hợp lệ bọc trong fence ```json (retry giống
  hệt) — giữ `unparseable` theo §5, không suy nhãn tay; nội dung trong
  fence ở cả 2 ô đều là clean/[] (ghi nhận mô tả, không tính là nhãn).
  Nhất trí heuristic–judge: 167/167 ô parse được (100%; heuristic clean
  trên cả 169 ô). Dấu hiệu chất lượng: chỉ 91 reason phân biệt / 169 ô;
  69 ô trùng reason với ô khác cùng task (3 solution edit-distance khác
  nhau nhận reason giống hệt từng chữ). Judge là model 7B cùng họ với
  solution — "0 degenerate" KHÔNG phải chứng minh không có bám test.
- **Checkpoint C2:** chiếu tổng ≈ $4,58 < $8 → tiếp tục train. App giữ
  nguyên (container tự scale-to-zero sau 180s idle trong lúc train).

## 2. Train (A100-SXM4-40GB)

- Lệnh: `modal run closed-loop/scripts/04_train_lora.py --stage
  sft_then_dpo --epochs 3`, 18:42:54–18:46:09 (wall 195s), exit 0.
  Không cờ nào khác; config đúng mặc định vòng 2.
- Run id: `20261115T114301-bcda6414`. Metadata verify (C3 PASS):
  sample_counts SFT 19 / DPO 19, hash khớp file đã stage,
  `provenance.allow_dry_run == false`, `allow_unverified_data == false`,
  epochs 3, lr 2e-4 / DPO 5e-6, r=16, alpha=32, dropout 0,05, seed 42.
- SFT 9 bước: 0,9999 / 1,1355 / 1,0309 / 0,8945 / 0,7127 / 0,5722 /
  0,5640 / 0,4932 / 0,4953 (vòng 2: 1,00→0,49 — gần như giống hệt, đúng
  kỳ vọng vì SFT không đổi). Runtime 18,1s.
- DPO 9 bước: 0,6931 / 0,6931 / 0,6839 / 0,6533 / 0,6253 / 0,6192 /
  0,6223 / 0,5838 / 0,5918 (vòng 2, 3 bước: 0,693→0,660). Reward
  accuracy: 0 / 0 / 0,667 / 1,0 / 0,875 / 1,0 / 0,875 / 1,0 / 1,0.
  Margin: 0 / 0 / 0,019 / 0,082 / 0,142 / 0,155 / 0,150 / 0,234 / 0,216.
  Runtime 35,3s. DPO CÓ học tín hiệu preference trên tập train
  (loss giảm, accuracy đạt 1,0 từ bước 4).
- Artifacts: `closed-loop/data/training_runs/20261115T114301-bcda6414/`
  (loss_history.json, metadata.json, versions.json) + log đầy đủ
  `train_log_suppl.txt`.
- Lưu adapter mới: chép từng file (12) `helix-lora-final` →
  `helix-lora-supplement-20261115`; verify 12 file / 177.426.357 byte
  khớp. Chỉ metadata.json (1133→1136) và loss_history.json (3215→6257)
  khác kích thước so với vòng 2; adapter safetensors cùng kích thước.

## 3. Redeploy + đo lại (A10G, model helix-lora, temp 0.0, tag suppl)

- Redeploy 18:46:47: Modal báo "no changes detected" (code không đổi)
  nhưng container đã scale-to-zero trong lúc train và cold-start lại
  (~60s) SAU khi adapter mới commit (18:46:01); timestamp `created` của
  model trong `/v1/models` là instance mới, sau thời điểm train xong;
  routing verify lại đúng cả 2 id. Không train nào xen giữa.
- REBUILD-suppl 80 ô: chunk 1 (10 task đầu) 18:48:07–19:04:38, 30/40;
  chunk 2 19:04:43–19:17:58, 35/40. Tổng **65/80**, latency 1771,7s.
- Held-out-suppl 60 ô (CHỈ model mới, base không chạy lại): chunk 1
  (8 task) 19:18:01–19:29:59, 30/32; chunk 2 (7 task) 19:30:03–19:45:42,
  21/28. Tổng **51/60**, latency 1645,8s.
- Mọi trace mới: mode live, model `helix-lora`, temperature 0.0,
  sample 0; tên file `suppl_lcb_*_*.json` (80) và
  `suppl_helix-lora_held2_*_*.json` (60); không đụng độ file cũ.

## 4. Re-verify + thống kê (C4 — đạt, offline)

- Script mới `suppl_stats.py` (tái dùng `reverify` của `round2_stats.py`):
  re-verify 140/140 trace mới → **0 mismatch**. Kết quả đầy đủ trong
  `suppl_stats.json` + biểu đồ `suppl_comparison_plot.svg/.png`.
- REBUILD-suppl 65/80 (Wilson 95% 0,7134–0,8829). Theo harness:
  minimal 14/20, pi-mono 16/20, hermes-agent 17/20, opencode 18/20.
  Union 20/20 task (vòng 2: rebuild2 19/20, build2 17/20).
  McNemar vs BUILD2 60/80: 7 gains / 2 losses, p=0,1797.
  McNemar vs REBUILD2 66/80: 2 gains / 3 losses, p=1,0.
- HELDOUT-suppl 51/60 (Wilson 95% 0,7389–0,9190). Theo harness:
  minimal 13/15, pi-mono 11/15, hermes-agent 13/15, opencode 14/15.
  Union 14/15 (cùng base và LoRA vòng 2; `held2_009` không harness nào
  giải được ở cả 3 model).
  McNemar vs base 50/60: 4 gains / 3 losses, p=1,0.
  McNemar vs LoRA vòng 2 53/60: 0 gains / 2 losses, p=0,5
  (2 loss đều ở pi-mono: `held2_013_decode_ways`, `held2_014_rotten_oranges`).
- **Kết luận DPO (trung thực):** DPO học được trên loss train nhưng
  KHÔNG cải thiện Pass@1 đo được: train −1 ô so với LoRA vòng 2,
  held-out −2 ô, mọi McNemar đều không có ý nghĩa. Không có bằng chứng
  tổng quát hóa thêm từ 19 cặp; cũng không có hồi quy có ý nghĩa.
  Không chạy lại, không p-hack, một lần chạy duy nhất.

## 5. Khôi phục + dừng (Bước 11)

- `data/processed/` khôi phục từ `staging-backup/`, verify hash khớp
  đúng trạng thái vòng 2 (SFT `4f4d6ad8…`, DPO cũ `a40fa5b1…` 6 dòng,
  manifest `273cd9a7…`, generated_at 2026-11-12).
- `helix-lora-final` khôi phục từ `helix-lora-final-round2-20261112`
  (chép từng file, 12 file); verify 12 file / 177.423.312 byte khớp
  bản gốc vòng 2. Adapter bổ sung vẫn ở
  `helix-lora-supplement-20261115`. Backup vòng 1
  (`helix-lora-final-backup-20261112`) và `...-20261104` không động tới
  (timestamp vẫn 2026-11-12). Không động fork, volume kgr1, Drive, GitHub.
- App dừng: `modal app stop -y ap-n6JsYM7JgfeSd4pTqWdfsp` 19:46:50;
  `modal app list` sau đó: cả 2 app `stopped`, 0 task (file
  `modal_app_list_after_stop.txt`); endpoint `/health` trả HTTP 404.

## 6. Chi phí (giờ +07; giá Modal đọc từ `modal billing rates`)

GPU thực tế: serving A10G ($1,10/giờ), train A100-SXM4-40GB ($2,10/giờ).
Quy ước kế hoạch tính bảo thủ theo giá A100-80GB $2,50/giờ + hệ số 1,15.

| Bước | Thời gian tính phí | $2,50/giờ ×1,15 | Thực tế theo GPU dùng |
|---|---|---|---|
| Deploy ×2 + idle/scaledown (ước đệm §6) | 1080s | $0,75 | (nằm trong bill A10G) |
| Judge full 169 ô (latency thật 392,6s) | 451,5s | $0,31 | A10G |
| Train (ước §6 1500s; wall thật 195s) | 1500s | $1,04 | A100-40GB bill $0,11 |
| REBUILD-suppl (latency thật 1771,7s) | 2037,5s | $1,42 | A10G |
| Held-out-suppl (latency thật 1645,8s) | 1892,7s | $1,31 | A10G |
| **Tổng (quy ước bảo thủ)** | **6961,7s** | **$4,83** | — |
| **Bill thật Modal hôm nay** | — | — | **$1,53** |

Bill thật (`modal billing report --for today --show-resources`, file
`modal_billing_today.txt`): serving app A10G $1,3269 + CPU $0,0577 +
memory $0,0257 ≈ $1,41; train app A100-40GB $0,1106 + egress $0,0080 +
CPU/memory $0,0058 ≈ $0,12; tổng $1,5347. Billing summary: metered
$13,17 − credits $12,51 − egress allowance = **billed $0,00** (chỉ dùng
credit, không động thẻ). Cả hai con số đều dưới cap $8. Lưu ý: bill có
thể lag nhẹ; số $1,53 là số đọc được ngay sau khi dừng app.

## 7. File mới tạo trong đợt này

Trong `results/2026-11-15-hang2-hang5/`: `stage_supplement_provenance.py`,
`run_judge.py`, `suppl_stats.py`, `trace_checksums_before_suppl.txt`,
`staging-backup/` (3 file), `judge_runs/2026-11-15/judge_results.jsonl`
(169 dòng) + `judge_results_pilot_validator-v1.jsonl` (3 dòng),
`train_log_suppl.txt`, 4 log eval (`eval_*_suppl_chunk*.log`),
`suppl_stats.json`, `suppl_comparison_plot.svg/.png`, 5 file
`volume_*.json`, `modal_billing_today.txt`,
`modal_app_list_after_stop.txt`, file nhật ký này.
Ngoài thư mục: 140 trace `suppl_*` trong
`closed-loop/data/raw_traces/`; `closed-loop/data/training_runs/
20261115T114301-bcda6414/` (3 file). Volume `helix-adapters` thêm 2 thư
mục: `helix-lora-final-round2-20261112` và
`helix-lora-supplement-20261115` (+ `runs/20261115T114301-bcda6414/` do
script 04 tạo). Không file chuẩn bị nào trong thư mục đợt này bị sửa;
không push GitHub, không động Drive.

## 8. Còn sót / chưa chắc chắn

- Biểu đồ: lần chạy đầu bằng modal-venv thiếu matplotlib nên bỏ qua;
  chạy lại bằng python hệ thống (matplotlib 3.6.3) cho cùng số liệu và
  đã lưu SVG/PNG.
- 2 ô judge `unparseable` do fence ```json — theo đúng §5, không có
  nhãn; nếu cần nhãn cho 2 ô này thì phải là đợt chấm khác (không tự ý
  sửa prompt hay suy nhãn).
- Judge 7B cùng họ: nhãn judge chỉ là sàng lọc; tuyên bố mạnh cần chấm
  kép bởi người (RUBRIC §7) — ngoài phạm vi nhiệm vụ GPU này.
- Bill Modal có thể cập nhật muộn; nếu parent cần số cuối cùng thì đọc
  lại `modal billing report --for today` sau vài giờ.
