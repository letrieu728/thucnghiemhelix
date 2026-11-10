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

## Rà soát kết quả hiện có (2026-11-10)

- **Đủ điều kiện công bố:** chỉ `typecheck` PASS. Bản tóm tắt có thể kiểm tra
  lại nằm ở `results/2026-11-07-typecheck.md`.
- **Không đủ điều kiện kết luận:** lần chạy `npm test` dùng working tree có
  chỉnh sửa cục bộ; vì thế không đưa kết quả fail vào đánh giá chất lượng HELIX.
- **Chưa có artifact kết quả:** cadence verify, assembly verify, flow graphs và
  các static audit. Việc có lệnh trong script không đồng nghĩa lệnh đã chạy.
- **Không chạy lại:** các benchmark/provider live và LCB100/SWE-bench, vì cần
  credential, chi phí inference, hoặc dữ liệu/runner không nằm trong checkout.
