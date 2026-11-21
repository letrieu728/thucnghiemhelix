# DESIGN — O1: Lặp lại các ô quyết định của O2 (thay "1 lượt/ô" bằng 2 lượt/ô)

Ngày viết: 2026-11-20. Thiết kế đăng ký trước (pre-registered) TRƯỚC khi chạy bất kỳ lệnh GPU nào.
Chương trình: cải thiện HELIX $6 (ngân sách còn lại ~$6,00 credit, tài khoản $30).
Người duyệt thiết kế: Triệu (chưa duyệt chạy — chỉ duyệt thiết kế thì mới được chạy).
**Chạy SAU O2** (thứ tự bắt buộc: O1 lặp lại đúng các ô O2 đã chạy; không chạy trước O2).

## 0. Vấn đề (đã xác minh — điểm yếu W3 trong AUDIT.md 20/11/2026)

Mọi số headline của nhóm đến nay đều đứng trên **1 lượt/ô**, trong khi base
pi-mono tự trôi giữa các lần chạy cùng giao thức: 25/35 (bước 2) → 20/35
(fix) → 22/35 (lặp lại bước 1) → 23/35 (ablation bước 3). Chênh lệch dưới
~5 bài nằm trong nhiễu chạy-lại. O2 sẽ cho ra một bộ số headline mới
(adapter sạch trên 45 bài) — nếu chỉ chạy 1 lần, bộ số đó mang đúng điểm
yếu đã khiến ablation SFT-only (bước 3) không kết luận được: realtool tự
nó đã dao động 28→29→25 qua các lần chạy.

O1 không tạo khẳng định mới. Nó đo **phương sai** của các khẳng định O2
đưa ra.

## 1. Mục tiêu (đăng ký trước)

Cho mỗi ô của O2, có thêm 1 mẫu độc lập nữa (tổng 2 lượt/ô), để nhóm được
phép nói — thay vì "mỗi ô 1 lần chạy" — một **khoảng đo được** cho các số
headline mới (ví dụ: "adapter sạch trên 30 bài chưa thấy đạt X/30 rồi Y/30
qua hai lần chạy; base đạt A/30 rồi B/30").

## 2. Phạm vi lặp — toàn bộ 135 ô của O2, lặp 1 lần

- Ô lặp: **3 nhánh × 45 bài của O2** (base, `helix-lora-clean`,
  `helix-lora-realtool` × held2 + held3 + held4), pi-mono, đúng giao thức
  O2 §4 (cùng driver, cùng deployment variant C, cùng `prompt_template.txt`,
  cùng test suite, max-steps 12, timeout 600 s, 1 lượt/ô cho lần lặp này).
- Tổng: **135 lượt** (không thêm nhánh, không thêm bài, không thêm harness).
- Không lặp O3 hay O5 (chúng là thăm dò n = 10/16 — lặp chúng không đổi
  được kết luận; tiền dành cho các ô quyết định).
- Không lặp các ô của các đợt cũ (fix 28/35, gen 13/15 đã có 2–3 mẫu lịch
  sử qua bước 1 lặp lại: realtool 28→29, base 25→20→22→23 — đủ để biết
  chúng trôi; lặp lại chúng lần nữa không thêm thông tin cho câu chuyện
  adapter sạch).

## 3. Phân tích — đăng ký trước (không đổi sau khi thấy kết quả)

- Mỗi ô: 2 kết quả (lượt O2 + lượt O1). Báo cáo:
  - Tỉ lệ ô đồng thuận (cùng PASS/FAIL ở cả hai lượt) theo nhánh và theo
    cohort (held2/held3/held4).
  - Pass@1 gộp 2 lượt cho mỗi nhánh × cohort (k/30 cho cohort 15 bài,
    k/60 cho so sánh chính 30 bài, k/90 cho bảng 45 bài) + Wilson 95% CI.
    Đây là **tỉ lệ mô tả trên 2 lượt**, không phải một ước lượng độc lập mới.
  - So sánh chính (mới vs base, 30 bài chưa thấy): McNemar tính RIÊNG
    cho từng lượt (lượt O2 và lượt O1) — KHÔNG gộp p-value qua hai lượt
    (hai lượt là replicate, không phải mẫu độc lập mới; gộp p-value là sai).
    Báo cáo cả hai p cùng khoảng chênh lệch (gains−losses) mỗi lượt.
  - Kiểm tra base drift trong một chương trình: base lượt O2 vs base lượt
    O1 trên cùng 45 bài. Nếu base dịch ≥ 4 bài giữa hai lượt thì ghi rõ
    "drift trong-chương-trình ≥ 4 bài — mọi so sánh một-lần-chạy đều hạ
    xuống mức mô tả" và điều này đi vào slide 15/16 khi đồng bộ (O6).
- Phán quyết O2 được ĐỌC LẠI dưới ánh sáng O1 (ghi vào RESULTS.md của O1,
  không sửa RESULTS.md của O2 sau khi viết):
  - Nếu C1/C2 của O2 giữ nguyên ở lượt lặp (cùng phán quyết cả hai lượt)
    → "phán quyết O2 ổn định qua 2 lượt".
  - Nếu phán quyết đổi giữa hai lượt (ví dụ C2 đạt ở lượt O2, hụt ở lượt
    O1) → "phán quyết O2 KHÔNG ổn định — báo cáo cả hai lượt, không chọn
    lượt đẹp". Không được chọn lượt có kết quả đẹp hơn để báo cáo.

## 4. Chi phí ước tính

- 135 lượt pi-mono × $0,012/lượt = **$1,62** (cùng căn cứ như O2 §6:
  ablation $0,0093/lượt; gen pi-mono $0,0111/lượt).
- Deploy dùng chung với cả chương trình (xem PROGRAM_BUDGET.md):
  phần O1 **$0,15** (chỉ tính nếu O1 cần deploy riêng; $0 nếu chạy trong
  cùng phiên deploy với O2/O3/O5).
- **Tổng O1 ≈ $1,77** (khoảng dự toán $1,60–1,80).

## 5. Quy tắc cắt giảm — đăng ký trước (theo thứ tự, không quyết sau khi thấy O2)

Nếu checkpoint billing sau O2+O3 dự báo tổng chương trình vượt $6,00
(xem PROGRAM_BUDGET.md §4), O1 được cắt theo thứ tự sau — cắt NHÁNH
trước, cắt BÀI sau, và không bao giờ cắt nhánh mới (nó là nhân vật chính):

1. **Cắt nhánh cũ** (`helix-lora-realtool`, 45 lượt): số của nhánh cũ
   trên 30 bài đã có từ bước 4b (26/30) — lặp nó là xa xỉ nhất.
   Còn lại 90 lượt (~$1,08).
2. **Cắt cohort held2** (mới + base trên held2, 30 lượt): held2 là so
   sánh phụ. Còn lại 60 lượt (~$0,72) — đúng các ô so sánh chính.
3. **Tối thiểu khả thi:** 60 ô so sánh chính (mới + base × held3+held4).
   Nếu ngay cả 60 ô này cũng dự báo vượt ngân sách thì DỪNG O1 hoàn toàn,
   báo cáo O2 là "1 lượt/ô" như cũ — không vay ngân sách của O5.

Việc cắt giảm nào đã áp dụng (nếu có) phải ghi trong RUN_LOG.md kèm số
billing tại thời điểm quyết định. Không cắt giảm nào được quyết sau khi
thấy kết quả O2 (chỉ theo billing, như trên).

## 6. Rủi ro

- Hai lượt vẫn là n nhỏ: khoảng đo được sẽ rộng (ví dụ 24–27/30) — đó là
  đáp án trung thực, không phải thất bại.
- Drift giữa hai lượt có thể lớn hơn kỳ vọng (base đã trôi ±3 bài giữa
  các đợt) — nếu vậy O1 làm YẾU câu chuyện O2 thay vì củng cố nó. Đó
  vẫn là thông tin đúng cần báo cáo, không phải lý do giấu lượt lặp.
- Thứ tự chạy (O2 trước, O1 sau) làm hai lượt không hoán đổi được với
  thời gian chạy (time confound) — ghi rõ trong limitations; không có
  cách nào tránh trong ngân sách này (xen kẽ lượt sẽ tốn thêm deploy).

## 7. Quy tắc sàn + dừng (tuyệt đối, không ngoại lệ)

- Token Modal đã hết hạn (19/11 10:25 +07, xác minh 20/11 20:11).
  CHỈ chạy GPU sau khi Triệu cấp lại quyền trong trình duyệt của mình.
  Nếu auth lỗi: DỪNG GPU ngay, làm phần offline, báo cáo.
- Snapshot `modal billing summary --json` TRƯỚC mọi GPU, sau O1, sau khi
  dừng app. Nếu billed_cost > $0,00 ở bất kỳ lần kiểm tra nào: DỪNG toàn
  bộ GPU ngay lập tức.
- Trước khi deploy (nếu cần deploy riêng): `modal app list`; chỉ deploy
  khi 0 task đang chạy; KHÔNG BAO GIỜ dừng app của người khác. Sau mỗi
  lượt: dừng app + tự kiểm tra `modal app list` = 0 task.
- Upstream git-clean (HEAD b5adffa) kiểm tra trước deploy đầu và sau GPU
  cuối; fork ghi trạng thái trước/sau (kỳ vọng không đổi: 94 D + 2 ??).
  KHÔNG commit/push ở đâu. KHÔNG sửa slide/Drive/GitHub/Canva.
- Quy tắc INFRA/rerun như O2 (tối đa 1 rerun/ô INFRA, ghi REPLACEMENTS.log).

## 8. Tái dùng (diff-verified trước GPU; ghi vào RUN_LOG §0)

Toàn bộ file của O2 (train script đã chạy xong, driver, compute_stats.py,
verify_scoring.py, tasks.json 45 bài, prompt_template.txt) — dùng lại
nguyên trạng, không sửa gì trừ cờ `--repeat` / thư mục đích `runs-repeat/`
(tránh ghi đè kết quả O2). Kết quả O2 là read-only đối với bước này.

## 9. Deliverables (dưới thư mục này)

DESIGN.md (file này), RUN_LOG.md, RESULTS.md, summary.json, summary.md,
billing JSONs, app-list logs, git-status snapshots,
`runs-repeat/pi-mono/<model>/<task>/` (135 ô, tách riêng khỏi runs của O2).
