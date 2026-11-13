# Thực nghiệm HELIX — Model–Harness Co-evolution ở quy mô nhỏ

Repository này ghi lại toàn bộ công việc thực nghiệm của Nhóm 19 cho bài báo
HELIX: kiểm chứng offline framework của tác giả, audit nguồn gốc dữ liệu của
nhóm, hai vòng chạy live pipeline closed-loop (Build → Update → Rebuild)
trên Modal với model `Qwen/Qwen2.5-Coder-7B-Instruct`, và một smoke test
ghép adapter đã train với harness lắp thật. Mọi trace, dataset, log train
và báo cáo phân tích đều nằm trong repository này; số liệu nào chưa chứng
minh được thì ghi rõ là chưa chứng minh được, phần nào chưa làm được thì
ghi rõ là chưa làm được.

Nhóm thực hiện: Nhóm 19, môn Khai phá dữ liệu / Cơ sở
hệ thống thông tin, VNU-UET, học kỳ I năm học 2026–2027. Giảng viên hướng
dẫn môn học: PGS.TS Hà Quang Thụy.

## Hướng dẫn đọc nhanh

Thầy đọc theo thứ tự sau là đủ nắm toàn bộ công việc:

1. **File này (README.md)** — tóm tắt kết quả, caveat và cách chạy lại.
2. [`REPORT.md`](./REPORT.md) — báo cáo đối chiếu: từng hạng mục của tác
   giả đối chiếu với kết quả kiểm chứng offline của nhóm.
3. [`RESULTS.md`](./RESULTS.md) — nhật ký kết quả theo ngày (07–12/11/2026),
   gồm cả phần phân loại lại lỗi test ngày 12/11 và tóm tắt hai vòng live.
4. [`closed-loop/REBUILD_REPORT.md`](./closed-loop/REBUILD_REPORT.md) §8–§9
   — phân tích thống kê đầy đủ của hai vòng chạy live (union, khoảng tin
   cậy Wilson, kiểm định McNemar).
5. [`results/`](./results/) — log và bằng chứng gốc (xem
   [`results/README.md`](./results/README.md) để biết file nào là gì),
   gồm audit nguồn gốc trace và bằng chứng smoke test harness thật.

## Bài báo và các repository liên quan

- **Bài báo:** HELIX: *Model–Harness Co-evolution for Recursive
  Self-Improvement*, Tianyu Fan & Chao Huang (In3 Lab, Đại học Hong Kong),
  arXiv:2608.13951 v1, 14/08/2026, preprint chưa peer-review.
  https://arxiv.org/abs/2608.13951
- **Code gốc của tác giả:** https://github.com/HKUDS/HELIX
- **Fork của nhóm** (pipeline closed-loop chính thức):
  https://github.com/Vietng-XPrince7/HELIX (HEAD `cc44b7b`)
- **Repository này:** kiểm chứng offline + bản sao working copy của
  `closed-loop/` kèm các bản sửa provenance, dữ liệu và trace của hai vòng
  chạy live, và bằng chứng smoke test harness thật. Fork vẫn là pipeline
  chính thức của nhóm; các cải tiến ở đây được port ngược về fork bằng
  patch (xem mục
  [Bản sao pipeline closed-loop](#bản-sao-pipeline-closed-loop)).

Tác giả làm 65 harness ứng viên × 100 bài (6.500 lượt chạy) và rút ra 438
sibling record từ 200 slot, nhưng **không train model mới** (paper §9.5):
phần train LoRA của nhóm đi xa hơn paper ở đúng một trục này, ở quy mô nhỏ.

## Kết quả chính

### Phát hiện audit (12/11/2026)

Kiểm tra offline 80 trace đã commit trong fork cho thấy BUILD tháng 10 chỉ có
**9 live + 31 dry-run mock** (không phải "40 live runs" như commit message
đã ghi); **8/9 record SFT và 8/8 `chosen` DPO lấy từ code viết tay trong
trace mock**. Cờ `passed` và số học trong báo cáo cũ đều đúng khi chạy lại
sandbox (0 lệch), nhưng nguồn gốc dữ liệu train và việc REBUILD đánh giá
đúng 10 bài đã train làm cho kết luận cũ không đứng được. Chi tiết:
[results/2026-11-12-closed-loop-trace-audit.md](./results/2026-11-12-closed-loop-trace-audit.md)
và [closed-loop/PROVENANCE_AUDIT.md](./closed-loop/PROVENANCE_AUDIT.md).

### Vòng 1 — chạy lại live toàn bộ (12/11/2026)

BUILD live 40/40 trên model gốc, trích xuất live-only, train lại, REBUILD
live 40/40 trên adapter mới, và held-out 80/80 trên 10 bài mới. Tất cả 160
cờ `passed` được re-verify độc lập: **0 sai lệch**.

| Harness | BUILD (base) | REBUILD (LoRA) |
| --- | --- | --- |
| Minimal | 6/10 | 7/10 |
| Pi Mono | 7/10 | 8/10 |
| Hermes Agent | 7/10 | 7/10 |
| OpenCode | 8/10 | 9/10 |
| **Tổng** | **28/40** | **31/40** |

Train: 8 SFT + 2 DPO, SFT 3 bước (loss 1,03 → 0,95), DPO 3 bước (loss
0,693 → 0,683). Chênh lệch +3/40 phù hợp với nhiễu mẫu (McNemar p = 0,375;
gain rơi vào bài không có trong dữ liệu train, loss rơi vào bài có trong
DPO). Held-out v1: base 39/40 (1 ô là lỗi hạ tầng HTTP 400, không phải sai
lời giải) so với LoRA 40/40 — bộ bài bị trần (ceiling effect), **không
chứng minh được khái quát hóa**. Union (ít nhất một harness giải được):
BUILD 8/10 → REBUILD 10/10.

Commit: [f84a03a](https://github.com/letrieu728/thucnghiemhelix/commit/f84a03a2a0dce403b1c43a2cbe1fc883fd7768f5)
(trace BUILD + REBUILD),
[4f595ea](https://github.com/letrieu728/thucnghiemhelix/commit/4f595ea2fbe41fbc49b51d62581f687c935af74b)
(trace held-out),
[bf6fdfc](https://github.com/letrieu728/thucnghiemhelix/commit/bf6fdfc147b05e5cd65c1b4fea623513aa8766ca)
(code, test, báo cáo).

### Vòng 2 — tập train mở rộng + sampling (12/11/2026)

20 bài train (thêm 10 bài mới) + sampling ở nhiệt độ 0,7 cho 2 harness
Minimal/OpenCode; held-out v2 gồm 15 bài khó mới, test chặt hơn. 360 trace
live, **0 lỗi hạ tầng** (đã sửa tràn context 4096 → 8192 và giới hạn vòng
feedback 4 bước). Tất cả 360 cờ `passed` được re-verify độc lập: **0 sai
lệch**. Kiểm tra rò rỉ: không ID held-out nào lọt vào dữ liệu train.

| Harness | BUILD2 (base) | REBUILD2 (LoRA) |
| --- | --- | --- |
| Minimal | 14/20 | 17/20 |
| Pi Mono | 15/20 | 16/20 |
| Hermes Agent | 14/20 | 15/20 |
| OpenCode | 17/20 | 18/20 |
| **Tổng** | **60/80 (75,0%, Wilson 95%: 64,5–83,2%)** | **66/80 (82,5%, Wilson 95%: 72,7–89,3%)** |

Train: 19 SFT + 6 DPO (sampling tạo thêm dữ liệu cho 4 bài chỉ có contrast
nhờ sampling), SFT 9 bước (loss 1,00 → 0,49), DPO 3 bước (loss 0,693 →
0,660). McNemar: 7 thắng / 1 thua, **p = 0,0703 — gợi ý nhưng chưa đạt mức
ý nghĩa 0,05**.

| Held-out v2 (15 bài mới) | Base | LoRA |
| --- | --- | --- |
| Minimal | 12/15 | 13/15 |
| Pi Mono | 13/15 | 13/15 |
| Hermes Agent | 13/15 | 13/15 |
| OpenCode | 12/15 | 14/15 |
| **Tổng** | **50/60 (83,3%, Wilson 95%: 72,0–90,7%)** | **53/60 (88,3%, Wilson 95%: 77,8–94,2%)** |

McNemar held-out v2: 5 thắng / 2 thua, **p = 0,4531 — không có ý nghĩa
thống kê, không chứng minh được khái quát hóa**, nhưng cũng không thoái hóa
trên bài mới. Union: tập train 17/20 → 19/20; held-out 14/15 ở cả hai
model (bài `held2_009_next_permutation` cả hai model đều trượt cả 4
harness). Phân tích đầy đủ:
[closed-loop/REBUILD_REPORT.md](./closed-loop/REBUILD_REPORT.md) (§8–§9),
[closed-loop/data/analysis_round1.json](./closed-loop/data/analysis_round1.json),
[closed-loop/data/analysis_round2.json](./closed-loop/data/analysis_round2.json),
[closed-loop/ROUND2_DESIGN.md](./closed-loop/ROUND2_DESIGN.md).

Commit: [43758ed](https://github.com/letrieu728/thucnghiemhelix/commit/43758ed272b1cb108d0fe18309aa6b19ab6497fd)
(code, báo cáo, dataset, train run),
[407c8d8](https://github.com/letrieu728/thucnghiemhelix/commit/407c8d8d791a5b09e5dbd86acbfa866cb936a296)
(240 trace BUILD2 + REBUILD2),
[ffb49ab](https://github.com/letrieu728/thucnghiemhelix/commit/ffb49ab69b7361da4ac10f6ea2d4ae7a24d85702)
(120 trace held-out v2).

### Smoke test: ghép LoRA với harness lắp thật (12/11/2026, tối)

Sau hai vòng chạy qua harness mô phỏng, nhóm thử ghép adapter LoRA vòng 2
với một harness lắp thật bằng CLI của tác giả: 1 bài sửa lỗi Python nhỏ,
harness pi-mono (297 module, 4 tool thật), model `helix-lora` qua endpoint
vLLM trên Modal. Kế hoạch gốc dùng `minimal`, nhưng `minimal` không phải
product chạy được bằng lệnh `run` của CLI nên buộc phải dùng pi-mono.

**Kết luận: chưa ghép được.** Cả 4 tiêu chí cam kết trước đều FAIL. Harness
assemble thành công và chạy tới bước gọi model, nhưng request chết ở 2
blocker độc lập, cả hai đều đã chẩn đoán rõ bằng probe trực tiếp:

1. **Proxy + streaming:** CLI bắt buộc `stream: true`; server vLLM trả 200
   nhưng response không qua được proxy FastAPI tới CLI (CLI nhận 502 rỗng,
   3/3 lần). Chạy không streaming thì vẫn 200 bình thường.
2. **Định dạng tool call:** cả model gốc lẫn LoRA đều sinh tool call dạng
   XML `<function_call>`, parser Hermes không nhận ra (`tool_calls: []`),
   nên tool không bao giờ được thực thi. Đây không phải lỗi do LoRA —
   model gốc cũng sinh y hệt.

Muốn ghép được cần 2 lần sửa ngoài scope smoke test: sửa proxy để stream
đúng chuẩn, và sửa định dạng tool call của model. Chi phí GPU ước tính
~$0,2–0,4 từ credit (dưới trần $2 đã duyệt); app Modal đã tắt ngay sau khi
chạy. Toàn bộ bằng chứng (đề bài, probe, output CLI, log deploy, bản sao
script có parser):
[results/2026-11-12-real-harness-smoke-test/](./results/2026-11-12-real-harness-smoke-test/),
commit
[baee74f](https://github.com/letrieu728/thucnghiemhelix/commit/baee74ff15fc156bd1fda3b5016eda42bfb1f1b7).

### Đọc kết quả thế nào

- Hai vòng chạy đều cho gain nhỏ, cùng chiều, nhưng **chưa vòng nào đạt ý
  nghĩa thống kê** — báo cáo của nhóm không tuyên bố model đã học được kỹ
  năng chung, chỉ tuyên bố vòng lặp chạy được đầu-cuối, dữ liệu có nguồn
  gốc rõ ràng, và adapter không thoái hóa trên bài mới.
- Trọng số adapter LoRA chỉ nằm trên Modal volume, không commit trong repo
  này; repo chỉ giữ metadata, loss history và hash dữ liệu của từng run
  train trong `closed-loop/data/training_runs/`.

## Cấu trúc repository

```text
.
├── README.md / REPORT.md / RESULTS.md   # Mặt tiền, báo cáo đối chiếu, log kết quả
├── LICENSE                              # MIT
├── closed-loop/                         # Working copy pipeline + dữ liệu 2 vòng live
│   ├── README.md                        # Hướng dẫn pipeline (từ fork)
│   ├── REBUILD_REPORT.md                # Báo cáo BUILD vs REBUILD, §8–§9 là thống kê 2 vòng
│   ├── PROVENANCE_AUDIT.md              # Audit nguồn gốc trace + các lỗi đã sửa
│   ├── HELDOUT_RUNBOOK.md               # Quy trình chạy live, train lại, đánh giá held-out
│   ├── ROUND2_DESIGN.md                 # Thiết kế vòng 2 (bài mới, sampling, ngân sách)
│   ├── LORA_VALIDATION.md               # Ghi chú kiểm tra adapter
│   ├── scripts/
│   │   ├── 01_modal_vllm.py             # vLLM OpenAI-compatible server trên Modal
│   │   ├── 02_run_helix_eval.py         # Runner đánh giá 4 harness (live + dry-run + sampling)
│   │   ├── 03_extract_pairs.py          # Trích xuất SFT/DPO, chỉ lấy trace live, ghi provenance.json
│   │   └── 04_train_lora.py             # Train LoRA SFT + DPO (Unsloth/QLoRA) trên Modal A100
│   ├── configs/                         # harnesses.json, lora_config.yaml
│   ├── data/
│   │   ├── heldout_problems.json        # 10 bài held-out v1 (held_001–010)
│   │   ├── heldout2_problems.json       # 15 bài held-out v2 (held2_001–015)
│   │   ├── train_extra_problems.json    # 10 bài train bổ sung vòng 2 (lcb_011–020)
│   │   ├── analysis_round1.json / analysis_round2.json
│   │   ├── rebuild_comparison_plot.svg / round2_comparison_plot.svg
│   │   ├── processed/                   # Dataset SFT/DPO hiện tại (vòng 2) + provenance.json
│   │   ├── raw_traces/                  # 520 trace JSON (vòng 1: 160, vòng 2: 360)
│   │   └── training_runs/               # metadata + loss history 2 run train
│   ├── notebooks/                       # evaluate_rebuild.py, round1_stats.py, round2_stats.py
│   ├── tests/test_pipeline.py           # 17 test (pipeline, provenance gate, drift config)
│   ├── requirements.txt / .env.template
├── results/                             # Log và bằng chứng kiểm chứng offline + audit
│   ├── README.md                        # Mục lục thư mục results/
│   ├── 2026-11-12-real-harness-smoke-test/  # Bằng chứng smoke test harness thật
│   └── 2026-11-11-fixed-artifacts/      # Artifact tái sinh 11/11 (3 FAIL gốc → PASS)
└── scripts/
    ├── run-offline.ps1                  # Chạy các lệnh verify offline của HELIX
    └── check_fixture_symlinks.py        # Kiểm tra 101 fixture symlink
```

Lưu ý: `closed-loop/data/processed/` hiện giữ dataset vòng 2; dataset vòng 1
(8 SFT + 2 DPO) xem lại ở commit
[bf6fdfc](https://github.com/letrieu728/thucnghiemhelix/commit/bf6fdfc147b05e5cd65c1b4fea623513aa8766ca).

## Bản sao pipeline closed-loop

Toàn bộ `closed-loop/` của fork (commit `cc44b7b`
cộng các bản sửa provenance 12/11) được sao vào `closed-loop/` của repo này
làm working copy
([3dc216d](https://github.com/letrieu728/thucnghiemhelix/commit/3dc216d70e71df5d471bb7ee619c7b548a2e3154)),
kèm các cải tiến train chỉ có ở bản sao này:

- `03_extract_pairs.py` ghi thêm `data/processed/provenance.json` (số lượng,
  trace nguồn, SHA-256 của 2 file dữ liệu) mỗi lần trích xuất.
- `04_train_lora.py` từ chối train nếu thiếu manifest, manifest nhận dữ
  liệu dry-run, hoặc số lượng/hash không còn khớp file; dữ liệu legacy bị
  chặn mặc định, chỉ mở bằng `--allow-unverified-data` khi chủ đích xác
  nhận; lệch số lượng/hash thì luôn chặn.
- Mỗi run train ghi `metadata.json` đầy đủ (siêu tham số, seed, hash dữ
  liệu, tóm tắt provenance, step/loss cuối từng stage, phiên bản thư viện)
  và entrypoint tải về cả `metadata.json` + `versions.json`.
- `seed` thành tham số (mặc định 42); `lora_config.yaml` đã đồng bộ lại
  đúng default của script (bản cũ lệch logging/save strategy/DPO epochs và
  toàn bộ mục storage), có test chặn lệch trong tương lai.
- Ảnh PNG của biểu đồ không commit trong repo; bản SVG nằm ở
  `closed-loop/data/`; chạy `notebooks/evaluate_rebuild.py` để vẽ lại.

Cải tiến ở bản sao này cần port
ngược về fork bằng patch, không sửa song song hai nơi. Việc push trực tiếp
lên fork bị chặn (GitHub App 403), nên các bản sửa được gói thành file patch
do nhóm giữ và áp bằng tay; patch không commit trong repo này.

## Cách chạy lại

### Test offline (không cần GPU hay Modal)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r closed-loop/requirements.txt   # test cần tối thiểu gói modal và pyyaml
cd closed-loop
python -m unittest discover -s tests
```

17/17 test phải pass. Test bao gồm: pipeline trích xuất/train, provenance
gate (chặn dữ liệu dry-run và held-out lọt vào train), và test chặn lệch
`lora_config.yaml`.

### Chạy live (cần tài khoản Modal)

Làm theo [closed-loop/HELDOUT_RUNBOOK.md](./closed-loop/HELDOUT_RUNBOOK.md)
và [closed-loop/ROUND2_DESIGN.md](./closed-loop/ROUND2_DESIGN.md): deploy
endpoint vLLM bằng `01_modal_vllm.py`, chạy đánh giá bằng
`02_run_helix_eval.py`, trích xuất bằng `03_extract_pairs.py`, train bằng
`04_train_lora.py`. Cần xác thực Modal (`modal token new`) và điền endpoint
vào file `.env` từ mẫu `closed-loop/.env.template`. **Không có secret hay
token nào được commit trong repo này.**

## Kiểm chứng offline

Kiểm chứng offline được thực hiện từ 07–11/11/2026.
Báo cáo đối chiếu đầy đủ nằm tại [`REPORT.md`](./REPORT.md); log kết quả
từng ngày nằm tại [`RESULTS.md`](./RESULTS.md) và thư mục
[`results/`](./results/).

Repository này tái lập các kiểm tra **offline, miễn phí và có thể chạy
lại** của HELIX. Mục tiêu là đánh giá kỹ thuật của framework, không tuyên
bố tái lập kết quả benchmark dùng LLM trả phí.

### Phạm vi đã thực hiện

| Thực nghiệm | Mục tiêu | Lệnh | Kết quả |
| --- | --- | --- | --- |
| Typecheck | Kiểm tra tính nhất quán kiểu của workspace | `npm run typecheck` | Xem `results/2026-11-07-typecheck.md` |
| Unit & conformance tests (tuỳ chọn) | Kiểm tra hồi quy và các hợp đồng module | `./scripts/run-offline.ps1 -IncludeFullTest` | Xem `results/2026-11-11-npm-test.txt` và `results/2026-11-12-npm-test-after-fix.txt` |
| Task parity (cassette) | So sánh assembled/original-contract trong chế độ xác định | Không tự chạy trong script | Có thể ghi đè artifact upstream |
| Cadence verification | Kiểm tra tái lập cadence artifact | `npm run task:parity:cadence:verify` | Xem `results/2026-11-11-task-parity-cadence-verify.txt` |
| Assembly verification | Kiểm tra recipe/assembly contract | `npm run assembly:contract:verify` | Xem `results/2026-11-11-linux-verification.md`; log thô nén tại `results/2026-11-11-assembly-contract-verify.txt.gz.b64` (xem `results/2026-11-11-large-files-gz-note.md`) |

Các lệnh được chạy từ bản HELIX cục bộ. Mặc định script giả định cấu trúc
thư mục:

```text
HELIX-main (2)/
├── HELIX-git/          # source HELIX, đã npm install
└── thucnghiemhelix/    # repository này
```

Mở PowerShell tại repository này và chạy:

```powershell
./scripts/run-offline.ps1
```

Hoặc truyền đường dẫn HELIX khác:

```powershell
./scripts/run-offline.ps1 -HelixDir 'D:\du-an\HELIX'
```

Script không dùng API key, không gửi dữ liệu ra ngoài và không gọi model. Nó
chỉ chạy các lệnh verify/read-only và lưu log cho từng lệnh vào `results/`.
Thêm `-IncludeFullTest` khi muốn chạy toàn bộ test suite.

### Cách diễn giải

Các thí nghiệm trên chứng minh rằng source hiện tại biên dịch, test được, và
các artifact/contract offline nhất quán. Chúng **không** chứng minh HELIX tốt
hơn các agent khác trên benchmark thực tế, vì không có lần gọi model thật.

`task:parity` ở đây dùng fixture/cassette hoặc original-contract replay khi
không bật `--native-original`; vì vậy đây là bằng chứng về khả năng tái lập
cấu trúc và hành vi đã ghi nhận, không phải native end-to-end parity.

### Trạng thái tái lập đã xác nhận

Kết quả được lưu trong thư mục `results/` và được version hóa khi có kết luận
rõ ràng. Lần rà soát ngày 2026-11-10 phân biệt giữa **đã chạy thành công**,
**đã thử nhưng không kết luận**, và **chưa chạy**; không suy diễn kết quả từ
artifact có sẵn trong HELIX thành một lần tái lập mới.

| Hạng mục trong HELIX | Trạng thái tái lập | Ghi chú |
| --- | --- | --- |
| Typecheck | PASS (2026-11-07) | Xem `results/2026-11-07-typecheck.md`; chạy tại commit `a090aba`. |
| Full unit/conformance tests | Không kết luận | Đã chạy trên working tree có thay đổi cục bộ; log thô không được dùng làm kết quả xác nhận. |
| Sinh cassette task parity | BLOCKED (2026-11-11) | 101 fixture symlink trỏ tới đường dẫn tuyệt đối trên máy tác giả, 101/101 hỏng (`ENOENT` trên Linux); nội dung 101 task không có trong repo, không tạo fixture giả. |
| Assembly contract | PASS (2026-11-10) | Strict verification hoàn thành trên cả 5 product. |
| Flow graphs | PASS (2026-11-10) | Cả 9 artifact blueprint/comparison hiện có đều verify được. |
| Executable audit | PASS (2026-11-10) | Fingerprint `44370eff3ea1ca3a`; không có compile blocker. |
| TODO-27 inventory & OpenCode acceptance | PASS (2026-11-10) | Hai verifier PASS; acceptance vẫn chỉ là `ready-for-review`, không phải TODO hoàn tất. |
| Task parity & cadence | FAIL gốc / PASS tái sinh (2026-11-11) | Artifact gốc thiếu metadata acceptance-timing drift; artifact tái sinh trên 12 task smoke verify PASS 13/13. |
| Split task parity | FAIL gốc / PASS tái sinh (2026-11-11) | Manifest gốc lệch hash/kích thước; manifest tái sinh verify PASS 403/403. |
| Current-module audit | FAIL gốc / PASS tái sinh (2026-11-11) | Artifact gốc `ce386…` ≠ tính lại `413e…`; artifact tái sinh verify PASS. |
| Live provider/native CLI/LCB/SWE-bench | Không thực hiện | Cần model/credential hoặc dữ liệu và runner không có trong checkout. |

### Các phần chưa làm được và lý do

| Hạng mục | Lý do chưa chạy | Điều kiện để chạy |
| --- | --- | --- |
| Live provider parity | Cần API credential của provider | API key OpenRouter/OpenAI-compatible/Anthropic/Google và ngân sách token |
| Native upstream CLI parity | `--native-original` gọi upstream CLI kèm model thật | Credentials, internet, và chi phí inference |
| LiveCodeBench/SWE-bench Pass@1 | Cần thực thi agent trên benchmark với model | Model API hoặc GPU/local model, dữ liệu benchmark, thời gian chạy |
| Full search / Pass@N | Mỗi task thử nhiều recipe/candidate | Ngân sách inference lớn và quy tắc budget-matched với baseline |
| So sánh đa seed, đa model | Cần lặp lại nhiều lần inference | API/GPU và một protocol thống kê định trước |
| Robustness đa provider | Cần endpoint/provider thật để tiêm lỗi mạng/tool | Credentials hoặc hạ tầng provider local tương thích |

Ghi chú thêm (12/11): nhóm đã thử 1 lượt live provider qua endpoint
OpenAI-compatible tự dựng (smoke test ghép LoRA với harness lắp thật, xem
mục trên); lượt thử bị chặn ở tầng proxy streaming và định dạng tool call,
chưa kết luận được parity. Bằng chứng tại
[results/2026-11-12-real-harness-smoke-test/](./results/2026-11-12-real-harness-smoke-test/).

### Ghi chú về giới hạn môi trường

Khi chạy trong sandbox, `tsx` gọi `node:os.userInfo()` và dừng với
`uv_os_get_passwd returned ENOMEM`. Chạy cùng các lệnh ngoài sandbox bằng Node
của tài khoản người dùng hoạt động bình thường; kết quả thực tế được ghi trong
`results/2026-11-10-offline-verification.md`.

## Hạn chế cần nêu trong báo cáo

1. 4 "harness" trong pipeline closed-loop là mô phỏng bằng system prompt +
   vòng lặp chat, không phải harness HELIX đã assemble qua Builder/CLI.
2. Các bài đánh giá là bài tự viết, gắn nhãn `lcb_*`/`held_*`, không phải
   bài LiveCodeBench hay AtCoder thật.
3. Cỡ mẫu nhỏ (10–20 bài train, 10–15 bài held-out); gain chưa đạt ý nghĩa
   thống kê ở vòng nào.
4. Kết quả offline không được suy diễn thành chất lượng giải benchmark.
5. Điểm "Full search" kiểu Pass@N không so sánh trực tiếp được với Pass@1
   của một harness cố định nếu không cùng ngân sách rollout/token.
6. Artifact live trong upstream chỉ là ảnh chụp ở thời điểm tạo; phiên bản
   upstream/model có thể đã thay đổi.
7. Bằng chứng native của các product không đồng đều; một số kiểm tra là
   fixture hoặc metadata guard thay vì quan sát native end-to-end.
8. 101 fixture symlink của tác giả vẫn hỏng; patch port ngược về fork vẫn
   đang chờ áp; bản chạy kiểm chứng trên Kaggle chưa được đưa vào đánh giá.
9. Việc ghép adapter đã train với harness lắp thật mới dừng ở smoke test
   1 task và **chưa thành công** (blocker proxy streaming và định dạng
   tool call, xem mục smoke test ở trên); mọi kết quả BUILD/REBUILD trong
   repo này đều qua harness mô phỏng, không phải harness lắp thật.

## Nguồn và khả năng tái lập

- Source HELIX cục bộ dùng cho kiểm chứng offline: `../HELIX-git/`
- Phiên bản Node/npm, commit và thời gian chạy được ghi ở đầu mỗi log trong
  `results/`.

## Credits

- **Lê Quốc Triệu** — K69 Hệ thống thông tin, MSSV 24022750
  ([letrieu728](https://github.com/letrieu728)): đọc hiểu paper, phân tích
  kết quả, viết và thuyết trình báo cáo, đồng huấn luyện LoRA cùng bạn.
- **Nguyễn Sỹ Việt** — MSSV 24022758
  ([Vietng-XPrince7](https://github.com/Vietng-XPrince7)): pipeline
  closed-loop, hạ tầng Modal/vLLM, đồng huấn luyện LoRA.
- Giảng viên hướng dẫn môn học: **PGS.TS Hà Quang Thụy**, VNU-UET.
- Thực hiện tháng 11/2026.

## License

MIT — xem [LICENSE](./LICENSE). Phần code lấy từ fork của nhóm và upstream
HELIX giữ nguyên license MIT của tác giả gốc.
