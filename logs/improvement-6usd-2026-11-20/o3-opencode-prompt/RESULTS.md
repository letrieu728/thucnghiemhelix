# RESULTS — O3: Can thiệp prompt opencode (DESIGN.md, pre-registered 2026-11-20)

Ngày chạy: 2026-11-20 (deploy 22:24 +07, sweeps 22:27–22:54 +07, app dừng 22:54 +07).
Model: base `Qwen/Qwen2.5-Coder-7B-Instruct` (cố định). 10 bài của bước 6, 1 lượt/ô.
Tổng lượt mới: **30** (3 nhánh × 10) + **1 rerun INFRA** (B1/lcb_015) = 31 lượt chạy.

## 1. Kết quả chính (từ summary.json; verify_scoring.py: 0 mismatch, 30 ô kiểm tra)

| Nhánh | Recipe + hậu tố | Pass@1 | Wilson 95% | Text-only | Text-only Wilson 95% | Tool calls | Phán quyết (§4) |
|---|---|---|---|---|---|---|---|
| **B1** | R8 + I-full | **1/10** (0,10) | [0,02; 0,40] | **0/10** | [0,00; 0,28] | read 10, write 7, edit 1, bash 7 (25) | **BEHAVIOR-ONLY** |
| **B2** | R8 + I-min | **2/10** (0,20) | [0,06; 0,51] | **3/10** | [0,11; 0,60] | write 7, bash 8 (15) | **BEHAVIOR-ONLY** |
| **B3** (đối chứng) | R1 + I-full | **6/10** (0,60) | [0,31; 0,83] | **0/10** | [0,00; 0,28] | read 11, write 10, edit 6, bash 10 (37) | **CONTROL-OK** |

Baselines TÁI DÙNG từ bước 6 (không chạy lại): **R8 0/10, text-only 10/10**;
**R1 4/10, text-only 2/10**. R0 đạt 6/10 trên 10 bài này và KHÔNG phải baseline
(DESIGN §0.1).

### Áp dụng tiêu chí đăng ký trước (§4)
- **Tiêu chí hành vi** (text-only ≤ 5/10 vs R8 10/10): B1 đạt (0/10), B2 đạt
  (3/10). Cả hai nhánh đều cứu được hành vi dùng tool theo nghĩa mô tả.
- **Tiêu chí kết quả** (Pass@1 ≥ 3/10 vs R8 0/10): B1 KHÔNG đạt (1/10),
  B2 KHÔNG đạt (2/10).
- **Phán quyết: BEHAVIOR-ONLY cho cả B1 và B2** — "model dùng tool nhưng vẫn
  fail — nút thắt chuyển từ hành vi sang chất lượng code". Không nhánh nào
  đạt "rescued".
- **Đối chứng B3: CONTROL-OK** — 6/10 so với R1 4/10, không rớt ≥ 2 bài;
  hậu tố KHÔNG làm hại harness đang chạy tốt (mô tả: +2 bài, xem McNemar dưới).

### McNemar exact 2-phía, KHÁM PHÁ (so với baseline tái dùng)
| So sánh | Cặp | Thắng (FAIL→PASS) | Thua (PASS→FAIL) | p (exact, 2-phía) |
|---|---|---|---|---|
| B1 vs R8 | 10 | 1 | 0 | **1,0** |
| B2 vs R8 | 10 | 2 | 0 | **0,5** |
| B3 vs R1 | 10 | 3 | 1 | **0,625** |

Không có so sánh nào có ý nghĩa thống kê — đúng như DESIGN §4 viết trước:
với R8 ở 0/10, 3 thắng/0 thua cũng chỉ cho p = 0,25. Ngôn từ được phép:
"can thiệp mô tả làm giảm text-only từ 10/10 xuống 0/10 (B1) / 3/10 (B2)
trên 10 bài" — không hơn. **Không nâng 1/10 hay 2/10 thành "thắng có ý nghĩa".**

### So sánh liều (mô tả)
- I-full (B1) cứu hành vi triệt để hơn I-min (B2): text-only 0/10 so với 3/10.
- Nhưng Pass@1 không hơn: B1 1/10 < B2 2/10 (chênh 1 bài, trong nhiễu n=10).
- B2 không bao giờ dùng read/edit (hậu tố chỉ nhắc write + bash) — 15 tool
  call, toàn write/bash. B1 dùng đủ 4 tool (read 10 lần — đúng chỉ dẫn "read
  trước"). B3 dùng nhiều tool nhất (37 call, trung bình 3,8 bước/ô so với
  B1 2,7 và B2 1,8).

## 2. Bảng 10 bài × 3 nhánh (PASS/FAIL; cột R8/R1 tái dùng)

| task_id | B1 | B2 | B3 | R8 (tái dùng) | R1 (tái dùng) |
|---|---|---|---|---|---|
| lcb_001_two_sum | FAIL | PASS | PASS | FAIL | PASS |
| lcb_002_valid_parentheses | FAIL | FAIL | FAIL | FAIL | FAIL |
| lcb_005_binary_search | FAIL | FAIL | PASS | FAIL | PASS |
| lcb_010_number_of_islands | FAIL | PASS | FAIL | FAIL | PASS |
| lcb_015_word_search | PASS | FAIL | PASS | FAIL | FAIL |
| lcb_020_min_jumps | FAIL | FAIL | FAIL | FAIL | FAIL |
| held2_001_edit_distance | FAIL | FAIL | PASS | FAIL | PASS |
| held2_005_word_ladder | FAIL | FAIL | PASS | FAIL | FAIL |
| held2_009_next_permutation | FAIL | FAIL | FAIL | FAIL | FAIL |
| held2_013_decode_ways | FAIL | FAIL | PASS | FAIL | FAIL |

- 3 bài không nhánh nào pass: lcb_002, lcb_020, held2_009 (cả R1 bước 6 cũng
  fail cả 3 — chúng khó với base trên cả hai ngăn xếp).
- B1 pass duy nhất lcb_015 — và đó là ô đã INFRA timeout ở lượt đầu (xem §3).

## 3. Hạ tầng / rerun
- **INFRA duy nhất: B1/lcb_015_word_search, `runner_timeout_600s`** (600,21 s,
  0 tool call) ở lượt đầu. Rerun 1 lần theo quy tắc DESIGN §3 (tối đa 1
  rerun/ô): **PASS** (27,31 s, read+write+bash). Ghi trong REPLACEMENTS.log;
  ô cũ lưu ở `runs/B1/lcb_015_word_search.attempt1/`. Không có rerun nào khác.
- Gián đoạn runtime giữa chừng: sweep B1 bị ngắt khi đang chạy lcb_020
  (không có result.json); resume bằng cùng lệnh driver — driver SKIP 5 ô đã
  xong, chạy nốt 5 ô còn lại. Không ô nào chạy trùng.
- Không có ô INFRA nào ở B2/B3. Tổng cộng 31 lượt chạy, 30 ô cuối cùng đều
  scored (0 INFRA còn lại).

## 4. Chi phí (billing snapshot, metered / billed)
| Checkpoint | Metered | Billed | Δ metered |
|---|---|---|---|
| Trước O3 | $26,7375 | $0,00 | — |
| Sau deploy + warmup | $26,7375 | $0,00 | $0,00 (lag) |
| Sau B1 (11 lượt incl. rerun) | $26,8875 | $0,00 | +$0,15 |
| Sau B2 (10 lượt) | $27,0375 | $0,00 | +$0,15 |
| Sau B3 (10 lượt) | $27,1775 | $0,00 | +$0,14 |
| Sau khi dừng app | $27,1975 | $0,00 | +$0,02 |
| **Tổng O3** | | | **+$0,46** |

- Dự toán DESIGN §5 là $0,31; thực tế $0,46 (+$0,15). Phần chênh chủ yếu là ô
  timeout 600 s của B1/lcb_015 (endpoint bận đủ 600 s) + thời gian idle của
  app giữa các nhánh. Vẫn trong ngân sách chương trình: tổng chương trình
  đến nay $27,1975 − $24,79 = **$2,41 / $6,00**; còn lại ≈ **$3,59** cho
  O1 ($1,77 dự toán) + O5 ($0,55 dự toán) = $2,32.
- **Billed = $0,00 ở mọi checkpoint** — quy tắc sàn không bị vi phạm.
- Tỉ lệ quan sát: ~$0,014–0,015/lượt (cao hơn $0,007 dự toán vì gồm deploy
  share + timeout + idle; lượt chạy thuần ~$0,007–0,010).

## 5. Diễn giải (theo DESIGN §4, không vượt quá những gì đã đăng ký)
- **Cơ chế thứ hai KHÔNG được xác nhận đầy đủ.** Chỉ dẫn tường minh cứu được
  hành vi (text-only 10/10 → 0/10 với I-full, 3/10 với I-min) nhưng không
  cứu được kết quả (1/10 và 2/10, đều dưới ngưỡng 3/10, p không ý nghĩa).
  Nút thắt trên ngăn xếp opencode, sau khi model đã chịu dùng tool, là chất
  lượng code nó viết ra — đúng phán quyết BEHAVIOR-ONLY đã đăng ký.
- **Không kết luận "prompt dài là nguyên nhân"** — chưa tách được (DESIGN §0/§4).
- **Hậu tố không có tác dụng phụ đo được** trên harness đang chạy tốt: B3
  6/10 so với R1 4/10 (gains 3, losses 1 — lcb_010 rớt, held2_005 + lcb_015
  + held2_013 thêm; p = 0,625, mô tả).
- **Caveat run-epoch (DESIGN §6):** baseline R8/R1 tái dùng từ đợt chạy bước 6
  (18/11), khác đợt với B1/B2/B3 (20/11). B2 nằm sát ngưỡng hành vi
  (text-only 3/10, trong khoảng) và cả hai nhánh đều sát ngưỡng kết quả
  (1–2/10 so với ngưỡng 3/10) — với n=10 và 1 lượt/ô, mọi kết luận đều mô tả.
- Điểm tốt hơn (theo quy tắc báo cáo): hành vi dùng tool trên opencode đã
  đổi hẳn — từ 10/10 lượt "trả lời bằng text" ở R8 xuống 0/10 (B1) và 3/10
  (B2); model làm đúng quy trình read → write/edit → bash khi được chỉ dẫn
  đầy đủ; và hậu tố không phá harness pi đang chạy tốt.

## 6. Deliverables (thư mục này)
- `DESIGN.md`, `RUN_LOG.md`, `RESULTS.md` (file này), `summary.json`, `summary.md`
- `runner.mts`, `run_driver.py` (+ `run_driver.diff`), `compute_stats.py`,
  `verify_scoring.py`
- `recipes/` (R1/R8 + manifest subset + `assemble_R1.json`, `assemble_R8.json`
  52/52), `probes/` (blend_probe.mts + `probe_R1.json`, `probe_R8.json` 7/7)
- `01_modal_vllm_rebuild_C_realtool.py`, `warmup.py` (sha256 khớp DESIGN §8)
- Billing: `billing_before.json`, `billing_after_deploy.json`,
  `billing_after_B1.json`, `billing_after_B2.json`, `billing_after_B3.json`,
  `billing_after_stop.json`
- App list: `app_list_before_deploy.log`, `app_list_after_deploy.log`,
  `app_list_after_stop.log`, `app_stop_after.log`
- Git status: `upstream_git_status_before.txt` (clean, b5adffa),
  `upstream_git_status_after.txt` (clean),
  `fork_git_status_before.txt` / `fork_git_status_after.txt` (94 D + 2 ??, không đổi)
- Logs: `modal_deploy.log`, `warmup_o3.log`, `warmup_o3.json`,
  `v1_models_o3.json`, `pilot_B1.log`, `sweep_B1.log`, `sweep_B2.log`,
  `sweep_B3.log`, `rerun_B1_lcb015.log`, `REPLACEMENTS.log`,
  `health_check_B1/B2/B3_*.json`
- `runs/B1/`, `runs/B2/`, `runs/B3/` (30 ô) + `runs/B1/lcb_015_word_search.attempt1/`
- App: đã dừng (`modal app stop --yes helix-vllm-engine`); `app_list_after_stop.log`
  xác nhận 0 task đang chạy.
- KHÔNG commit/push ở đâu. KHÔNG sửa slide/Drive/GitHub/Canva.
