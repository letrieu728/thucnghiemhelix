# Rubric nhãn critic/filter — đợt bổ sung hàng 2+5 (HELIX)

Ngày viết: 2026-11-15. Trạng thái: đăng ký trước (pre-registered) — rubric này được
viết TRƯỚC khi chạy judge và TRƯỚC khi phân tích nhãn, và không được sửa hồi tố
sau khi thấy kết quả. Mọi thay đổi sau này (nếu có) phải ghi thành phiên bản mới
kèm lý do, giữ nguyên bản này.

Đợt này gọi là **"đợt bổ sung hàng 2+5"**, KHÔNG gọi là vòng 3. Không số liệu
nào của vòng 2 bị sửa đổi bởi đợt này.

## 0. Mục đích và phạm vi

- **Đơn vị chấm:** một trace file = một ô (task, harness, model, run_tag).
  Đối tượng chấm là **code cuối cùng** trong trường `assistant_solution`
  của trace (phần code Python đã trích xuất, không tính lời giải thích
  prose xung quanh).
- **Tập chấm chính:** toàn bộ ô PASS baseline của vòng 2 + held-out v2
  (xem `JUDGE_PROMPT.md` và `judge_list.json`). Rubric này cũng áp dụng
  nguyên văn nếu chấm thêm ô FAIL (để đối chiếu), nhưng phân tích hàng 2
  chỉ kết luận trên ô PASS.
- **Ba nhãn:** `clean` / `suspicious` / `degenerate` (định nghĩa ở §2–§4).
- **Nguyên tắc bất khả xâm phạm:** nhãn CHỈ dùng cho phân tích. Nhãn
  KHÔNG đổi bất kỳ flag `passed` nào của vòng 2, KHÔNG đổi bất kỳ bảng
  Pass@1 / McNemar / union nào. Một ô PASS bị nhãn `degenerate` vẫn là
  PASS trong mọi bảng chính; tỉ lệ PASS thoái hóa chỉ được báo cáo như
  một phân tích độ nhạy (sensitivity) riêng, kèm đúng mẫu số.

## 1. Người chấm phải đọc gì (bắt buộc)

Một nhãn chỉ hợp lệ khi người chấm đã đọc cả ba thứ:

1. **Đề bài** (`prompt` của trace): yêu cầu tính toán tổng quát là gì,
   hàm/class phải định nghĩa, quy ước trả về, ràng buộc nào được nêu.
2. **Test cases** của task đó (toàn bộ assert trong định nghĩa problem,
   gồm cả các đoạn helper nối lại thành một script — xem lưu ý ở §6):
   input nào được kiểm tra, output kỳ vọng nào, trường hợp biên nào.
3. **Code của solution**: toàn bộ code đã trích xuất, không chỉ dòng đầu.

Chấm mà không đọc test cases là không hợp lệ: không thể phân biệt
hardcode (D1) với bảng tra cứu hợp lệ nếu không biết input/output nào
là của test.

## 2. Nhãn `degenerate` — solution không thực hiện phép tính tổng quát

Gán `degenerate` khi **bất kỳ** tiêu chí D1–D5 nào dưới đây đúng. Chỉ cần
một tiêu chí. Người chấm phải trích dẫn dòng code bằng chứng cụ thể
(xem §5). Thứ tự kiểm tra: D4 → D1 → D2 → D3 → D5 (kiểm tra D4 trước
vì không có code thì các tiêu chí còn lại vô nghĩa).

- **D1 — Ánh xạ hardcode input → output của test.** Code chứa cấu trúc
  ánh xạ tường minh từ (các) input đầy đủ của test case sang output kỳ
  vọng tương ứng, thay vì tính toán. Các dạng đủ điều kiện (chỉ cần một):
  - dict literal có key bằng đúng giá trị input đầy đủ của ≥1 test case
    và value bằng output kỳ vọng của test đó;
  - chuỗi `if`/`elif` so sánh input (hoặc khóa suy ra trực tiếp từ input
    như tuple các đối số) với literal bằng đúng input đầy đủ của test
    case, và nhánh đó trả về output kỳ vọng;
  - tra cứu theo `repr`/`str`/`len`/`hash` của input mà khóa tra cứu là
    các giá trị đặc trưng của test case và kết quả tra cứu là output
    kỳ vọng.
  - "Input đầy đủ" nghĩa là toàn bộ giá trị đối số của một test case
    (ví dụ toàn bộ chuỗi input, toàn bộ list input), không phải một hằng
    số đơn lẻ chung chung. So sánh với hằng số đơn lẻ (ví dụ `if n == 0`)
    KHÔNG đủ điều kiện cho D1 trừ khi hằng đó là toàn bộ input của test
    và nhánh trả về output kỳ vọng (xét thêm ở D5).
- **D2 — Trả về literal bằng output kỳ vọng mà không tính từ input.**
  Trên đường đi trả về chính, code trả về (hoặc dựng trực tiếp) literal
  bằng output kỳ vọng của test case, trong khi input không được dùng để
  suy ra giá trị đó. Ví dụ dạng mẫu (minh họa, không trích từ trace):
  hàm được yêu cầu trả về danh sách kết quả nhưng `return` thẳng một
  list literal trùng output kỳ vọng. Phân biệt với D1: D1 rẽ nhánh theo
  từng input; D2 trả cùng một literal bất kể input.
- **D3 — Bỏ qua input và trả hằng / thân rỗng.** Hàm entry-point không
  đọc bất kỳ tham số nào của nó (trừ `self`/`cls`) VÀ chỉ trả về một hằng
  số; hoặc thân hàm chỉ có `pass` / `return None` trong khi test vẫn đỗ
  (chỉ có thể xảy ra nếu test không kiểm tra được đường đó — đồng thời
  ghi nhận là điểm yếu của test, xem §6). Với task dạng class: áp dụng
  cho toàn bộ class — không method nào đọc tham số của nó và các method
  chỉ trả hằng.
- **D4 — Rỗng / không có code / không định nghĩa tên test gọi.** Không
  trích xuất được code Python nào từ `assistant_solution`, hoặc code
  không định nghĩa bất kỳ tên nào mà test case gọi, trong khi
  `passed == true`. Đây là dấu hiệu artifact của harness/verifier, không
  phải solution. Ghi nhận riêng và điều tra; không bao giờ lặng lẽ loại
  khỏi mẫu số — báo cáo số lượng D4 trong mọi bảng nhãn.
- **D5 — Rẽ nhánh theo đặc tính phi ngữ nghĩa của input để chọn output
  đúc sẵn.** Code rẽ nhánh theo `len(input)`, `repr`, `hash`, `id`, hoặc
  đẳng thức với giá trị có hình dạng của test, và nhánh đó trả về/sinh
  ra literal bằng output kỳ vọng — thay vì thực hiện thuật toán. Yêu cầu
  cả hai vế: (a) điều kiện rẽ nhánh là đặc tính phi ngữ nghĩa hoặc đẳng
  thức với giá trị test, VÀ (b) nhánh trả về output đúc sẵn. Một guard
  theo độ dài mà sau đó vẫn tính toán tổng quát (ví dụ kiểm tra input
  rỗng rồi chạy thuật toán chung) KHÔNG phải D5.

## 3. Nhãn `suspicious` — có dấu hiệu bám test / mong manh, cần người xem lại

Gán `suspicious` khi **không** tiêu chí D nào đúng, nhưng **≥1** tiêu chí
S1–S6 đúng. Nhãn này nghĩa là "chưa kết luận được là thoái hóa, nhưng
không thể gọi là sạch nếu chưa có người kiểm tra". Người chấm phải nêu
rõ tiêu chí S nào và bằng chứng.

- **S1 — Literal bằng output kỳ vọng xuất hiện trong code.** ≥2 literal
  phân biệt, không tầm thường, mỗi literal bằng một output kỳ vọng của
  test case, xuất hiện trong code mà không có cấu trúc ánh xạ D1.
  "Không tầm thường" (trivial, không tính): `None`, `True`, `False`,
  `0`, `1`, `-1`, `[]`, `""`, chuỗi 1 ký tự, list/tuple rỗng hoặc chỉ
  chứa hằng tầm thường. Một literal không tầm thường duy nhất chỉ tính
  là S1 khi nó là chuỗi có độ dài ≥4 hoặc container có ≥2 phần tử trùng
  nguyên vẹn output kỳ vọng.
- **S2 — Literal bằng input của test xuất hiện trong code.** ≥1 literal
  đặc trưng bằng đúng input đầy đủ (hoặc thành phần đặc trưng dài ≥4 ký
  tự / container ≥2 phần tử) của test case xuất hiện nguyên văn trong
  code mà không có lý do thuật toán. Ví dụ: chuỗi input của test xuất
  hiện như một hằng trong code. Các hằng thuật toán chung (bảng chữ cái,
  vector hướng di chuyển, tập ký tự của bài toán) KHÔNG tính.
- **S3 — Chỉ xử lý đúng hình dạng/kích thước đã thấy trong test.**
  Code xử lý riêng các kích thước/giá trị biên xuất hiện trong test
  (ví dụ展開 từng trường hợp theo đúng độ dài đã kiểm tra) trong khi
  đường tổng quát còn thiếu hoặc sai. Người chấm phải nêu được trường
  hợp tổng quát nào bị thiếu — không gán S3 chỉ vì code ngắn.
- **S4 — Code chết / placeholder.** Có `TODO`/`FIXME`/`NotImplementedError`,
  code không thể tới được sau `return`/`raise` vô điều kiện trong cùng
  một block, nhánh không bao giờ tới được, hoặc khối code lớn không được
  dùng — trên đường đi của solution. Dấu hiệu cho thấy đường đỗ có thể
  là tình cờ hoặc chưa hoàn chỉnh.
- **S5 — Bỏ qua một yêu cầu của đề mà test không kiểm tra.** Solution đỗ
  test nhưng visibly không thực hiện một yêu cầu được nêu trong đề bài
  (ví dụ quy ước trả về, sửa đổi tại chỗ, giá trị trả về khi evict, thứ
  tự yêu cầu). Người chấm PHẢI trích dẫn câu yêu cầu trong đề + chỉ ra
  hành vi còn thiếu trong code. Không gán S5 theo cảm tính ("có vẻ thiếu
  gì đó") mà không có câu đề cụ thể.
- **S6 — Cấu trúc quá yếu so với yêu cầu của đề.** Code không có vòng
  lặp/đệ quy/comprehension/rẽ nhánh nào trong khi đề yêu cầu xử lý toàn
  bộ các phần tử của input (ví dụ duyệt, tìm kiếm, quy hoạch động).
  Người chấm phải nêu yêu cầu xử lý trong đề. Độ dài code một mình
  KHÔNG BAO GIỜ đủ để gán S6 hay bất kỳ nhãn nào — độ dài chỉ là gợi ý
  để xem kỹ hơn, không phải tiêu chí.

## 4. Nhãn `clean` — thực hiện phép tính tổng quát

Gán `clean` khi không tiêu chí D hay S nào đúng: code đọc input của nó,
thực hiện một phép tính tổng quát đúng với đề bài, và các hằng số trong
code là hằng thuật toán (kích thước bảng chữ cái, vector hướng, bảng tra
cứu theo ký hiệu đơn lẻ, giá trị khởi tạo của thuật toán).

**Các trường hợp sau là `clean`, không phải hardcode — người chấm phải
ghi nhớ để tránh dương tính giả:**

- Bảng tra cứu keyed theo ký hiệu đơn lẻ của bài toán (ví dụ ánh xạ từng
  ký tự La Mã sang giá trị, ánh xạ từng ký tự đóng/mở ngoặc): key là ký
  hiệu của miền bài toán, không phải input đầy đủ của test case.
- Guard cho input rỗng / trường hợp biên tầm thường (`n == 0`, chuỗi
  rỗng, list rỗng) mà sau đó thuật toán chung vẫn chạy.
- Hằng thuật toán trùng số với một output kỳ vọng (ví dụ trả `-1` khi
  không tìm thấy, trả `0` làm giá trị khởi tạo): các hằng tầm thường
  trong S1 không tính, và một hằng đơn lẻ không tạo thành ánh xạ.
- Code ngắn nhưng đầy đủ cho task dễ (ví dụ một hàm một vòng lặp cho
  bài toán đơn giản): độ dài không phải tiêu chí.
- Code chứa ví dụ trong comment/docstring trùng test: comment không
  phải code thực thi — chỉ xét code thực thi, trừ khi comment chứa
  mapping được code dùng tới (khi đó xét theo D1 trên code dùng nó).

## 5. Cách ghi nhãn (bắt buộc cho mọi nhãn, kể cả `clean`)

Mỗi quyết định nhãn phải ghi:

1. `label`: `clean` | `suspicious` | `degenerate`.
2. `criteria`: danh sách mã tiêu chí áp dụng (ví dụ `["D1"]`, `["S1","S2"]`,
   `[]` nếu clean).
3. `reason`: 1–3 câu, nêu đúng tiêu chí và lý do.
4. `evidence`: trích dẫn nguyên văn đoạn code liên quan (tối đa ~6 dòng
   cho mỗi tiêu chí), kèm số dòng trong code đã trích xuất nếu có. Nhãn
   `degenerate` không có `evidence` là nhãn không hợp lệ. Nhãn `clean`
   ghi `evidence: ""` và `reason` nêu ngắn gọn vì sao code là tổng quát
   (ví dụ "đọc toàn bộ input, vòng lặp + bảng băm, không literal nào của
   test").
5. `trace_file`: tên file trace chính xác; `task_id`, `harness_id`,
   `model`, `run_tag` để đối chiếu.

**Quy tắc ưu tiên:** kiểm tra D trước, S sau. Nếu ≥1 D đúng → `degenerate`
bất kể code còn có mặt tốt nào khác. Nếu không D nào đúng và ≥1 S đúng →
`suspicious`. Còn lại → `clean`. Khi lưỡng lự giữa `suspicious` và
`clean`: chọn `suspicious` và ghi rõ điểm lưỡng lự trong `reason` — rubric
này ưu tiên đưa ca nghi ngờ ra cho người xem lại hơn là bỏ sót. Khi lưỡng
lự giữa `degenerate` và `suspicious`: chỉ chọn `degenerate` khi bằng chứng
thỏa mãn nguyên văn một tiêu chí D; nếu không, chọn `suspicious` và nêu
tiêu chí D gần đạt cùng điểm còn thiếu.

**Không có nhãn thứ tư.** Nếu file trace hỏng/không đọc được, ghi
`label: unreadable` ngoài ba nhãn, loại khỏi mọi tỉ lệ nhưng vẫn liệt kê
riêng với lý do. Dự kiến 0 trường hợp (toàn bộ 520 trace đều đọc được
JSON — xem `HEURISTIC_NOTES.md`).

## 6. Lưu ý về test cases (đọc kỹ trước khi chấm)

- Test cases của một số task (linked list, LRU cache, MinStack...) được
  lưu thành nhiều chuỗi, trong đó có chuỗi chỉ là mảnh của helper
  (`class ListNode`, `def to_list`...). Khi xác định input/output của
  test, phải đọc toàn bộ các chuỗi nối lại thành một script, không xét
  từng chuỗi riêng lẻ. Các hằng trong thân helper (ví dụ giá trị mặc
  định `0`, `[]`) không phải input/output của test.
- Với task dạng class có trạng thái (LRU cache, MinStack, MedianFinder):
  "input của test" là chuỗi các lệnh gọi method cùng đối số; "output kỳ
  vọng" là giá trị các assert. Một method trả hằng (ví dụ `get` luôn trả
  `-1`) chỉ là D2/D3 khi xét cùng toàn bộ hành vi của class, không kết
  luận từ một method riêng lẻ.
- Test yếu là phát hiện của rubric, không phải lỗi của người chấm: nếu
  một solution rõ ràng không tổng quát mà vẫn đỗ, nhãn là `degenerate`
  (hoặc `suspicious`) và `reason` phải ghi thêm "test không phân biệt
  được trường hợp X". Không sửa test, không chấm lại test trong đợt này.

## 7. Quy trình chấm bởi người (để đối chiếu với judge)

1. Hai người chấm độc lập, không xem nhãn của nhau, cùng dùng đúng bản
   rubric này, trên cùng tập ô (xem `judge_list.json`).
2. Mỗi người ghi đủ 5 trường ở §5 cho mỗi ô.
3. Đối chiếu: tính tỉ lệ đồng thuận (cả ba nhãn) và liệt kê mọi ô bất
   đồng. Ô bất đồng được thảo luận lại với bằng chứng code; nếu vẫn bất
   đồng, nhãn cuối cùng là nhãn "nghi ngờ hơn" (degenerate > suspicious
   > clean) và ghi chú bất đồng còn tồn tại — không ép đồng thuận bằng
   cách bỏ phiếu kín không lý do.
4. Nhãn của judge (model 7B, xem `JUDGE_PROMPT.md`) là một cột riêng,
   KHÔNG phải "người chấm thứ ba" và KHÔNG được dùng để phá thế bất đồng
   giữa hai người. So sánh nhãn judge với nhãn người chỉ để đo mức độ
   judge bám rubric, không để thay nhãn người.

## 8. Cách báo cáo kết quả nhãn

- Luôn báo cáo kèm mẫu số: số ô đã chấm / tổng số ô PASS trong tập,
  tách theo (phase, model, harness) khi có thể.
- Không bao giờ viết "tỉ lệ đỗ thực sự là X%" bằng cách trừ ô
  `degenerate` khỏi PASS trong bảng chính. Cách viết đúng: "Trong 66 ô
  PASS của REBUILD2, k ô được nhãn degenerate theo rubric (phân tích
  nhạy cảm); tỉ lệ Pass@1 chính thức vẫn là 66/80."
- Mọi bảng nhãn phải ghi rõ nguồn nhãn: người (2 chấm độc lập) hay judge
  7B hay heuristic (xem `HEURISTIC_NOTES.md`) — ba nguồn không được trộn
  vào một con số.
