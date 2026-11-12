# Kiểm tra carry-over: kết quả offline ở a090aba có còn đúng ở cc44b7b không (2026-11-12)

Ngày kiểm tra: 2026-11-12. Repo: fork `Vietng-XPrince7/HELIX`.
Phương pháp: `git diff` thuần túy giữa hai commit, không cần npm, không
chạy verifier. Không gọi model.

## Lệnh và kết quả

```
git diff --stat a090aba cc44b7b -- . ':!closed-loop'
# (không có output: 0 file thay đổi ngoài closed-loop/)

git diff --shortstat a090aba cc44b7b -- closed-loop
# 45 files changed, 1497 insertions(+), 71 deletions(-)
```

45 file thay đổi trong `closed-loop/` gồm: 40 trace REBUILD mới trong
`data/raw_traces/`, `REBUILD_REPORT.md`, `data/rebuild_comparison_plot.png`,
`notebooks/evaluate_rebuild.py`, `scripts/01_modal_vllm.py` và
`scripts/02_run_helix_eval.py`. Không file nào ngoài `closed-loop/` thay
đổi — toàn bộ code TypeScript, contract, fixture và artifact của upstream
đều giống hệt ở hai commit.

## Diễn giải

Mọi kết quả kiểm tra offline đã chạy trên `a090aba` (typecheck PASS,
assembly contract PASS, flow graph PASS, executable audit PASS, 3 artifact
FAIL, 101 symlink hỏng, bộ test 823–834 case) đều **carry-over nguyên vẹn
sang `cc44b7b`** đối với phần upstream, vì phần đó không đổi một byte nào.
Phần thay đổi duy nhất (trace REBUILD + báo cáo + script runner) đã được
kiểm tra chéo riêng trong
[results/2026-11-12-closed-loop-trace-audit.md](./2026-11-12-closed-loop-trace-audit.md).

## Kiểm tra symlink fixture (cùng ngày)

Script mới `scripts/check_fixture_symlinks.py` (chỉ dùng stdlib, không cần
npm) chạy trên cả bản clone upstream lẫn bản clone fork đều cho: **101
symlink, 101 hỏng, 0 nguyên vẹn**, tất cả trỏ về đường dẫn tuyệt đối
`/home/HarnessLego-pi-lcb-eval/...` trên máy của tác giả. Output đầy đủ:
[results/2026-11-12-fixture-symlink-check.md](./2026-11-12-fixture-symlink-check.md).
Cassette regeneration vẫn bị chặn như đã ghi ngày 11/11; không có thay đổi.

## Tình trạng các bản sửa ngày 11/11

"CHƯA PUSH" trong `RESULTS.md` nghĩa là chưa push lên repo upstream
(HKUDS/HELIX), không phải bị mất: bằng chứng các bản sửa đều đã nằm trong
repo này — audit đã regenerate trong
`results/2026-11-11-fixed-artifacts/` (JSON + Markdown), manifest split đã
sửa trong cùng thư mục, và báo cáo task-parity smoke-subset (13/13) chính
là file `results/18-task-parity-smoke-subset.txt` kèm log verify 19–20.
Không cần khôi phục gì thêm; muốn đưa các bản sửa này lên upstream thì cần
mở pull request từ một checkout của upstream, việc đó nằm ngoài phạm vi
offline của repo này.

## Phần offline KHÔNG làm lại ngày 12/11 (và lý do)

Không chạy lại `npm install`/`npm test`/`npm run typecheck` toàn bộ: VM
hiện tại không còn `node_modules` của lần chạy Linux ngày 11/11, cài lại
từ đầu trên 1,5 CPU kèm build native `node-pty` rất lâu và đã từng thất
bại; trong khi diff trên chứng minh phần upstream không đổi nên chạy lại
cũng không cho kết quả mới. Nếu cần chạy lại toàn bộ, dùng đúng
`scripts/run-offline.ps1` trên máy đã có môi trường Node sẵn.
