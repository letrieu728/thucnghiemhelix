# Mục lục thư mục `results/`

Thư mục này giữ log và bằng chứng gốc của công việc kiểm chứng offline
(07–13/11/2026) và các audit/báo cáo kèm theo. Số liệu tổng hợp nằm ở
[`../RESULTS.md`](../RESULTS.md) và [`../REPORT.md`](../REPORT.md); ở đây
là bằng chứng thô để đối chiếu lại.

## Báo cáo và ghi chú theo ngày

| File | Nội dung |
| --- | --- |
| `2026-11-07-typecheck.md` | Tóm tắt `npm run typecheck` PASS (07/11) |
| `2026-11-10-offline-verification.md` | Kết quả verify offline lần 2 (10/11): assembly, flow graph, audit, TODO-27 |
| `2026-11-11-linux-verification.md` | Verify offline trên Linux (11/11): 6 PASS / 4 FAIL, 101 symlink hỏng |
| `2026-11-11-linux-fix-attempt.md` | Nỗ lực sửa ngày 11/11: build `node-pty`, tái sinh 3 artifact, cassette vẫn BLOCKED |
| `2026-11-11-phan-chua-lam-duoc.md` | 5 hạng mục chưa làm được và lý do (11/11, trước khi push) |
| `2026-11-11-large-files-gz-note.md` | Cách giải nén các file `.gz.b64` (base64 + gzip) và SHA-256 đối chiếu |
| `2026-11-12-test-fix-attempt.md` | Phân loại lại 13 lỗi assertion + 6 timeout ngày 12/11 (8/13 thực ra là symlink ENOENT) |
| `2026-11-12-closed-loop-trace-audit.md` | Audit 80 trace fork: 9 live + 31 dry-run mock |
| `2026-11-12-closed-loop-copy-verification.md` | Kiểm chứng bản sao `closed-loop/` trong repo này |
| `2026-11-12-fixture-symlink-check.md` | Kiểm tra 101 fixture symlink hỏng |
| `2026-11-12-fork-carryover-check.md` | Đối chiếu phần việc mang từ fork sang repo này |
| `2026-11-13-tinh-trang-harness-that-benchmark.md` | Tình trạng harness thật + benchmark thật (13/11): smoke test chưa ghép được, 101 symlink chặn benchmark |

## Log chạy lệnh (11–12/11)

| File | Nội dung |
| --- | --- |
| `2026-11-11-npm-test.txt` | Full test lần đầu có tổng kết (20 file fail / 88 pass) |
| `2026-11-11-npm-test-with-pty.txt` | Full test sau khi build được `node-pty` (19/89, 29/805) |
| `2026-11-11-npm-ci-failed.txt` | `npm ci` thuần FAIL (build native `node-pty` lỗi `EPERM`) |
| `2026-11-11-typecheck.txt` | Log typecheck trên Linux |
| `2026-11-11-current-module-audit-verify.txt`, `2026-11-11-executable-audit-verify.txt`, `2026-11-11-flow-graph-verify.txt`, `2026-11-11-todo27-*.txt` | Log verify từng hạng mục |
| `2026-11-11-task-parity-*.txt`, `2026-11-11-task-parity-*.json` | Log và dữ liệu task parity / cadence / split (gồm 2 file JSON ~1,1 MB) |
| `2026-11-12-npm-test-after-fix.txt` | Full test sau sửa (song song): 18 file fail / 90 pass |
| `2026-11-12-npm-test-sequential.txt` | Full test tuần tự: 14 file fail / 94 pass, 0 timeout |
| `13-node-pty-rebuild.txt`, `14-node-pty-gyp-nodedir.txt` | Log build `node-pty` bằng đường vòng (node-gyp + header tải tay) |
| `15-current-module-audit-regen.txt`, `16-current-module-audit-verify-after-regen.txt` | Tái sinh và verify lại current-module audit |
| `17-task-parity-split-verify-after-manifest.txt` | Verify split parity sau khi sửa manifest (PASS 403/403) |
| `18-task-parity-smoke-subset.txt`, `19-task-parity-smoke-subset-verify.txt` | Subset smoke task parity + kết quả verify (PASS 13/13) |
| `20-task-parity-cadence-subset.txt`, `21-task-parity-cadence-subset-verify.txt` | Subset cadence + kết quả verify |
| `2026-11-11-assembly-contract-verify.txt.gz.b64` | Log assembly-contract verify, nén gzip+base64 (xem file gz-note) |
| `manifest-before.json` | Manifest split-parity gốc (06/2026), dùng để đối chiếu với bản tái sinh |

## Thư mục con

| Thư mục | Nội dung |
| --- | --- |
| `2026-11-11-fixed-artifacts/` | 3 artifact tái sinh ngày 11/11 (current-module audit, split manifest) — bản gốc vẫn giữ nguyên và vẫn FAIL |
| `2026-11-12-real-harness-smoke-test/` | Bằng chứng smoke test ghép LoRA với harness lắp thật (chưa thành công, 2 blocker đã chẩn đoán) |
| `2026-11-13-test-audit/` | Rà test 35 bài (13/11): 29 test đúng, 6 test lỏng, 0 mâu thuẫn; số headline giữ nguyên; kèm 8 script kiểm tra tái chạy được |
| `2026-11-13-per-task-analysis/` | Phân tích theo từng bài (13/11): train 5 cải thiện / 1 tụt / 14 không đổi; held-out 3 / 1 / 11; kiểm định cấp bài đều không có ý nghĩa |

## Lưu ý khi thêm file mới

`.gitignore` của repo bỏ qua `results/*.txt` và `results/*.json` ở thẳng
thư mục này (mẫu một tầng, không áp dụng cho thư mục con). File log mới
nên đặt trong thư mục con theo ngày/mục đích, hoặc phải thêm bằng
`git add -f` nếu để ở thẳng `results/`; file đã commit thì vẫn được theo
dõi bình thường.
