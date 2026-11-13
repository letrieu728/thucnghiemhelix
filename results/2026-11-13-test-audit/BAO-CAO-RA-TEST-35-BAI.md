# Báo cáo rà test — 35 bài HELIX (20 train + 15 held-out v2)

- **Ngày rà:** 13/11/2026. Làm việc **offline**, chỉ đọc file gốc, chạy kiểm tra bằng Python CPU local. **Không sửa bất kỳ file gốc nào** (spec, test, traces), không chạy GPU/Modal, không git push, không upload Drive.
- **Phạm vi:** 10 bài train gốc `lcb_001`–`lcb_010` (trong `closed-loop/scripts/02_run_helix_eval.py`, đọc bằng AST, không import/chạy script), 10 bài train thêm `lcb_011`–`lcb_020` (`closed-loop/data/train_extra_problems.json`), 15 bài held-out v2 `held2_001`–`held2_015` (`closed-loop/data/heldout2_problems.json`). Tổng **35 bài**, **256 mục test** (mỗi mục là một dòng assert/lệnh trong `test_cases`).
- **Cơ chế chấm đã xác minh:** `run_test_cases()` trong `02_run_helix_eval.py` nối code lời giải + `"\n".join(test_cases)` rồi chạy trong subprocess Python với timeout 5 giây; `passed=True` khi và chỉ khi exit code = 0 (mọi assert đều qua, không exception). Cùng một bộ test được dùng cho mọi phase/mô hình — không có đường chấm riêng nào khác.

## 1. Kết luận tổng thể — SỐ HEADLINE GIỮ NGUYÊN

> **Không phát hiện test mâu thuẫn nào. Số headline giữ nguyên, không đổi ô nào, không cần chấm lại, không cần tính lại McNemar.**

| Phân loại | Số bài | Danh sách |
|---|---|---|
| (a) Test đúng | **29** | lcb_001, 003, 005, 006, 007, 008, 010, 011, 012, 013, 015, 016, 017, 018, 020; held2_001–010, 012–015 |
| (b) Test THIẾU (spec nêu hành vi mà test không kiểm tra) | **6** | lcb_002, lcb_004, lcb_009, lcb_014, lcb_019, held2_011 |
| (c) Test MÂU THUẪN với spec | **0** | — |

**Số chốt đối chiếu (không đổi):**

| Chỉ số | Cũ | Mới | Thay đổi |
|---|---|---|---|
| Vòng 2 BUILD2 → REBUILD2 | 60/80 → 66/80 (Minimal 14→17, pi-mono 15→16, hermes 14→15, opencode 17→18; McNemar 7 thắng/1 thua, p=0,0703) | như cũ | Không |
| Held-out v2 base → LoRA | 50/60 → 53/60 (5 thắng/2 thua, p=0,4531) | như cũ | Không |
| Vòng 1 BUILD → REBUILD | 28/40 → 31/40 | như cũ | Không |
| Held-out v1 base → LoRA | 39/40 → 40/40 | như cũ | Không |

**Ý nghĩa của 6 bài loại (b):** các test này *lỏng* (một lời giải sai vẫn có thể đậu), chứ không *sai* (không có lời giải đúng nào bị đánh trượt). Vì cùng một bộ test áp dụng cho cả base lẫn LoRA ở mọi phase, phép so sánh vẫn công bằng; chỉ có tỷ lệ đậu tuyệt đối ở 6 bài này có thể hơi lạc quan. Theo quy tắc cam kết trước, **không** bổ sung test hồi tố để chấm lại — các test bổ sung ở §4 chỉ dành cho phiên bản benchmark sau.

## 2. Phương pháp và quy tắc phân loại

**Ba lớp kiểm tra độc lập cho mỗi bài:**

1. **Đáp án tham chiếu:** viết lại lời giải đúng từ *văn bản spec* (không copy từ traces), chạy với *đúng* `test_cases` gốc bằng đúng ngữ nghĩa `run_test_cases` (nối code + test, subprocess, timeout). Kết quả: **35/35 đậu**.
2. **Kiểm chứng giá trị kỳ vọng bằng phương pháp khác:** liệt kê vét cạn / thuật toán độc lập (ví dụ: mọi mảng con cho lcb_006, mọi chuỗi con cho lcb_013, mọi dãy con cho held2_004, mọi bộ ba cho held2_010, mô phỏng mọi điểm xuất phát cho held2_012, `re.fullmatch` cho held2_002, `statistics.median` cho held2_008, liệt kê hoán vị cho held2_009). Kết quả: **0 lệch** trên toàn bộ giá trị kỳ vọng đã kiểm chứng.
3. **Probe "biến thể lỗi":** chạy các lời giải *cố tình sai* một khía cạnh của spec (ví dụ: checker sudoku chỉ kiểm tra hàng; `>=` thay cho `>`; bỏ qua `[]`/`{}`; đảo ngược thứ tự output) với test gốc. Nếu biến thể lỗi vẫn đậu → test thiếu khả năng phân biệt khía cạnh đó (bằng chứng cho loại (b)). Nếu biến thể lỗi trượt → test đã kiểm tra khía cạnh đó thật (bằng chứng cho loại (a)). 17/18 probe cho kết quả như dự đoán; 1 probe "thông tin" về lcb_009 cho kết quả ngoài dự đoán (xem §4) — chính probe này đã phát hiện ra lỗ hổng thứ 6.

**Quy tắc phân loại (cam kết trước):**

- **(c) Mâu thuẫn:** test đòi hỏi điều spec không nêu (ví dụ: chọn một đáp án trong khi spec không có quy tắc hòa và có nhiều đáp án đúng), hoặc giá trị kỳ vọng sai về mặt toán học (đã kiểm chứng bằng vét cạn). Chỉ loại này mới được "sửa" trong báo cáo và chấm lại.
- **(b) Thiếu:** spec nêu rõ một hành vi/trường hợp, nhưng **không có test nào phân biệt được** hành vi đó — chứng minh bằng một input hợp lệ theo spec mà một lời giải đậu toàn bộ test hiện tại lại cho đáp án sai spec. Ghi rõ, không coi là sai, không chấm lại.
- **(a) Đúng:** mọi hành vi nêu rõ trong spec đều có ít nhất một test phân biệt được.
- **Ngoại lệ độ phức tạp:** yêu cầu O(1)/O(log n) (lcb_003, lcb_005) không thể kiểm chứng bằng assert giá trị trong harness này (input nhỏ, timeout chung 5 giây) — ghi nhận là giới hạn của harness, không tính là (b). Ngược lại, yêu cầu "in-place" (lcb_004) *có thể* kiểm chứng bằng assert (so sánh identity của node) nên vẫn tính là (b) khi thiếu.
- **Spec im lặng thì không tính thiếu:** ví dụ n=0 cho lcb_007, k>n cho held2_006, self-loop cho lcb_012, begin=end cho held2_005 — spec không nêu, không có test, không mâu thuẫn → vẫn là (a), chỉ ghi chú.

## 3. Bảng 35 bài

"Ref" = đáp án tham chiếu viết độc lập có đậu toàn bộ test gốc không. "Mục test" = số phần tử trong `test_cases` (gồm cả dòng khai báo helper).

| # | Bài | Spec tóm tắt | Mục test | Ref | Kết luận | Bằng chứng chính |
|---|---|---|---|---|---|---|
| 1 | lcb_001_two_sum | Chỉ số 2 số cộng bằng target, đúng 1 nghiệm, trả về tăng dần | 3 | Đậu | (a) Đúng | Vét cạn mọi cặp: nghiệm duy nhất khớp cả 3 test; T1 kiểm tra thứ tự tăng dần |
| 2 | lcb_002_valid_parentheses | `()[]{}`, `*` = `(` / `)` / rỗng | 7 | Đậu | **(b) Thiếu** | 0/7 literal chứa `[]`/`{}` (kiểm tra AST); biến thể chỉ-`()` đậu hết; `'([)]'` phân biệt được (xem §4) |
| 3 | lcb_003_lru_cache | LRU, `put` trả về key bị trục xuất, không trục xuất thì `None` | 11 | Đậu | (a) Đúng | Mô phỏng độc lập bằng danh sách recency khớp từng bước (trục xuất 2 rồi 3); `get` và `put`-update đều cập nhật recency; biến thể `put` luôn `None` trượt |
| 4 | lcb_004_reverse_linked_list | Đảo danh sách liên kết **in-place**, trả về head mới | 15 | Đậu | **(b) Thiếu** | Biến thể tạo node mới đậu hết → in-place không được kiểm tra (identity phân biệt được); thiếu case 1 node (xem §4) |
| 5 | lcb_005_binary_search | Tìm kiếm nhị phân, không thấy → −1, O(log n) | 5 | Đậu | (a) Đúng | Quét tuyến tính xác nhận vị trí duy nhất; có test rỗng + đơn trị. O(log n) không kiểm chứng bằng assert (giới hạn harness). Lưu ý: spec không định nghĩa mảng có phần tử trùng, không test nào có trùng |
| 6 | lcb_006_max_subarray | Mảng con liên tục tổng lớn nhất, trả `(tổng, lát cắt)`; rỗng → `(0, [])` | 5 | Đậu | (a) Đúng | Liệt kê mọi mảng con: **mỗi test có duy nhất 1 lát cực đại** (T0 chỉ có `[4,−1,2,1]`) → việc spec không nêu quy tắc hòa không gây ảnh hưởng |
| 7 | lcb_007_climbing_stairs | Số cách leo n bậc (1/2 bước) | 5 | Đậu | (a) Đúng | Kiểm tra Fibonacci độc lập khớp 1, 2, 3, 8, 89. n=0 không được spec nêu |
| 8 | lcb_008_merge_intervals | Gộp khoảng chồng lấn **hoặc chạm nhau**, trả dict `{start, end, count}`, sắp xếp theo start | 4 | Đậu | (a) Đúng | Kiểm tra union-find khớp cả 4 (gộp chạm `[1,4]+[4,5]` count=2; input chưa sắp xếp; rỗng); biến thể count luôn 1 trượt. Lưu ý nhỏ: không test chuỗi gộp ≥3 khoảng (count≥3) |
| 9 | lcb_009_word_break | Mọi cách tách thành câu, **sắp xếp lexicographic**, không tách được → `[]` | 4 | Đậu | **(b) Thiếu** | Liệt kê mọi cách tách khớp cả 4; nhưng DFS theo thứ tự dict không sort vẫn đậu, và đổi thứ tự dict thì output mất sorted → yêu cầu sorted chưa được stress-test (xem §4). T3 `''→[]` phù hợp quy tắc `[]` của spec |
| 10 | lcb_010_number_of_islands | Đếm đảo, kề **4 hướng** | 6 | Đậu | (a) Đúng | Union-find 4 hướng khớp; bản 8 hướng **trượt** (g2 cho 1 thay vì 3) → tính 4 hướng được phân biệt thật |
| 11 | lcb_011_trap_rain_water | Nước mưa bị giữ, rỗng → 0 | 7 | Đậu | (a) Đúng | Tính naive từng cột khớp cả 7 (kể cả T6 = 10) |
| 12 | lcb_012_can_finish_courses | Có hoàn thành được mọi khóa học không (phát hiện chu trình) | 7 | Đậu | (a) Đúng | DFS phát hiện chu trình khớp cả 7 (chu trình 2, chu trình 3, DAG, không ràng buộc). Lưu ý: self-loop không có test (spec không nêu riêng) |
| 13 | lcb_013_longest_palindromic_substring | Chuỗi con đối xứng dài nhất; **hòa thì lấy chỉ số bắt đầu nhỏ nhất**; rỗng → `''` | 8 | Đậu | (a) Đúng | Liệt kê mọi chuỗi con: `babad` có 2 ứng viên dài nhất, test chọn đúng `bab` (bắt đầu 0); `ac→a` cũng kiểm tra tie-break; biến thể lấy max cuối trượt |
| 14 | lcb_014_daily_temperatures | Số ngày chờ đến ngày **ấm hơn** (nghiêm ngặt), không có → 0 | 6 | Đậu | **(b) Thiếu** | Quét naive khớp cả 6; nhưng không test nào có 2 nhiệt độ bằng nhau kề nhau; biến thể `>=` đậu hết; `[70,70,71]` phân biệt được (xem §4) |
| 15 | lcb_015_word_search | Tìm từ trên bảng, kề 4 hướng, **mỗi ô dùng tối đa 1 lần** | 6 | Đậu | (a) Đúng | Liệt kê đường đi khớp ABCCED/SEE/ABCB; biến thể cho dùng lại ô trượt (ABCB) |
| 16 | lcb_016_partition_equal_subset | Chia 2 tập con tổng bằng nhau; rỗng → True | 7 | Đậu | (a) Đúng | Liệt kê mọi tập con khớp cả 7 (rỗng→True theo spec, tổng lẻ→False) |
| 17 | lcb_017_merge_k_sorted_lists | Gộp k list đã sắp xếp; rỗng/chỉ-None → None | 17 | Đậu | (a) Đúng | Rỗng, chỉ-None, None-lẫn, 1 list, giá trị trùng lặp qua các list đều có test |
| 18 | lcb_018_decode_string | Giải mã `k[...]`, k nhiều chữ số, lồng nhau, chữ ngoài ngoặc giữ nguyên | 7 | Đậu | (a) Đúng | Parser đệ quy độc lập khớp cả 7 (lồng nhau, `10[a]`, chữ ngoài ngoặc, rỗng) |
| 19 | lcb_019_permutations_unique | Mọi hoán vị duy nhất, **sắp xếp lexicographic**; rỗng → `[[]]` | 5 | Đậu | **(b) Thiếu** | Backtracking khớp cả 5; nhưng **mọi input đều đã sắp xếp**; biến thể giữ thứ tự gặp (không sort) đậu hết và trượt với `[2,1,1]` (xem §4) |
| 20 | lcb_020_min_jumps | Số bước nhảy tối thiểu; không tới được → −1; 0/1 phần tử → 0 | 8 | Đậu | (a) Đúng | DFS vét cạn khớp cả 8 |
| 21 | held2_001_edit_distance | Khoảng cách chỉnh sửa (thêm/xóa/thay) | 8 | Đậu | (a) Đúng | DP ma trận đầy đủ khớp cả 8 |
| 22 | held2_002_regex_match | Regex `.` và `*`, khớp toàn bộ chuỗi | 10 | Đậu | (a) Đúng | `re.fullmatch` khớp cả 10 (kể cả `mississippi` → False) |
| 23 | held2_003_n_queens_count | Số nghiệm bài toán n hậu | 7 | Đậu | (a) Đúng | Liệt kê hoán vị khớp n≤5; n=8,9 khớp dãy A000170 (92, 352) |
| 24 | held2_004_number_of_lis | Số lượng dãy con tăng dài nhất; rỗng → 0 | 7 | Đậu | (a) Đúng | Liệt kê mọi dãy con khớp cả 7 (kể cả `[1,2,4,3,5,4,7,2]→3`) |
| 25 | held2_005_word_ladder | Độ dài dãy biến đổi ngắn nhất (mỗi bước đổi 1 chữ, từ trung gian phải trong list), đếm cả đầu + cuối, không có → 0 | 6 | Đậu | (a) Đúng | BFS kề naive khớp cả 6 (end vắng→0, 1 bước trực tiếp, begin trong list) |
| 26 | held2_006_sliding_window_max | Max mỗi cửa sổ trượt cỡ k; rỗng → `[]` | 8 | Đậu | (a) Đúng | Cửa sổ naive khớp cả 8. k>n không được spec nêu |
| 27 | held2_007_course_order | Trả về **bất kỳ** thứ tự hợp lệ nào; chu trình → `[]` | 10 | Đậu | (a) Đúng | Helper `_valid` đã kiểm tra trực tiếp: từ chối thứ tự sai/thiếu/trùng, chấp nhận thứ tự đúng; chu trình→`[]` có test; n=1 có test `==[0]` (thứ tự duy nhất) |
| 28 | held2_008_median_finder | `add_num` + `find_median` (chỉ gọi khi đã có ≥1 số) | 6 | Đậu | (a) Đúng | `statistics.median` khớp cả 7 giá trị (âm, trùng lặp, chẵn/lẻ, đơn trị). Lưu ý: assert `==` chấp nhận int (`2 == 2.0`) nên kiểu trả về float không được ép chặt — không ảnh hưởng điểm |
| 29 | held2_009_next_permutation | Hoán vị lớn hơn tiếp theo, **trả về list mới, không sửa input**; không có thì trả về nhỏ nhất | 8 | Đậu | (a) Đúng | Liệt kê hoán vị khớp mọi giá trị; biến thể sửa input trượt T7; biến thể LeetCode in-place (trả None) trượt. 8/8 traces trượt do lỗi lời giải, không phải lỗi test (xem §7) |
| 30 | held2_010_three_sum | Mọi bộ ba tổng 0, mỗi bộ tăng dần, list **sắp xếp lexicographic** | 6 | Đậu | (a) Đúng | Liệt kê mọi bộ ba khớp cả 6 (kể cả thứ tự sorted); biến thể đảo thứ tự trượt; input chưa sắp xếp nên yêu cầu sorted được stress-test thật |
| 31 | held2_011_valid_sudoku | Bảng 9×9 hợp lệ: mỗi **hàng, cột, hộp 3×3** không trùng lặp; `.` bỏ qua | 7 | Đậu | **(b) Thiếu** | `valid_board` sạch; b2/b3/b4 đều False đúng; nhưng **không board nào vi phạm chỉ-cột hoặc chỉ-hộp** → checker chỉ-hàng và chỉ-hàng+cột đều đậu hết (xem §4) |
| 32 | held2_012_gas_station | Điểm xuất phát hoàn thành vòng; không thể → −1; nghiệm duy nhất nếu có | 6 | Đậu | (a) Đúng | Mô phỏng mọi điểm xuất phát khớp cả 6; mỗi case đúng 1 điểm khả thi (đúng tuyên bố duy nhất của spec) |
| 33 | held2_013_decode_ways | Số cách giải mã (`1`–`26`); `0` chỉ hợp lệ trong `10`/`20` | 10 | Đậu | (a) Đúng | Đệ quy + memo khớp cả 10 (số 0 đầu, `'100'→0`, `'11106'→2`) |
| 34 | held2_014_rotten_oranges | Số phút đến khi không còn cam tươi; không thối hết → −1; không có cam tươi → 0 | 6 | Đậu | (a) Đúng | Mô phỏng từng phút khớp cả 6 |
| 35 | held2_015_longest_consecutive | Dãy số nguyên liên tiếp dài nhất; rỗng → 0 | 7 | Đậu | (a) Đúng | Phương pháp sắp xếp khớp cả 7 (trùng lặp, âm, rỗng) |

Chi tiết từng bài ở file CSV kèm theo: `chi-tiet-35-bai.csv`.

## 4. Chi tiết 6 bài test THIẾU (loại (b))

Mỗi mục gồm: hành vi spec nêu nhưng test không kiểm tra → bằng chứng chạy thật → test bổ sung **đề xuất cho phiên bản sau** (đã kiểm tra là đậu với đáp án tham chiếu; **không** áp dụng hồi tố, **không** dùng để chấm lại).

### 4.1 lcb_002_valid_parentheses — không test `[]`/`{}`

- Spec nêu rõ chuỗi có thể chứa `()`, `[]`, `{}`. Nhưng cả 7 test chỉ dùng `(` `)` `*` và chuỗi rỗng — kiểm tra bằng AST: không literal nào trong test chứa `[`, `]`, `{`, `}`.
- Bằng chứng: biến thể chỉ xử lý `()` (bỏ qua mọi ký tự `[]`/`{}`) **đậu toàn bộ 7 test**.
- Input phân biệt: `'([)]'` — biến thể chỉ-`()` trả `True`, đáp án đúng theo spec là `False` (ngoặc lồng sai thứ tự). `'[(])'` tương tự.
- Đề xuất bổ sung: `assert is_valid('([)]') == False`, `assert is_valid('[]{}') == True`, `assert is_valid('[*]') == True`, `assert is_valid('([*])') == True`, `assert is_valid('(]') == False`.

### 4.2 lcb_004_reverse_linked_list — không kiểm tra "in-place", thiếu case 1 node

- Spec nêu "reverses a singly linked list **in-place**". Test chỉ so sánh giá trị qua `to_list()` — không kiểm tra node trả về có phải chính các node cũ không.
- Bằng chứng: biến thể tạo toàn node mới (không sửa node cũ) **đậu toàn bộ test**. Kiểm tra identity xác nhận: biến thể này cho tập id node khác hẳn input, trong khi bản in-place giữ nguyên tập id.
- Ngoài ra không có test list 1 phần tử (chỉ có 5, 2 phần tử và `None`).
- Đề xuất bổ sung: `assert to_list(reverse_list(make_list([1]))) == [1]` và một assert so sánh tập `id()` của các node trước/sau khi đảo (đã kiểm tra: đậu với đáp án tham chiếu in-place).

### 4.3 lcb_009_word_break — yêu cầu "sorted" chưa được stress-test

- Spec nêu output phải sắp xếp lexicographic. Cả 2 test có nhiều đáp án đều dùng `word_dict` có thứ tự trùng với thứ tự sorted của output.
- Bằng chứng: DFS duyệt theo thứ tự `word_dict`, **không sort**, vẫn đậu toàn bộ test. Nhưng với cùng input `'catsanddog'` và `word_dict` đảo thứ tự `['dog','sand','and','cats','cat']`, biến thể này trả `['cats and dog', 'cat sand dog']` — sai thứ tự theo spec.
- Đề xuất bổ sung: `assert word_break('catsanddog', ['dog', 'sand', 'and', 'cats', 'cat']) == ['cat sand dog', 'cats and dog']`.
- Ghi chú: T3 `word_break('', ['a']) == []` **không** phải mâu thuẫn — phù hợp quy tắc "không tạo được câu hợp lệ thì trả `[]`" của spec.

### 4.4 lcb_014_daily_temperatures — không test nhiệt độ bằng nhau

- Spec nêu "warmer temperature" (ấm hơn — nghiêm ngặt). Không test nào có 2 nhiệt độ bằng nhau kề nhau: các input là `[73,74,75,71,69,72,76,73]`, `[30,40,50,60]`, `[30,60,90]`, `[90,80,70]`, `[]`, `[50]`.
- Bằng chứng: biến thể dùng `>=` thay cho `>` **đậu toàn bộ test**.
- Input phân biệt: `[70,70,71]` — biến thể `>=` trả `[1,1,0]`, đáp án đúng là `[2,1,0]`.
- Đề xuất bổ sung: `assert daily_temperatures([70, 70, 71]) == [2, 1, 0]`, `assert daily_temperatures([73, 73, 73]) == [0, 0, 0]`.

### 4.5 lcb_019_permutations_unique — mọi input đều đã sắp xếp

- Spec nêu output phải sắp xếp lexicographic. Mọi input test (`[1,1,2]`, `[1,2,3]`, `[1]`, `[]`, `[2,2,2]`) đều đã sắp xếp không giảm, nên một lời giải không sort nhưng duyệt theo thứ tự input vẫn cho output đúng thứ tự.
- Bằng chứng: biến thể liệt kê `itertools.permutations` theo thứ tự gặp, khử trùng lặp, **không sort** — đậu toàn bộ test gốc, nhưng **trượt** với input `[2,1,1]` (trả về thứ tự không sorted).
- Đề xuất bổ sung: `assert permute_unique([2, 1, 1]) == [[1, 1, 2], [1, 2, 1], [2, 1, 1]]`, `assert permute_unique([3, 1, 2]) == [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]`.
- Đối chiếu: held2_010 (three_sum) có cùng yêu cầu sorted nhưng input chưa sắp xếp nên **không** rơi vào trường hợp này — biến thể đảo thứ tự trượt ngay.

### 4.6 held2_011_valid_sudoku — không test vi phạm chỉ-ở-cột / chỉ-ở-hộp

- Spec nêu 3 quy tắc: hàng, cột, hộp 3×3. Phân tích vi phạm từng board test:
  - `valid_board`: không vi phạm (đúng, True).
  - b2 (`[0][2]='5'`): vi phạm **hàng 0 + hộp (0,0)** — không vi phạm cột.
  - b3 (`[1][0]='5'`): vi phạm **hàng 1 + cột 0 + hộp (0,0)** — cả ba cùng lúc.
  - b4 (`[1][1]='5'`): vi phạm **hàng 1 + hộp (0,0)** — không vi phạm cột.
  - Không board nào vi phạm **chỉ** cột hoặc **chỉ** hộp. Mọi board False đều có vi phạm hàng.
- Bằng chứng: checker **chỉ kiểm tra hàng** đậu toàn bộ test; checker **chỉ kiểm tra hàng + cột** (bỏ hộp) cũng đậu toàn bộ test.
- Input phân biệt: board chỉ có `'5'` tại `[0][0]` và `[3][0]` (cùng cột, khác hàng, khác hộp) — checker chỉ-hàng trả `True`, đáp án đúng là `False`. Board chỉ có `'5'` tại `[0][0]` và `[1][1]` (chỉ vi phạm hộp) — checker hàng+cột trả `True`, đáp án đúng là `False`.
- Đề xuất bổ sung: 2 board trên, mỗi board assert `== False`.

## 5. Test MÂU THUẪN (loại (c)): KHÔNG CÓ

Không bài nào có test mâu thuẫn với spec đã viết. Các ứng viên nghi ngờ đã được kiểm tra kỹ và **loại trừ**:

| Ứng viên nghi ngờ | Kết quả kiểm tra |
|---|---|
| lcb_006: spec không nêu quy tắc hòa, test đòi một lát cắt cụ thể | Liệt kê mọi mảng con: mỗi test có **duy nhất** 1 lát cực đại → test không đòi hỏi thêm điều gì ngoài spec. Không mâu thuẫn. (Thiếu quy tắc hòa trong spec là điểm yếu của *spec*, không phải lỗi test, và không ảnh hưởng kết quả hiện tại.) |
| held2_009: spec khác LeetCode (trả list mới, không sửa input) | Test bám đúng spec đã viết, kể cả T7 kiểm tra input không đổi. Đáp án tham chiếu đậu; liệt kê hoán vị khớp mọi giá trị. Spec sạch — xem §7. |
| lcb_002 T5 `'(((******))' == True` | Kiểm chứng bằng cả liệt kê vét cạn (đáp án tham chiếu) lẫn phương pháp khoảng số ngoặc mở: đều True (1 `*` đóng vai `)`, còn lại rỗng → `((()))`). |
| lcb_009 T3 `'' → []` | Phù hợp quy tắc "không tạo được câu hợp lệ thì trả `[]`" của spec. |
| held2_007: helper `_valid` trong test | Đã kiểm tra trực tiếp: từ chối đúng thứ tự sai/thiếu/trùng, chấp nhận đúng thứ tự hợp lệ. Không mâu thuẫn. |
| held2_011 b2/b3/b4: vi phạm chồng lấn nhiều quy tắc | Giá trị kỳ vọng `False` đều đúng về mặt toán học (phân tích vi phạm ở §4.6). Việc chồng lấn chỉ làm test *thiếu* (loại (b)), không làm test *sai*. |
| lcb_004/lcb_017: test định nghĩa lại `ListNode` sau code lời giải | Đây là cơ chế nối chuỗi của harness: định nghĩa của test ghi đè định nghĩa của lời giải, nhưng cùng giao diện (`val`/`next`, `__init__(val=0, next=None)`), và mọi thao tác đều qua duck-typing. Đáp án tham chiếu đậu; không mâu thuẫn. |
| held2_008: test so sánh `== 2.0` nhưng `2 == 2.0` | Lỏng về kiểu (int cũng đậu) nhưng không mâu thuẫn: giá trị median đúng, và spec chỉ hứa `find_median` trả về median. |
| lcb_008: dict `count` | `count` = số khoảng gốc gộp vào, kiểm chứng bằng union-find khớp cả 4 test. |
| held2_012: tuyên bố nghiệm duy nhất | Mô phỏng mọi điểm xuất phát: mỗi test có đúng 0 hoặc 1 điểm khả thi. Tuyên bố đúng. |

## 6. Bảng chấm lại cũ/mới: KHÔNG CÓ

Vì loại (c) = 0, không có test nào được "sửa", không có lời giải nào được chấm lại, **không ô điểm nào đổi**. Bảng đối chiếu ở §1 là đầy đủ: mọi số headline giữ nguyên như đã chốt, McNemar không cần tính lại.

## 7. Kiểm tra bổ sung

### 7.1 Prompt trong traces khớp file local: 520/520

So sánh `prompt` của toàn bộ 520 file trong `data/raw_traces/` với prompt của bài tương ứng trong file local (35 bài trong phạm vi + 10 bài held-out v1): **0 lệch, 0 task_id lạ**. File local chính là thứ đã được dùng khi chạy. Traces không lưu `test_cases`, nên việc chấm hoàn toàn dựa vào file test local qua `run_test_cases` — đúng nguồn đã rà.

### 7.2 held2_009: kiểm tra độc lập, không tin mù

Biết trước bài này "spec sạch, lỗi ở lời giải model, trượt 0/4 cả base lẫn LoRA". Kiểm tra lại độc lập:

- Spec + test: đáp án tham chiếu (copy list, thuật toán chuẩn) đậu cả 8 mục test; liệt kê hoán vị bằng `itertools` khớp mọi giá trị kỳ vọng; T7 kiểm tra không sửa input hoạt động đúng (biến thể sửa input trượt).
- Traces: cả **8/8** file (base 4 + LoRA 4, mỗi bên 4 harness) đều `passed=False`, `mode=live`:
  - 5 file lỗi `IndexError: list index out of range` (lời giải crash — code quét hậu tố không xử lý được input rỗng/đơn trị).
  - 3 file lỗi `AssertionError` (lời giải trả giá trị sai).
- Kết luận: **spec và test sạch; 0/8 là lỗi thật của lời giải model**. Không đổi điểm.

### 7.3 Cơ chế chấm không có ngoại lệ ẩn

`passed` trong traces chỉ sinh ra từ `run_test_cases` (2 điểm gọi trong `02_run_helix_eval.py`: `_live_solution` và `run_evaluation`). Không có chuẩn hóa, làm tròn, hay so sánh mềm nào khác — mọi assert đều là `==`/`is` trực tiếp trong `test_cases`, trừ helper `_valid` của held2_007 (đã kiểm tra ở §3).

## 8. Hạn chế và khuyến nghị

**Hạn chế của đợt rà này:**

- Chỉ rà *test có bám spec đã viết không*, không rà *spec có phải là bài toán "chuẩn" không* (ví dụ: lcb_006 thiếu quy tắc hòa, lcb_005 không định nghĩa trùng lặp — đó là điểm yếu của spec, không phải lỗi test, và không ảnh hưởng điểm hiện tại vì không test nào chạm vào vùng mơ hồ).
- Không chạy lại lời giải trong traces với test đã sửa — vì không có test nào thuộc loại (c) nên không có cơ sở để chấm lại. Việc 6 bài loại (b) có làm *tăng* điểm của ô nào không (lời giải sai nhưng đậu nhờ test lỏng) là câu hỏi khác, ngoài quy tắc cam kết trước của đợt rà này; nếu muốn trả lời, cần một đợt phân tích riêng với test bổ sung được phê duyệt trước, và kết quả đó không được dùng để sửa số headline đã chốt.
- Yêu cầu độ phức tạp (O(1), O(log n)) và một phần yêu cầu "in-place" nằm ngoài khả năng của assert giá trị; đợt rà chỉ ghi nhận, không đo hiệu năng.

**Khuyến nghị (cho phiên bản benchmark sau, không hồi tố):**

1. Thêm các test bổ sung ở §4 cho 6 bài loại (b) (đã kiểm tra đậu với đáp án tham chiếu).
2. Bổ sung quy tắc hòa cho lcb_006 trong spec (ví dụ: "nếu nhiều lát cắt cùng tổng lớn nhất, trả về lát cắt có chỉ số bắt đầu nhỏ nhất") để spec chặt chẽ hơn, dù hiện tại không test nào hòa.
3. Giữ nguyên tắc "mỗi hành vi nêu trong spec phải có ít nhất một test phân biệt được" khi thêm bài mới — đặc biệt với các yêu cầu về thứ tự output (dùng input chưa sắp xếp / dict chưa sắp xếp) và các quy tắc nhiều thành phần (sudoku: vi phạm riêng từng thành phần).

## 9. Tái chạy kiểm tra

Các script kiểm tra (chỉ đọc, CPU local) nằm trong `scripts/` cùng thư mục với báo cáo này:

| Script | Việc làm |
|---|---|
| `scripts/refs.py` | 35 đáp án tham chiếu viết độc lập từ spec |
| `scripts/run_ref_check.py` | Chạy 35 đáp án với đúng test gốc, đúng ngữ nghĩa `run_test_cases` → 35/35 đậu |
| `scripts/brute_checks.py` | Kiểm chứng giá trị kỳ vọng bằng vét cạn/phương pháp độc lập → 0 lệch |
| `scripts/probes.py` | 18 probe biến thể lỗi + kiểm tra cấu trúc (AST literal, helper `_valid`, mô phỏng LRU, `statistics.median`) |
| `scripts/extract_all35.py` | Trích xuất 35 bài từ nguồn gốc (AST từ `02_run_helix_eval.py` + 2 file JSON) ra `/tmp/all35.json` cho các script trên |
| `scripts/confirm_gaps.py` | Input phân biệt cụ thể cho 5/6 bài loại (b) (lcb_019 đã xác nhận trong `probes.py`) |
| `scripts/trace_check.py` | So sánh prompt 520 traces với file local; liệt kê 8 traces held2_009 |
| `scripts/verify_suggested.py` | Kiểm tra các test bổ sung đề xuất ở §4 đều đậu với đáp án tham chiếu |

Chạy lại: trước tiên `python3 scripts/extract_all35.py` để tạo `/tmp/all35.json` từ nguồn gốc, sau đó `python3 scripts/run_ref_check.py`, `python3 scripts/brute_checks.py`, `python3 scripts/probes.py`, `python3 scripts/confirm_gaps.py`, `python3 scripts/trace_check.py`, `python3 scripts/verify_suggested.py` (chạy từ thư mục `test-audit-2026-11-13/`; `brute_checks.py` và `confirm_gaps.py` không cần `/tmp/all35.json`).
