# Báo cáo đối chiếu thực nghiệm HELIX

## Tóm tắt

Đợt thực nghiệm này kiểm tra khả năng tái lập **offline** của HELIX tại commit
`a090aba675be000b608e821f40ded4dc705e92af`, trên Windows, Node `v24.21.0`
và npm `11.19.0`. Kết quả xác nhận được nhiều contract và audit tĩnh, nhưng
không tái lập được các benchmark năng lực model. Ba artifact parity/audit có
lỗi nhất quán và việc tái sinh cassette task-parity bị chặn bởi quyền tạo
workspace tạm trên Windows.

Kết luận đúng là: **một phần kiểm tra cấu trúc offline của HELIX có thể xác
minh; các số liệu LiveCodeBench và SWE-bench của tác giả chưa được tái lập.**

## Phạm vi và phương pháp

- Nguồn công bố: [ghi chú phân tích ban đầu](../../THUC-NGHIEM-HELIX.md) và
  artifact trong [HELIX source](../HELIX-git/).
- Kết quả lệnh: [offline verification](./results/2026-11-10-offline-verification.md)
  và [RESULTS.md](./RESULTS.md).
- Verifier `tsx` chạy ngoài sandbox vì sandbox làm `node:os.userInfo()` lỗi
  `uv_os_get_passwd returned ENOMEM`.
- Checkout gốc có thay đổi cục bộ; lượt verify đánh giá artifact hiện diện,
  không dùng làm bằng chứng benchmark. Một clean worktree đã được thử để tái
  sinh cassette task-parity.

## Đối chiếu kết quả

| Hạng mục | Tác giả công bố / artifact | Kết quả đợt này | Diễn giải đúng |
| --- | --- | --- | --- |
| Typecheck | Có script TypeScript | **PASS** | Source tại commit kiểm tra typecheck thành công. |
| Assembly contract | Recipe/contract cho 5 product | **PASS** strict verification | Xác nhận contract hợp lệ theo verifier; không đo năng lực model. |
| Flow graph | Blueprint/comparison artifact | **PASS** 9 artifact | 5 blueprint và 4 comparison artifact verify được. |
| Executable audit | Artifact audit | **PASS**, fingerprint `44370eff3ea1ca3a` | Không có compile blocker theo rule audit. |
| TODO-27 inventory | Inventory transition atom | **PASS**, fingerprint `e12a2bb0941ac9c7` | Nhất quán theo verifier, không phải native parity hoàn chỉnh. |
| OpenCode acceptance | Acceptance artifact | **PASS**, `ready-for-review` | 108/124 native, 16 metadata retained; chưa phải TODO hoàn tất. |
| Task parity/cadence | 12 task × 4 harness | **FAIL** | Thiếu metadata bắt buộc của acceptance-timing drift. |
| Split task parity | Summary và attachment | **FAIL** | Nhiều attachment lệch hash/kích thước manifest. |
| Current-module audit | Audit fingerprint | **FAIL** | Artifact `ce386…` khác fingerprint tính lại `413e…`. |
| Tái sinh task parity | Script cassette không cần LLM | **BLOCKED** | Clean checkout gặp `EPERM` khi tạo workspace tạm. |
| Unit/conformance suite | Tác giả nói có 108 file Vitest | **Không kết luận** | Lần chạy trước dùng working tree dirty; chưa có full-suite sạch. |
| Live provider/native CLI | Live parity/capture | **Không thực hiện** | Cần credential, provider thật, internet và inference. |
| LiveCodeBench 100 | pi-mono 76, tổ hợp 79, full search 87 | **Không tái lập** | Thiếu 100 task/runner; summary còn đánh dấu tổ hợp tốt nhất là contaminated. |
| SWE-bench Verified 55 | 44 → 49/55 | **Không tái lập** | Thiếu Docker/runner/grader; cần model thật. |

## Điều đã được chứng minh

1. TypeScript của checkout typecheck thành công.
2. Assembly contract, flow graph, executable audit và hai artifact TODO-27 nêu
   trên thỏa điều kiện verifier hiện tại.
3. Verifier phát hiện ba điểm không nhất quán: metadata acceptance timing,
   integrity attachment split parity và fingerprint current-module audit.

## Điều chưa được chứng minh

1. Không có bằng chứng mới về parity native end-to-end với CLI upstream.
2. Không có đo lường mới về Pass@1, Pass@N hay hiệu quả full-search.
3. Không thể xác nhận hay phủ định các số LCB 76/79/87 và SWE-bench 44→49/55.
4. PASS của artifact verifier chỉ nói artifact thỏa rule của verifier, không
   đồng nghĩa benchmark live PASS.

## Hạn chế và hướng tái lập đầy đủ

| Hạn chế | Tình trạng | Việc cần làm |
| --- | --- | --- |
| Workspace tạm Windows | `EPERM` khi chạy cassette task-parity, kể cả clean worktree/TEMP riêng | Chạy trên máy/VM khác hoặc Linux có quyền temp bình thường. |
| Full test | Chưa có kết quả sạch | Chạy `npm test` trên clean checkout sau khi xử lý môi trường. |
| Live provider/native CLI | Cần API/GPU và credential | Chọn model, ngân sách và protocol ghi log. |
| LCB100 | Thiếu dataset/runner | Chuẩn bị 100 task và runner 10 lượt/task. |
| SWE-bench | Thiếu runner/Docker/grader | Dựng toolchain chính thức, dataset và quy tắc chấm. |

## Kết luận

HELIX có bằng chứng offline tích cực ở lớp cấu trúc: typecheck, contract,
flow graph và một số audit/acceptance artifact đều verify được. Tuy nhiên,
artifact task-parity quan trọng không qua integrity/metadata verification;
không nên dùng chúng để khẳng định parity end-to-end. Các kết quả
LiveCodeBench và SWE-bench của tác giả ở trạng thái **chưa tái lập**, không
phải đã được xác nhận hoặc bác bỏ.

Ưu tiên tiếp theo là chạy lại task parity và full test trên clean environment
có quyền workspace tạm, rồi version hóa manifest, attachment và log trước khi
đến benchmark live.
