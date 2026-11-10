# Offline verification — 2026-11-10

Source HELIX: `a090aba675be000b608e821f40ded4dc705e92af` (working tree có
thay đổi cục bộ; không dùng lượt này cho benchmark). Node `v24.21.0`; npm
`11.19.0`.

| Lệnh | Kết quả | Ghi chú |
| --- | --- | --- |
| `npm run typecheck` | PASS | `tsc -p tsconfig.json --noEmit` hoàn thành không có diagnostics. |
| `npm run task:parity:verify` | BLOCKED | `tsx` lỗi trước CLI: `uv_os_get_passwd returned ENOMEM`. |
| `npm run task:parity:cadence:verify` | BLOCKED | Cùng lỗi runtime. |
| `npm run executable:audit:verify` | BLOCKED | Cùng lỗi runtime. |
| `npm run current-module:audit:verify` | BLOCKED | Cùng lỗi runtime. |
| `npm run todo27:inventory:verify` | BLOCKED | Cùng lỗi runtime. |
| `npm run todo27:opencode:acceptance:verify` | BLOCKED | Cùng lỗi runtime. |

`ERR_SYSTEM_ERROR` được ném trong `node:os.userInfo()` khi loader của `tsx`
khởi tạo. Do đó các trạng thái BLOCKED không phản ánh kết quả pass/fail của
task parity, cadence hay audit.
