# Phần chưa làm được và lý do — 2026-11-11

Ghi chú kèm 2 commit Linux ngày 11/11/2026 (`c5ac4d4` xác minh,
`298b0c0` nỗ lực sửa). File này liệt kê những gì vẫn chưa làm được
sau cả 2 lượt, và lý do từng mục, để người đọc không tưởng là nhóm
quên hay giấu.

## 1. Tái sinh cassette livecodebench100 — chưa làm được

Lý do: 101 fixture trong `packages/conformance/fixtures/tasks` của
HELIX là symlink commit trong git, tất cả trỏ tới đường dẫn tuyệt đối
trên máy tác giả (`/home/HarnessLego-pi-lcb-eval/...`), 101/101 hỏng
trên mọi máy khác. File thật chưa từng có trong repo hay trong lịch
sử git (symlink đã có từ commit đầu tiên `1eb360b`), và nội dung 101
task này cũng không nằm ở đâu khác trong repo (chỉ có 1 task LCB thật
là `livecodebench-1883-b-palindrome-removal`).

Nhóm đã làm thay: chạy lại task parity trên đúng 12 task smoke có
file thật, sinh artifact mới verify PASS 13/13 (xem
`2026-11-11-linux-fix-attempt.md` §3). Đó là toàn bộ smoke suite,
không phải livecodebench100.

Muốn làm tiếp thì cần 1 trong 2 thứ: file fixture của tác giả, hoặc
một dự án dựng lại 101 task từ dataset LiveCodeBench công khai và ghi
rõ đó là fixture mới, không phải fixture gốc — vì vậy cassette sinh
ra cũng sẽ là cassette mới, không chứng minh được parity với artifact
gốc của tác giả.

## 2. 13 test lỗi assertion thật trong full test — chưa làm

Lý do: đây là lỗi nội dung thật của HELIX trên checkout `a090aba`
(`capture-dry-run` 2, `cli` 2, `todo27-misleading-native-copy`,
`block-ledger`, `compatible-bridge-visibility`, `nanobot-lego-depth`,
`p1-native-like-visibility`, `preview-metadata-retention-visibility`,
`product-turn-profile-visibility`, `recipe-targets`,
`reverse-assembly` — mỗi cái 1 test), không phải lỗi môi trường.
Sửa chúng nghĩa là sửa mã nguồn HELIX, thuộc về upstream/fork, không
thuộc về repo tái lập này (repo này chỉ kiểm chứng, không sửa HELIX).
Cần điều tra từng test một với tác giả hoặc trong fork của nhóm.

## 3. 6 test timeout — chưa kết luận được

Lý do: các test này timeout ở 5s / 15s / 120s trên VM chia sẻ chỉ có
1,5 CPU (`cli` 2, `config-prompt-ui` 1,
`current-module-placeholder-audit` 3). Chưa phân biệt được đâu là máy
chậm, đâu là code thật sự chậm. Cần chạy lại trên máy nhanh hơn hoặc
nới timeout rồi mới kết luận.

## 4. Benchmark mất phí — cố tình không chạy

Lý do: LiveCodeBench 100, SWE-bench 55, live provider, native CLI và
full search Pass@N đều cần gọi model thật qua API trả phí (tác giả
dùng MiniMax, khoảng 6.500 lượt gọi cho một lượt benchmark đầy đủ),
cộng thêm dữ liệu và bộ chạy chính thức (riêng SWE-bench còn cần
Docker và bộ chấm). Repo này được thiết kế chỉ cho kiểm tra offline,
miễn phí, nên các số benchmark của tác giả vẫn ở trạng thái chưa tái
tạo — không phải đã xác nhận, cũng không phải đã bác bỏ.

## 5. Đánh giá held-out cho LoRA và build đầu tiên trên Builder — chưa làm, nằm ngoài repo này

Lý do: 2 việc này thuộc về nhánh closed-loop / Builder trong fork
HELIX của nhóm, không thuộc repo tái lập offline này. Đánh giá
held-out cần chạy thêm vòng BUILD–train–REBUILD trên task chưa từng
dùng để train (cần GPU Modal và thời gian chạy); build đầu tiên trên
Builder cần chạy một tác vụ thật với model (sửa 1 file, Max steps = 5).
Cả 2 đều chưa có kết quả, không phải vì quên mà vì nằm ở mạch công
việc khác.

## 6. Push từng bị chặn — đã rõ nguyên nhân, không phải lỗi kết quả

Trước lượt này, push bị lỗi 403 vì Muse GitHub App chưa được cài /
chưa có quyền ghi trên repo `letrieu728/thucnghiemhelix` (đọc qua API
vẫn được, chỉ ghi bị chặn). Cần người sở hữu repo mở
https://github.com/apps/meta-muse-ai/installations/new và chọn repo
này cho app thì mới push được.
