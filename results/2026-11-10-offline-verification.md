# Offline verification — 2026-11-10

Source HELIX: `a090aba675be000b608e821f40ded4dc705e92af` (working tree có
thay đổi cục bộ; không dùng lượt này cho benchmark). Node `v24.21.0`; npm
`11.19.0`. Các lệnh `tsx` được chạy ngoài sandbox vì sandbox làm
`node:os.userInfo()` lỗi `uv_os_get_passwd returned ENOMEM`.

| Lệnh | Kết quả | Ghi chú |
| --- | --- | --- |
| `npm run typecheck` | PASS | `tsc -p tsconfig.json --noEmit` hoàn thành không có diagnostics. |
| `npm run assembly:contract:verify` | PASS | Strict verification của 5 product hoàn thành. |
| `verify-flow-graph` (9 artifact) | PASS | Bao gồm 5 blueprint và 4 comparison artifact. |
| `npm run executable:audit:verify` | PASS | Fingerprint `44370eff3ea1ca3a`; không có compile blocker. |
| `npm run todo27:inventory:verify` | PASS | Fingerprint `e12a2bb0941ac9c7`. |
| `npm run todo27:opencode:acceptance:verify` | PASS | `ready-for-review`; có 108/124 native và 16 metadata retained. |
| `npm run task:parity:verify` | FAIL | Thiếu metadata bắt buộc của acceptance-timing drift. |
| `npm run task:parity:cadence:verify` | FAIL | Cùng thiếu metadata acceptance-timing drift. |
| `npm run task:parity:split:verify` | FAIL | Nhiều attachment không khớp hash và byte size trong manifest. |
| `npm run current-module:audit:verify` | FAIL | Artifact fingerprint `ce386d45f16fbeda` khác fingerprint tính lại `413e63553ad22ce5`. |

Failure ở bảng trên là kết quả kỹ thuật của artifact hiện có. Không tự sửa hay
tái sinh artifact trong lượt này vì checkout HELIX đang dirty; việc đó phải
được làm trên clean checkout để có thể quy kết thay đổi và so sánh lại.

## Thử tái sinh trên clean checkout

Đã tạo clean worktree tại commit `a090aba` và cài dependency bằng `npm ci`.
`npm run task:parity` vẫn bị **BLOCKED** trước khi sinh artifact:

```text
EPERM, Permission denied: ...helix-task-branch-or-fork-opencode-assembled-...
```

Lỗi lặp lại sau khi đặt `TEMP`, `TMP` và `TMPDIR` vào thư mục tạm riêng trong
clean worktree. Vì CLI không tạo được workspace tác vụ, không thể tái sinh
cassette task-parity trong môi trường Windows hiện tại.
