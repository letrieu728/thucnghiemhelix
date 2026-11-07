# Kết quả chạy ban đầu

Thời điểm: 2026-11-07. Nguồn HELIX: commit `a090aba675be000b608e821f40ded4dc705e92af`. Môi trường: Node `v24.21.0`, npm `11.19.0`, Windows.

| Thực nghiệm | Trạng thái | Ghi nhận |
| --- | --- | --- |
| `npm run typecheck` | PASS | TypeScript hoàn thành không lỗi. |
| `npm test` | FAIL / không kết luận | Nhiều conformance tests fail trong working tree đang có thay đổi chưa commit. Không dùng kết quả này để kết luận framework lỗi; cần chạy lại trên clean checkout. |
| `npm run assembly:contract:verify` | BLOCKED | Không khởi tạo được `tsx` vì Node trả `ERR_SYSTEM_ERROR: uv_os_get_passwd returned ENOMEM`. Đây là giới hạn của môi trường sandbox, không phải bằng chứng lỗi assembly. |

## Diễn giải cho báo cáo

- Có bằng chứng trực tiếp rằng TypeScript source hiện tại typecheck được.
- Các kiểm tra còn lại phải chạy lại trên một clean checkout, với Node LTS được HELIX hỗ trợ và đủ bộ nhớ/quyền hệ điều hành.
- Không coi một test run lỗi trong source đã sửa cục bộ là kết quả benchmark hay kết luận chất lượng của HELIX.

## Việc cần làm để tái chạy đáng tin cậy

1. Clone sạch HELIX ở đúng commit đã ghi ở trên.
2. Cài Node LTS theo yêu cầu của HELIX và `npm install`.
3. Chạy `powershell -ExecutionPolicy Bypass -File .\scripts\run-offline.ps1`.
4. Nếu các verify pass, chạy thêm `-IncludeFullTest`; đưa log tạo ra vào phần phụ lục, không commit secrets/API keys.
