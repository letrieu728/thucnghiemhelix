# RUN_LOG — O3: Can thiệp prompt opencode (DESIGN.md, pre-registered 2026-11-20)

## §0. Tái dùng + kiểm chứng offline (TRƯỚC mọi GPU, 2026-11-20 ~22:20 +07)

### Baseline — đính chính (§0.1 DESIGN)
- Baseline là **R8 (0/10, text-only 10/10)**, KHÔNG phải R0. R0 đạt **6/10** trên
  10 bài này (step6 summary.json). Mọi so sánh trong O3 đều đối chiếu với R8
  (B1/B2) và R1 (B3, đối chứng: 4/10, text-only 2/10).
- Baselines TÁI DÙNG từ `evolution-2026-11-18/step6-mini-search/summary.json`,
  không chạy lại (tiết kiệm 20 lượt).

### File tái dùng — sha256 đối chiếu step 6 (byte-identical)
| File | sha256 (O3) | step 6 | Khớp |
|---|---|---|---|
| runner.mts | c5b4b095fdc96ee11bcb8a7efec3392905cbd17024d1c399a47c454da40eef6f | c5b4b095… | YES |
| run_driver.py (gốc, trước sửa) | 21f945da38b9e25cc8b3403b9e2e640982f90dbaa71b510a4a4825f27de735e1 | 21f945da… | YES |
| compute_stats.py (gốc) | 9c6cca4027c965500c1a7cbd7612a07145b218de218b32a3b627bab381d67419 | 9c6cca40… | YES |
| verify_scoring.py (gốc) | c6fc1581d93a813483fea75dfdd87c6adfcc31ed5e7609e8babfa8a31c7cfb50 | c6fc1581… | YES |
| tasks.json | ee27cbc6d73276424fb4fedc3f71c3e3b81f5323faf022b6e744e7610fcbf304 | ee27cbc6… | YES |
| prompt_template.txt | 3e100f24b8d71cb0e62e6e231f0d8c88ff170afdd38fb0dde8a24c1b942019e8 | 3e100f24… | YES |
| recipes/R1-prompt-pi_tools-pi_turn-pi.json | ec1b75d583c17ffbfe603f20cdb8ca9bf8a534fb1cb952f319436acb5341e429 | ec1b75d5… | YES |
| recipes/R8-prompt-opencode_tools-opencode_turn-opencode.json | 6c6ce94cc7e5ea5b35177f303cc415daf90d62f8803177923e3e2ed6b9f67b49 | 6c6ce94c… | YES |
| 01_modal_vllm_rebuild_C_realtool.py (fix log) | c9bd24037c7b1cfcfd915651194e10a88054be7609923f8b421137fd636e486c | c9bd2403… (DESIGN §8) | YES |
| warmup.py (fix log) | 892a96b4e483aebdc3d6fa627b636626ffdf7d355ef77246154f8d0f2f4fae30 | 892a96b4… (DESIGN §8) | YES |
- `recipes/manifest.json` là SUBSET của manifest step 6 (chỉ R1 + R8, entries
  copy verbatim); sha khác manifest đầy đủ là đúng theo thiết kế.

### Driver — thay đổi duy nhất được phép + 1 thay đổi bắt buộc (ghi vào header + run_driver.diff)
- `--prompt-suffix`: hậu tố nối VERBATIM vào cuối user prompt đã xây xong,
  trước khi truyền cho runner.mts; ghi vào result.json (`prompt_suffix`) và
  prompt.txt (prompt.txt giữ đúng prompt đã gửi, gồm hậu tố).
- `--branch` (B1/B2/B3): runs đi vào `runs/<branch>/<task>/` thay vì
  `runs/<recipe>/<task>/`, result.json ghi `branch`. BẮT BUỘC vì B1 và B2
  cùng dùng recipe R8 — không có cờ này hai nhánh sẽ đè lên nhau trong
  runs/R8/. Không động vào scoring/parser/đếm tool/health/classification/
  rerun/resume. Diff đầy đủ: `run_driver.diff` (104 dòng, toàn bộ là header
  + 2 cờ + truyền tham số).
- Dry-run offline (import run_driver, build_prompt trên lcb_001_two_sum):
  I-full và I-min đều có mặt ở cuối prompt, phần còn lại byte-identical
  với prompt gốc (orig 430 bytes; +I-full 645; +I-min 513). PASS.
- compute_stats.py: gom theo nhánh (B1/B2/B3); `wilson` + `mcnemar_exact` +
  `summarise` + `no_tool_stats` verbatim từ step 6; thêm baseline tái dùng +
  McNemar B1/B2-vs-R8, B3-vs-R1 + verdict cơ học theo DESIGN §4.
- verify_scoring.py: logic giữ nguyên; tag thêm branch.
- blend_probe.mts: STEP trỏ sang thư mục O3; danh sách recipe chỉ R1/R8;
  2 sửa cùng họ với sửa probe của step 6 (ghi rõ dưới đây).

### CLI assemble — kiểm chứng lại (DESIGN §3.1)
- R1: 52/52 checks, verification.ok=true,
  contractID opencode-pi-hybrid@0.1.0:59c40e7b2621fbcf. PASS.
- R8: 52/52 checks, verification.ok=true, cùng contractID. PASS.
- Output: `recipes/assemble_R1.json`, `recipes/assemble_R8.json`
  (file giữ nguyên npm echo header như step 6 đã làm; parse từ `{` đầu tiên).

### Runtime blend probe — kiểm chứng lại (DESIGN §3.2, 7/7 mỗi recipe)
- Lần 1: R1 PASS 7/7; R8 FAIL 6/7 — chỉ `prompt_hash_matches_P2_or_normalized`
  sai. Chẩn đoán: prompt hệ thống opencode có dòng 105
  ` Today's date: Fri Nov 20 2026` — thay đổi theo NGÀY, cùng độ dài
  (9620 bytes cả 18/11 lẫn 20/11), nên hash thô khác hằng số P2 (tính
  18/11) trong khi so sánh cùng-lượt với stock (check mạnh) vẫn PASS.
  Đây là lỗi probe, không phải lỗi recipe — cùng họ với lỗi dòng đồng hồ
  của prompt pi mà step 6 đã sửa.
- Sửa 1: `normPrompt` chuẩn hoá thêm dòng ` Today's date:` (như step 6
  chuẩn hoá dòng đồng hồ pi).
- Sửa 2: nhánh opencode của check `prompt_hash_matches_P2_or_normalized`
  so hash THÔ với hằng số P2 — chỉ có thể đúng vào đúng ngày P2 chạy.
  Đổi sang so hash đã chuẩn hoá với stock cùng lượt (check mạnh đã có),
  cùng cách nhánh pi làm. Hằng số P2 chỉ còn in ra tham chiếu, không làm gate.
- Lần 2 (sau sửa): **R1 PASS 7/7, R8 PASS 7/7 — ALL BLEND PROBES PASS.**
  Output: `probes/probe_R1.json`, `probes/probe_R8.json`.

### Trạng thái trước GPU
- Billing trước O3 (`billing_before.json`): metered **$26.7375**, billed **$0.00**.
  (Trần chương trình: $24.79 + $6.00 = $30.79 metered; còn lại ≈ $4.05.)
- `modal app list` trước deploy (`app_list_before_deploy.log`): 0 task đang
  chạy (2 app đều stopped). Đủ điều kiện deploy.
- Upstream git-clean: HEAD b5adffa, `status --porcelain` trống
  (`upstream_git_status_before.txt`).
- Fork: 94 D + 2 ?? như kỳ vọng, HEAD 5d44be6
  (`fork_git_status_before.txt`).
- Token Modal: đã cấp lại 2026-11-20 20:37 (profile letrieu728); billing
  đọc được ở trên xác nhận auth còn hiệu lực.
- KHÔNG commit/push ở đâu. KHÔNG sửa slide/Drive/GitHub/Canva.

## §1. Deploy (fix deploy file — base + helix-lora + helix-lora-realtool)

- Lệnh: `modal deploy 01_modal_vllm_rebuild_C_realtool.py` (`modal_deploy.log`).
  App `helix-vllm-engine`, endpoint
  `https://letrieu728--helix-vllm-engine-vllmserver-serve.us-east.modal.run`.
  Deploy 22:24 +07 (1,55 s). O2 app đã stopped trước đó; deploy này thay thế
  function của cùng app name (O1 sau này sẽ deploy lại file clean của nó).
- Warmup (`warmup_o3.log`, `warmup_o3.json`, `v1_models_o3.json`): OK sau
  150,6 s (15 attempts); health shim_enabled=true, adapters
  [helix-lora, helix-lora-realtool]; models gồm base
  Qwen/Qwen2.5-Coder-7B-Instruct.
- Billing sau deploy: metered $26,7375, billed $0,00 (chưa nhúc nhích — lag).
- App list sau deploy (`app_list_after_deploy.log`): ap-9Jc40NoaZfhr5EX9zqpo3O
  deployed, 1 task.

## §2. Chạy nhánh

- **B1 (R8 + I-full), pilot 1 ô rồi sweep:** pilot lcb_001 FAIL nhưng dùng đủ
  read/write/bash — vòng lặp chạy đúng, hậu tố có trong prompt.txt
  (`pilot_B1.log`). Sweep 10 ô (`sweep_B1.log`): 9 FAIL + 1 INFRA
  (lcb_015 `runner_timeout_600s`, 600,21 s, 0 tool).
  - Gián đoạn runtime giữa chừng: sweep bị ngắt khi đang chạy lcb_020 (chưa có
    result.json). Resume cùng lệnh: SKIP 5 ô đã xong, chạy nốt 5 ô.
  - Rerun duy nhất: lcb_015, `--rerun` với lý do INFRA timeout
    (`rerun_B1_lcb015.log`, `REPLACEMENTS.log`): **PASS** 27,31 s. Ô cũ lưu
    `runs/B1/lcb_015_word_search.attempt1/`.
  - B1 cuối: **1/10 PASS** (lcb_015), 9 FAIL, 0 INFRA. Text-only 0/10.
- **B2 (R8 + I-min), sweep 10 ô (`sweep_B2.log`): 2/10 PASS** (lcb_001,
  lcb_010), 8 FAIL, 0 INFRA. Text-only 3/10 (lcb_002, lcb_005, held2_013).
  Không rerun.
- **B3 (R1 + I-full, đối chứng), sweep 10 ô (`sweep_B3.log`): 6/10 PASS**
  (lcb_001, lcb_005, lcb_015, held2_001, held2_005, held2_013), 4 FAIL,
  0 INFRA. Text-only 0/10. Không rerun.
- Tổng: 31 lượt chạy (30 ô + 1 rerun), 0 ô INFRA còn lại.

## §3. Phân tích + kiểm chứng chấm điểm

- `compute_stats.py` → `summary.json`, `summary.md`. McNemar: B1-vs-R8
  gains 1/losses 0, p=1,0; B2-vs-R8 gains 2/losses 0, p=0,5; B3-vs-R1 gains
  3/losses 1, p=0,625. Verdict cơ học: B1 BEHAVIOR-ONLY, B2 BEHAVIOR-ONLY,
  B3 CONTROL-OK.
- `verify_scoring.py`: checked=30, infra_skipped=0, mismatches=0,
  hash_mismatches=0, recipe_sha_mismatches=0. **0 mismatch.**

## §4. Billing + dừng app

| Checkpoint | Metered | Billed |
|---|---|---|
| Trước O3 | $26,7375 | $0,00 |
| Sau deploy + warmup | $26,7375 | $0,00 |
| Sau B1 | $26,8875 | $0,00 |
| Sau B2 | $27,0375 | $0,00 |
| Sau B3 | $27,1775 | $0,00 |
| Sau khi dừng app | $27,1975 | $0,00 |

- **Tổng O3: +$0,46 metered** (dự toán $0,31; chênh +$0,15 do ô timeout
  600 s + idle giữa các nhánh). Billed $0,00 ở mọi checkpoint — sàn không
  bị vi phạm. Tổng chương trình đến nay: $27,1975 − $24,79 = $2,41/$6,00;
  còn ≈ $3,59 cho O1 + O5 (dự toán $2,32).
- Dừng app: `modal app stop helix-vllm-engine` lần đầu bị từ chối (cần xác
  nhận tương tác); chạy lại với `--yes` → exit 0 (`app_stop_after.log`).
  `app_list_after_stop.log`: ap-9Jc40NoaZfhr5EX9zqpo3O stopped, **0 task**.
- Git sau GPU: upstream clean (b5adffa), fork 94 D + 2 ?? — không đổi so
  với trước GPU.
- KHÔNG commit/push ở đâu. KHÔNG sửa slide/Drive/GitHub/Canva.
