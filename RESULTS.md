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

## Xác minh offline lần 2 (2026-11-10)

- `npm run typecheck`: **PASS** trên cùng checkout `a090aba`.
- Các lệnh `tsx` được chạy lại ngoài sandbox, nơi `node:os.userInfo()` hoạt
  động bình thường. Kết quả: assembly contract, 9 flow-graph artifact,
  executable audit, TODO-27 inventory và OpenCode acceptance đều **PASS**.
- Task-parity/cadence, split task-parity và current-module audit **FAIL** do
  artifact không còn nhất quán với các metadata, hash/kích thước attachment,
  hoặc fingerprint mà verifier yêu cầu. Đây là kết quả của verifier, không phải
  lỗi môi trường.
- Tái sinh cassette task-parity trên clean worktree `a090aba` bị **BLOCKED**:
  Windows trả `EPERM` khi CLI tạo thư mục workspace tạm, kể cả khi `TEMP/TMP`
  trỏ vào thư mục riêng trong worktree. Không có artifact mới được dùng để
  thay thế artifact hiện có.
- Đã thử `npm test` trên clean worktree. Vitest quan sát được failure ngay ở
  `tools.conformance` (4 test) và `hooks.conformance` (1 test), nhưng môi
  trường điều phối không trả tổng kết/exit code của toàn suite; chưa báo cáo
  tổng số failure cuối cùng.

## Xác minh offline trên Linux (2026-11-11)

Clean clone HELIX tại cùng commit `a090aba`, `git status` sạch, chạy trên
Linux (kernel 7.0.0-44-generic), Node `v24.22.1`, npm `10.9.4`. Chi tiết đầy
đủ trong `results/2026-11-11-linux-verification.md`, log thô trong
`results/2026-11-11-*.txt`.

- **Verifier: không đổi so với 10/11.** 6 PASS (typecheck, assembly contract
  strict 5 product, flow graph 9/9 artifact, executable audit fingerprint
  `44370eff3ea1ca3a`, TODO-27 inventory fingerprint `e12a2bb0941ac9c7`,
  OpenCode acceptance ready-for-review 108/124 native) và 4 FAIL y hệt
  (task parity + cadence thiếu metadata acceptance-timing drift; split
  parity lệch hash/kích thước attachment; current-module audit fingerprint
  `ce386...` khác `413e...` tính lại). Các FAIL là tính chất của artifact
  đã commit, không phải của hệ điều hành.
- **Tái sinh cassette: vẫn BLOCKED, nhưng nguyên nhân khác.** Trên Linux
  lỗi là `ENOENT`, không phải `EPERM`: 101 fixture trong
  `packages/conformance/fixtures/tasks` là symlink commit trong git, tất cả
  trỏ tới đường dẫn tuyệt đối trên máy tác giả
  (`/home/HarnessLego-pi-lcb-eval/...`), 101/101 hỏng trên mọi máy khác.
  Không artifact mới nào được sinh ra.
- **`npm test` lần đầu có tổng kết cuối cùng:** exit 1, 20 file fail / 88
  pass (108 file), 26 test fail / 797 pass (823 test), 317,07 giây. Phân
  loại theo log: 4 test fail vì symlink fixture hỏng, 2 file fail vì thiếu
  binary native `node-pty` (do cách cài đặt, xem dưới), 8 test fail vì
  timeout trên VM 1,5 CPU, 12 test fail do assertion. Riêng
  `tools.conformance` (26 test) và `hooks.conformance` (22 test) **PASS**
  trên Linux, khác với lần chạy Windows.
- **Lưu ý về cài đặt:** `npm ci` thuần **FAIL** trong sandbox Linux này
  (build native `node-pty` lỗi `EPERM` ở `fchown` khi giải nén tarball);
  đã dùng `npm ci --ignore-scripts` (exit 0) để chạy các verifier và test.
  Các verifier dùng `tsx`/`tsc` không cần `node-pty` nên không bị ảnh
  hưởng; 2 file test nạp `node-pty` thì fail vì thiếu binary native.

Còn thiếu sau lượt này: sửa 101 symlink tuyệt đối rồi sinh lại cassette;
sửa 3 artifact verifier đang FAIL; chạy lại full test trên máy có build
`node-pty` đầy đủ để tách lỗi cài đặt/timeout khỏi lỗi thật. Benchmark
mất phí vẫn không chạy, theo phạm vi của repo.

## Nỗ lực sửa trên Linux, cùng ngày 2026-11-11 (ĐÃ PUSH tối 11/11)

> Cập nhật 12/11: lượt sửa này đã được user duyệt và push tối 11/11, đủ
> 33/33 file (remote mới nhất lúc đó `ae3f6b7`); 2 file lớn lên dạng
> gzip+base64 `.gz.b64`, đã kiểm chứng sha256 khớp bản gốc. Xem
> `results/2026-11-11-large-files-gz-note.md`.

Chi tiết đầy đủ trong `results/2026-11-11-linux-fix-attempt.md`.

- **`node-pty` đã build được bằng đường vòng:** tải header Node v24.22.1
  bằng tay, giải nén với `--no-same-owner`, rồi `node-gyp rebuild
  --nodedir=/tmp/node-headers` cho ra `build/Release/pty.node`, load được.
  Chạy lại full test với `node-pty` đầy đủ: **19 file fail / 89 pass
  (108), 29 test fail / 805 pass (834)**, 291,48 giây, exit 1. Số test fail
  tăng không phải là thụt lùi: 2 file trước đây fail lúc load (0 test) giờ
  chạy được 11 test, 8 pass, 5 fail — cả 5 đều do symlink hỏng (§ dưới).
  So với lượt trước: 2 test hết fail, 5 test mới hiện ra, 24 test vẫn fail.
  Phân loại 29 lỗi: 10 do symlink ENOENT, 6 timeout trên VM 1,5 CPU,
  13 assertion thật.
- **Current-module audit: ĐÃ SỬA.** Sinh lại bằng `npm run
  current-module:audit` cho fingerprint mới `d18dadd33fec5d5a`, verify lại
  **PASS**. Artifact gốc tháng 6 đã cũ, không phải sai một hằng số.
- **Split parity: ĐÃ SỬA.** Tính lại hash/kích thước của 96 attachment
  (40/96 lệch, đều thuộc 5 task × 4 product × 2 mode, file trên đĩa nhỏ
  hơn manifest 12 hoặc 24 byte), cập nhật đúng 40 mục manifest, verify lại
  **PASS 403/403**.
- **Task parity + cadence: ĐÃ SỬA trên artifact MỚI.** Nội dung 101 task
  LCB v6 không nằm ở đâu khác trong repo (chỉ có 1 task LCB thật là
  `livecodebench-1883`); không bịa fixture. Chạy lại bằng `--task` liệt kê
  đúng 12 task smoke thật — hóa ra đó là toàn bộ smoke suite, artifact gốc
  tháng 6 cũng đúng 12 task, 96 report, 48 matched / 48 acceptable-drift
  đó. Artifact mới sinh 2026-11-11 (96 report, 48/48) verify **PASS 13/13**,
  gồm đúng check `acceptance-timing.drift-metadata` từng fail. Artifact gốc
  vẫn giữ nguyên và vẫn FAIL, không ghi đè.
- **Cassette livecodebench100: vẫn không sinh được.** 101 symlink trỏ tới
  máy tác giả, file thật chưa từng có trong repo hay git history.

Còn thiếu sau lượt sửa này: push (chờ user duyệt + cấp quyền ghi cho app);
sửa 101 symlink (cần file của tác giả hoặc dựng lại từ dataset công khai,
ghi rõ là fixture mới); 13 test lỗi assertion; 6 test timeout cần máy
nhanh hơn. Benchmark mất phí vẫn không chạy.

## Phần chưa làm được và lý do (2026-11-11, trước khi push)

Chi tiết đầy đủ trong `results/2026-11-11-phan-chua-lam-duoc.md`.
Tóm tắt: (1) cassette livecodebench100 không sinh được vì 101 symlink
trỏ tới máy tác giả, file thật chưa từng có trong repo; (2) 13 test lỗi
assertion thật chưa sửa vì đó là lỗi nội dung của HELIX, sửa là việc
của upstream/fork, không phải của repo tái lập này; (3) 6 test timeout
chưa kết luận được vì VM chỉ có 1,5 CPU; (4) benchmark mất phí cố tình
không chạy vì cần API, ngân sách và bộ chạy chính thức; (5) đánh giá
held-out cho LoRA và build đầu tiên trên Builder chưa làm, vì 2 việc
đó thuộc mạch closed-loop/Builder trong fork HELIX, không thuộc repo
này.

## Sửa test 12/11 — phân loại lại 13 lỗi assertion + 6 timeout

Chi tiết đầy đủ trong `results/2026-11-12-test-fix-attempt.md`, log trong
`results/2026-11-12-npm-test-after-fix.txt` (song song) và
`results/2026-11-12-npm-test-sequential.txt` (tuần tự). Checkout thử nghiệm:
HELIX `a090aba` tại `~/workspace/helix-repro-clean-2026-11-11`, Node
v24.22.1, VM 1,5 CPU. Các sửa đổi chỉ nằm trên checkout thử nghiệm, chưa
commit vào HELIX upstream hay fork; file này là bản ghi, không phải code sửa.

- **Phân loại cũ sai.** Trong 13 "lỗi assertion" thì 8 cái thực ra là lỗi
  symlink ENOENT (chưa từng chạm tới assertion nào), chỉ còn 5 lỗi assertion
  thật — và cả 5 đã sửa xong trên checkout thử nghiệm:
  (1) `packages/external-tools/src/verifiers.ts` — verifier chỉ chấp nhận
  tên biến môi trường chữ hoa, trong khi chính `runner.ts` cho phép
  `http_proxy`/`https_proxy`/`all_proxy`/`no_proxy` chữ thường; sửa regex
  thành chấp nhận cả chữ thường; (2) test todo27 đòi file `TODO/TODO-027.md`
  vốn nằm trong `.gitignore` và chưa từng có trong git history; bỏ kỳ vọng
  đó, giữ 12 file bắt buộc còn lại.
- **6 timeout cũ thực ra là 7 timeout** trong full run mới — và cả 7 đều
  pass khi chạy riêng file (todo27 chỉ 26ms khi chạy riêng, 5084ms khi chạy
  song song). Chạy tuần tự `--no-file-parallelism`: **14 file fail / 94
  pass, 18 test fail / 816 pass, 0 timeout** — 18 fail còn lại toàn là lỗi
  symlink ENOENT. Kết luận: timeout là do 108 file test tranh nhau 1,5 CPU,
  không phải lỗi code; không tăng timeout để ép pass.
- **Full test sau sửa (song song): 18 file fail / 90 pass, 25 test fail /
  809 pass** (trước đó 19/89, 29/805). Trong 25 fail còn lại: 18 symlink +
  7 timeout, không còn lỗi assertion thật nào trong phạm vi này.
- **Còn lại:** 18 lỗi symlink ENOENT (101 symlink fixture trỏ tới máy tác
  giả) — ngoài phạm vi, cần file của tác giả hoặc dựng lại từ dữ liệu công
  khai. 2 sửa ở trên là lỗi thật của upstream (verifier quá chặt, test đòi
  file gitignored); nếu đưa lên upstream thì nên báo cho tác giả kèm bằng
  chứng, không sửa lặng.

Cập nhật cho mục "Phần chưa làm được" ở trên: điểm (2) "13 test lỗi
assertion thật chưa sửa" và (3) "6 test timeout chưa kết luận được" giờ đã
có đáp án như trên — chỉ còn gốc symlink là chưa đụng tới.

## Chạy lại live Vòng 1 + Vòng 2 — closed-loop (2026-11-12)

Phần này không thuộc mạch kiểm chứng offline ở trên; nó là công việc
closed-loop của nhóm, lưu trong cùng repo này tại `closed-loop/`. Số liệu
chính thức nằm ở trang đầu `README.md` và `closed-loop/REBUILD_REPORT.md`
(§8–§9), `closed-loop/data/analysis_round1.json`,
`closed-loop/data/analysis_round2.json`. Ghi lại ở đây để `RESULTS.md`
không còn dừng ở ngày 11/11.

- **Audit 12/11:** 80 trace BUILD tháng 10 trên fork chỉ có 9 live + 31
  dry-run mock (transcript rỗng, đáp án khớp bảng `_DRY_RUN_SOLUTIONS`);
  8/9 SFT và 8/8 đáp án chosen DPO lấy từ đáp án mẫu viết tay. Mọi số
  tháng 10 so với baseline BUILD đó (Minimal 30%→60%, Gap 60%→10%,
  Pi/Hermes/OpenCode 90%→70%, độ trễ tăng) đã bị rút lại. Chi tiết:
  `results/2026-11-12-closed-loop-trace-audit.md`,
  `closed-loop/PROVENANCE_AUDIT.md`.
- **Vòng 1 (12/11, 160 trace live, 10 bài train + 10 bài held-out v1):**
  BUILD 28/40 → REBUILD 31/40; held-out v1 base 39/40 → LoRA 40/40
  (1 ô base trượt là lỗi hạ tầng HTTP 400, không phải lời giải sai; bộ bài
  bị trần). McNemar BUILD→REBUILD p = 0,375. Train live-only: 8 SFT + 2
  DPO. Tất cả 160 cờ `passed` re-verify độc lập: 0 sai lệch. Commit
  `f84a03a`, `4f595ea`, `bf6fdfc`.
- **Vòng 2 (12/11, 360 trace live, 20 bài train + 15 bài held-out v2 khó
  hơn):** BUILD2 60/80 → REBUILD2 66/80; held-out v2 base 50/60 → LoRA
  53/60. McNemar p = 0,0703 (train) và p = 0,4531 (held-out) — gợi ý
  nhưng chưa đạt ý nghĩa thống kê 0,05; **chưa chứng minh được khái quát
  hóa**, LoRA không tụt trên bài mới. 0 lỗi hạ tầng (đã sửa tràn context
  4096 → 8192). Train: 19 SFT + 6 DPO (gồm sampling nhiệt độ 0,7).
  Tất cả 360 cờ `passed` re-verify độc lập: 0 sai lệch. Commit
  `43758ed`, `407c8d8`, `ffb49ab`.
- **Điểm tự chấm so với paper: 7,6/10** (nhóm tự chấm theo 5 tiêu chí,
  không phải điểm môn học; Kaggle chưa tính vì chưa có link/notebook).
  Chi phí Modal là ước tính: vòng 1 ~$2–2,50; vòng 2 ~$4,30.
- **Trọng số adapter LoRA** chỉ nằm trên Modal volume, không commit trong
  repo; repo chỉ giữ metadata, loss history và hash dữ liệu train trong
  `closed-loop/data/training_runs/`.
