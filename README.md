# Thực nghiệm HELIX — Báo cáo cuối kỳ

Repository này tái lập các kiểm tra **offline, miễn phí và có thể chạy lại** của [HELIX](../HELIX-git/). Mục tiêu là đánh giá kỹ thuật của framework, không tuyên bố tái lập kết quả benchmark dùng LLM trả phí.

## Phạm vi đã thực hiện

| Thực nghiệm | Mục tiêu | Lệnh | Kết quả |
| --- | --- | --- | --- |
| Typecheck | Kiểm tra tính nhất quán kiểu của workspace | `npm run typecheck` | Xem `results/typecheck.txt` |
| Unit & conformance tests (tuỳ chọn) | Kiểm tra hồi quy và các hợp đồng module | `./scripts/run-offline.ps1 -IncludeFullTest` | Xem `results/tests.txt` |
| Task parity (cassette) | So sánh assembled/original-contract trong chế độ xác định | Không tự chạy trong script | Có thể ghi đè artifact upstream |
| Cadence verification | Kiểm tra tái lập cadence artifact | `npm run task:parity:cadence:verify` | Xem `results/cadence-verify.txt` |
| Assembly verification | Kiểm tra recipe/assembly contract | `npm run assembly:contract:verify` | Xem `results/assembly-verify.txt` |

Các lệnh được chạy từ bản HELIX cục bộ. Mặc định script giả định cấu trúc thư mục:

```text
HELIX-main (2)/
├── HELIX-git/          # source HELIX, đã npm install
└── thucnghiemhelix/    # repository này
```

## Chạy lại

Mở PowerShell tại repository này và chạy:

```powershell
./scripts/run-offline.ps1
```

Hoặc truyền đường dẫn HELIX khác:

```powershell
./scripts/run-offline.ps1 -HelixDir 'D:\du-an\HELIX'
```

Script không dùng API key, không gửi dữ liệu ra ngoài và không gọi model. Nó chỉ chạy các lệnh verify/read-only và lưu log cho từng lệnh vào `results/`. Thêm `-IncludeFullTest` khi muốn chạy toàn bộ test suite.

## Cách diễn giải

Các thí nghiệm trên chứng minh rằng source hiện tại biên dịch, test được, và các artifact/contract offline nhất quán. Chúng **không** chứng minh HELIX tốt hơn các agent khác trên benchmark thực tế, vì không có lần gọi model thật.

`task:parity` ở đây dùng fixture/cassette hoặc original-contract replay khi không bật `--native-original`; vì vậy đây là bằng chứng về khả năng tái lập cấu trúc và hành vi đã ghi nhận, không phải native end-to-end parity.

## Trạng thái tái lập đã xác nhận

Kết quả được lưu trong thư mục `results/` và được version hóa khi có kết luận
rõ ràng. Lần rà soát ngày 2026-11-10 phân biệt giữa **đã chạy thành công**,
**đã thử nhưng không kết luận**, và **chưa chạy**; không suy diễn kết quả từ
artifact có sẵn trong HELIX thành một lần tái lập mới.

| Hạng mục trong HELIX | Trạng thái tái lập | Ghi chú |
| --- | --- | --- |
| Typecheck | PASS (2026-11-07) | Xem `results/2026-11-07-typecheck.md`; chạy tại commit `a090aba`. |
| Full unit/conformance tests | Không kết luận | Đã chạy trên working tree có thay đổi cục bộ; log thô không được dùng làm kết quả xác nhận. |
| Cassette task parity và cadence | Chưa có kết quả được lưu | Chỉ chạy khi các artifact đầu vào còn phù hợp với checkout đang kiểm tra. |
| Assembly contract | BLOCKED | Lần chạy trước bị `ERR_SYSTEM_ERROR: uv_os_get_passwd returned ENOMEM`. |
| Flow graphs và static audits | Chưa chạy trong repository này | Có thể chạy offline, nhưng phải lưu kèm commit và trạng thái working tree. |
| Live provider/native CLI/LCB/SWE-bench | Không thực hiện | Cần model/credential hoặc dữ liệu và runner không có trong checkout. |

## Các phần chưa làm được và lý do

| Hạng mục | Lý do chưa chạy | Điều kiện để chạy |
| --- | --- | --- |
| Live provider parity | Cần API credential của provider | API key OpenRouter/OpenAI-compatible/Anthropic/Google và ngân sách token |
| Native upstream CLI parity | `--native-original` gọi upstream CLI kèm model thật | Credentials, internet, và chi phí inference |
| LiveCodeBench/SWE-bench Pass@1 | Cần thực thi agent trên benchmark với model | Model API hoặc GPU/local model, dữ liệu benchmark, thời gian chạy |
| Full search / Pass@N | Mỗi task thử nhiều recipe/candidate | Ngân sách inference lớn và quy tắc budget-matched với baseline |
| So sánh đa seed, đa model | Cần lặp lại nhiều lần inference | API/GPU và một protocol thống kê định trước |
| Robustness đa provider | Cần endpoint/provider thật để tiêm lỗi mạng/tool | Credentials hoặc hạ tầng provider local tương thích |

## Hạn chế cần nêu trong báo cáo

1. Kết quả offline không được suy diễn thành chất lượng giải benchmark.
2. Điểm “Full search” kiểu Pass@N không so sánh trực tiếp được với Pass@1 của một harness cố định nếu không cùng ngân sách rollout/token.
3. Artifact live trong upstream chỉ là ảnh chụp ở thời điểm tạo; phiên bản upstream/model có thể đã thay đổi.
4. Bằng chứng native của các product không đồng đều; một số kiểm tra là fixture hoặc metadata guard thay vì quan sát native end-to-end.

## Nguồn và khả năng tái lập

- HELIX local source: `../HELIX-git/`
- Upstream project remote: `https://github.com/Vietng-XPrince7/HELIX`
- Phiên bản Node/npm, commit và thời gian chạy được ghi ở đầu mỗi log trong `results/`.

