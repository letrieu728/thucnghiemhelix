# RUN_LOG — O1: Lặp lại toàn bộ 135 ô của O2, 1 lần (20/11/2026)

Múi giờ ghi log: UTC trong file (giờ +07 = UTC+7). Thiết kế đăng ký trước:
DESIGN.md trong thư mục này. Thứ tự bắt buộc: chạy SAU O2 (O2 đã xong,
C1+C2 ĐẠT). O2 là read-only đối với bước này — không sửa file O2 nào.

## Giai đoạn 0 — Tái dùng (diff-verified) + billing + git (TRƯỚC mọi GPU)

- Token Modal FRESH (cấp lại 20/11 20:37 +07, profile letrieu728, verified).
- Billing trước O1 (billing_before_o1.json): metered **$27.16753521**,
  billed **$0.00**. Trần chương trình: $24.78857824 (baseline O2) + $6.00
  = **$30.78857824** tuyệt đối. Còn lại ≈ $3.62 cho O1 + O5
  (dự toán $1.77 + $0.55 = $2.32).
- `modal app list` trước deploy (app_list_before_deploy.log): 2 app đều
  stopped, **0 task** đang chạy.
- Upstream git clean trước GPU (HEAD b5adffa, status trống);
  fork 94 D + 2 ?? (đúng kỳ vọng, HEAD 5d44be6).
  Xem upstream_git_status_before.txt, fork_git_status_before.txt.
- File tái dùng từ O2 (copy vào thư mục này, diff-verified):
  - byte-identical (sha256 khớp O2): tasks.json
    (ba891fef…), prompt_template.txt (3e100f24…),
    01_modal_vllm_rebuild_C_clean.py (20b698ca… — bản có --max-loras 3
    và helix-lora-clean trong danh sách adapter),
    warmup.py (892a96b4…).
  - chỉ khác thư mục đích runs-repeat/ (+ ghi chú docstring):
    run_driver.py (run_driver.diff), compute_stats.py
    (compute_stats.diff), verify_scoring.py (verify_scoring.diff).
    Không động scoring/parser/đếm tool/health/phân loại/rerun/resume.
  - train script KHÔNG chạy lại (adapter helix-lora-clean đã train xong
    ở O2; bước này chỉ lặp đánh giá).

## Giai đoạn 5 — Đánh giá, nhánh clean (45 ô, pi-mono, 1 lượt/ô cho lần lặp)

Thứ tự chạy (như O2: clean → base → realtool; xem §6 về cắt giảm).
- Sweep clean 45/45 (clean_full_pi-mono.log): 33 PASS / 8 FAIL / **4 INFRA**
  (tất cả harness_error, finish=provider_error):
  held2_003_n_queens_count (500, 342.6s), held2_015_longest_consecutive
  (400 context-length 8192 vượt ở bước 11, 340.6s),
  held3_005_top_k_frequent (500, 319.3s), held3_010_house_robber
  (500, 324.3s). 4 ô INFRA đốt ~21.8 phút/46.5 phút wall của sweep
  (mỗi ô ~5.5 phút do CLI retry nội bộ trước khi bỏ).
- Rerun INFRA (mỗi ô ĐÚNG 1 lần, rerun_infra_pi-mono_clean.log):
  cả 4 đều **PASS** (49.8s / 21.8s / 23.1s / 23.5s).
  REPLACEMENTS.log: 4 dòng; ô cũ lưu *.attempt1/.
- Clean cuối: **37 PASS / 8 FAIL / 0 INFRA** (45 ô).
  (Lưu ý đếm: glob thô thấy 49 result.json vì gồm 4 attempt1 đã lưu trữ;
  các script phân tích bỏ qua thư mục .attempt.)

## Checkpoint chi phí sau 45 ô đầu — QUYẾT ĐỊNH CẮT GIẢM (theo DESIGN §5,
chỉ theo billing, không theo kết quả)

- Billing sau clean45 + reruns (billing_after_clean45_reruns.json):
  metered **$28.28754044**, billed **$0.00**.
  Chương trình đã dùng **$3.4990/$6.00**; còn **$2.5010** cho O1-phần-còn-lại + O5.
- Tỉ lệ quan sát (phương pháp checkpoint của O2): deploy+45 ô = +$1.1200;
  eval-only (trừ deploy) **$0.0238/ô**; thận trọng (gộp deploy) $0.0249/ô.
  Tỉ lệ cao vì 4 ô INFRA đốt 21.8/46.5 phút wall (deployed_apps +$1.0692,
  ephemeral không đổi — toàn bộ là GPU wall-clock, không phải lag).
  Tỉ lệ ô tốt (trừ INFRA) ~$0.0139/ô, khớp O2 ($0.0138/ô) — nhưng quy tắc
  đăng ký trước dùng tỉ lệ quan sát all-in, không trừ ngoại lệ INFRA.
- Dự báo tổng chương trình (phương pháp O2: ô còn lại × tỉ lệ quan sát ×1.2
  + O5 theo tỉ lệ ngân sách $0.55):
  - O1 đủ (90 ô base+realtool): **$6.62–$6.85 > trần $6.00 → VƯỢT.**
  - Cắt bước 1 (bỏ nhánh cũ realtool, còn 45 ô base): **$5.33–$5.50 < $6.00.**
- **QUYẾT ĐỊNH: áp dụng cắt giảm DESIGN §5 bước 1 — BỎ nhánh
  `helix-lora-realtool` (45 lượt) khỏi O1.** O1 còn 90 lượt:
  clean 45 (đã xong) + base 45 (sắp chạy). So sánh CHÍNH (clean vs base
  trên 30 bài chưa thấy) giữ nguyên đầy đủ; số realtool của O2 (35/45)
  ở lại mức 1 lượt/ô, và so sánh clean-vs-realtool không có lượt lặp.
  Cắt giảm này do billing, không do kết quả (chưa có số base/realtool nào
  lúc quyết định). Ghi chú cho O6: lặp realtool bị cắt theo quy tắc §5.

## Giai đoạn 6 — Đánh giá, nhánh base (45 ô) + phân tích

- Sweep base 45/45 (base_full_pi-mono.log): 31 PASS / 14 FAIL / **0 INFRA**,
  không rerun. Base cuối lượt O1: **31/45** (lượt O2: 33/45).
- verify_scoring.py: **checked=90, infra_skipped=0, mismatches=0,
  hash_mismatches=0** (exit 0). compute_stats.py → summary.json +
  summary.md (chỉ lượt O1: base 31/45, clean 37/45; hàng realtool 0/0 =
  KHÔNG CHẠY do cắt giảm, xem RESULTS.md).
- compute_stats_o1.py (mới, chỉ phân tích 2 lượt) → o1_2run_summary.json +
  o1_2run_summary.md. Kết quả đầy đủ ở RESULTS.md:
  - Đồng thuận: base 31/45 (0,69), clean 40/45 (0,89).
  - Gộp 2 lượt (mô tả): clean chính 50/60 [0,7197, 0,9069], base 42/60
    [0,5749, 0,8010]; đủ 45 bài clean 71/90, base 64/90.
  - McNemar chính 30 bài, RIÊNG từng lượt: O2 p=0,4531 (gains 5/losses 2);
    O1 p=0,0625 (gains 5/losses 0). Không gộp p-value.
  - Base drift trong chương trình: **14/45 ô đổi kết quả** (8 PASS→FAIL,
    6 FAIL→PASS) → câu drift ≥ 4 bài kích hoạt, ghi cho O6.
  - Đọc lại phán quyết O2: C1+C2 đạt cả hai lượt →
    "phán quyết O2 ổn định qua 2 lượt".

## Giai đoạn 7 — Billing + dừng app + git sau GPU

- Billing sau eval (billing_after_eval.json): metered **$28.66754063**,
  billed **$0.00**. Delta O1 từ trước O1: +$1.5000 (deploy + warmup +
  90 ô + 4 rerun INFRA).
- Dừng app: `modal app stop --yes helix-vllm-engine` 17:16 UTC, exit 0
  (app_stop_after_eval.log). Sau dừng: endpoint trả
  "modal-http: invalid function call" (đúng kỳ vọng);
  `modal app list` = 3 app stopped, **0 task** (app_list_after_stop.log;
  lần đọc ngay sau stop hiện 1 task thoáng qua, đọc lại sau 20s = 0 —
  chỉ là đếm trễ, app đã stopped).
- Billing sau dừng (billing_after_stop.json): metered **$28.69754069**,
  billed **$0.00** (cao hơn sau eval $0.03 — điều chỉnh/lag, như O2).
  Billing delayed: billing_delayed.json (xem file).
- Upstream git clean sau GPU (HEAD b5adffa, status trống); fork không đổi
  (94 D + 2 ??, diff với trước GPU trống). Xem upstream_git_status_after.txt,
  fork_git_status_after.txt.
- KHÔNG commit/push ở đâu. KHÔNG động deck/báo cáo/Drive/GitHub/Canva.
- KHÔNG sửa file O2 nào (RESULTS.md của O2 giữ nguyên; phán quyết đọc lại
  chỉ ghi trong RESULTS.md của O1).

## Tổng chi phí O1 (theo lần đọc sau dừng)

| Hạng mục | Metered |
|---|---|
| Deploy + warmup (1 lần warmup lỗi timeout /v1/models, chạy lại OK 23,0s) | +$0.0500 |
| Sweep clean 45 ô + 4 rerun INFRA | +$1.0700 |
| Sweep base 45 ô | +$0.3800 |
| Điều chỉnh/lag sau dừng | +$0.0300 |
| **Tổng O1 (90 ô + 4 rerun)** | **+$1.5300** |
| Billed | **$0.00** (mọi checkpoint) |

Ngân sách chương trình còn lại sau O1 (theo lần đọc sau dừng):
$30.7886 − $28.6975 = **$2.09** cho O5 (dự toán $0.55).
- Billing delayed (billing_delayed.json, ~2 phút sau dừng): metered
  **$28.76754070**, billed **$0.00** (+$0.07 so với sau dừng — lag/điều chỉnh,
  cùng kiểu đã thấy ở O2/O3). Chương trình đến nay $3.98/$6.00; còn $2.02
  cho O5 (dự toán $0.55).
