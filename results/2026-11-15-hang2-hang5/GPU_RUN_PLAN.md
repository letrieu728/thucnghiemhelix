# Kế hoạch chạy GPU — đợt bổ sung hàng 2+5 (HELIX)

Dành cho worker GPU tiếp theo. Đợt này gọi là **"đợt bổ sung hàng 2+5"**,
KHÔNG gọi là vòng 3. Mọi file chuẩn bị đã có sẵn trong thư mục này
(`RUBRIC.md`, `DPO_RULES.md`, `dpo_pairs_expanded.jsonl`,
`dpo_extraction_audit.json`, `JUDGE_PROMPT.md`, `judge_list.json`,
`heuristic_labels.*`, `HEURISTIC_NOTES.md`). Worker GPU KHÔNG viết lại
luật, KHÔNG sửa prompt judge, KHÔNG trích lại DPO.

Ngân sách: **tổng dưới $8**, ước tính $6.70 theo giá A100 $2.50/giờ
(xem §6). Modal không cho đọc số dư qua CLI nên chi phí được kiểm soát
bằng ước tính từ latency đã ghi + hệ số an toàn 1.15 (quy ước của
`ROUND2_DESIGN.md` §3), với checkpoint dừng cứng ở §7.

## 1. Config train đề xuất (thay đổi tối thiểu so với vòng 2)

Vòng 2 dùng (`configs/lora_config.yaml` mirror đúng default của
`04_train_lora.py`; metadata train `20261112T082610-f368cbfe` xác nhận):
epochs 3 (chung cho SFT+DPO), SFT lr 2e-4, DPO lr 5e-6, beta 0.1
(hardcode trong script, KHÔNG có cờ CLI), r=16, alpha=32, dropout 0.05,
seed 42, max_seq 4096, effective batch SFT 8 (2×4) / DPO 8 (1×8).
Kết quả vòng 2: SFT 9 bước, loss 1.00→0.49; DPO 3 bước, loss 0.693→0.660
(gần như không học; reward accuracy chỉ đạt 1.0 ở bước cuối cùng).

| Tham số | Vòng 2 | Đợt bổ sung | Thay đổi? |
|---|---|---|---|
| SFT records | 19 | 19 (cùng file, cùng hash `4f4d6ad8…`) | Không |
| DPO pairs | 6 | **19** (`dpo_pairs_expanded.jsonl`, SHA-256 `47b8e075…`) | **Duy nhất** |
| Epochs (chung) | 3 | 3 | Không |
| SFT lr / DPO lr | 2e-4 / 5e-6 | 2e-4 / 5e-6 | Không |
| Beta (DPO) | 0.1 | 0.1 | Không |
| r / alpha / dropout / seed | 16 / 32 / 0.05 / 42 | 16 / 32 / 0.05 / 42 | Không |
| Bước kỳ vọng | SFT 9, DPO 3 | **SFT 9, DPO 9** | Hệ quả của 19 cặp |

Số bước DPO kỳ vọng: ceil(19/8) = 3 bước/epoch × 3 epochs = 9 bước
(vòng 2: ceil(6/8) = 1 × 3 = 3). SFT không đổi vì dữ liệu không đổi.

**Lý do giữ nguyên mọi siêu tham số:** biến duy nhất của đợt bổ sung là
số cặp DPO (6→19). DPO vòng 2 dừng đúng lúc tín hiệu vừa xuất hiện (3
bước), nên tăng số bước ở cùng LR là sửa chữa tối thiểu đúng chỗ. Đổi LR
hay beta sẽ làm nhiễu (confound) — không biết cải thiện (nếu có) đến từ
dữ liệu hay từ siêu tham số. Hai phương án khác đã loại trừ có lý do:
(a) tăng riêng epochs DPO là không thể qua CLI (cờ `--epochs` chung cho
cả hai stage; tăng chung sẽ nhân ba bước SFT trên 19 mẫu → nguy cơ
overfit); (b) đổi beta cần sửa code `04` + re-verify test khớp config —
vượt phạm vi "thay đổi tối thiểu" và không cần thiết khi ràng buộc thực
sự là số bước.

Lệnh train (default của script đã là đúng config — không truyền thêm cờ
nào ngoài stage/epochs):

```bash
modal run closed-loop/scripts/04_train_lora.py --stage sft_then_dpo --epochs 3
```

Chạy từ repo root `thucnghiemhelix/`, bằng Modal CLI trong
`~/workspace/modal-venv` (xem `~/TOOLS.md`: cần extra
`api-proxy-support`). Ghi lại run id + toàn bộ loss history; nếu số bước
DPO thực tế khác 9 thì ghi nhận và điều tra, không train lại lặng lẽ.

## 2. Đường dẫn adapter (KHÔNG ghi đè adapter vòng 2)

Trạng thái volume `helix-adapters` (`/vol/checkpoints`):

| Đường dẫn | Nội dung | Quy tắc |
|---|---|---|
| `helix-lora-final` | Adapter VÒNG 2 (đang phục vụ) | Sao lưu trước khi train; train sẽ ghi đè; khôi phục sau khi đo xong (§4 bước 10) |
| `helix-lora-final-backup-20261112` | Adapter VÒNG 1 | **KHÔNG ĐỘNG TỚI** dưới bất kỳ hình thức nào |
| `helix-lora-final-backup-20261104` | Adapter cũ hơn | **KHÔNG ĐỘNG TỚI** |
| `helix-lora-final-round2-20261112` (MỚI) | Bản sao adapter vòng 2 | Tạo ở bước 1, verify trước khi train |
| `helix-lora-supplement-20261115` (MỚI) | Adapter đợt bổ sung | Tạo ở bước 6, ngay sau khi train xong |
| `runs/<run-id>/` | Adapter SFT + metadata của đợt train mới | Do `04` tạo; không xóa |

Script `04` hardcode `final_adapter_dir = /vol/checkpoints/helix-lora-final`
và không có cờ đổi đường dẫn — yêu cầu "đường dẫn riêng" được thỏa mãn
bằng quy trình sao lưu + sao chép ở §4, không bằng cờ lệnh. Mọi lần sao
chép đều phải verify số file + kích thước khớp nguồn trước khi tiếp tục;
ghi số file/kích thước vào báo cáo (bản sao lưu vòng 1 có 12 file theo
audit — KHÔNG giả định vòng 2 cũng 12 file, phải đếm thật).

Endpoint `01_modal_vllm.py` load đúng `helix-lora-final` dưới alias
`helix-lora` khi khởi động (`--lora-modules helix-lora=/adapters/helix-lora-final`,
`--max-loras 2`, `--max-lora-rank 64`, `--max-model-len 8192`); server
đang chạy không tự load adapter mới — bắt buộc redeploy sau khi train
(bước 7). Routing theo model id của request (base id → base weights,
`helix-lora` → adapter); quy tắc rewrite proxy cũ đã bị xóa ở working
copy — verify routing ở cả hai lần deploy (bước 2 và 7) bằng cách gọi
một completion với mỗi model id và ghi lại model id trả về.

## 3. Staging dữ liệu train (cổng provenance — không bypass)

Script `04` từ chối train nếu `data/processed/provenance.json` thiếu,
thừa nhận dry-run, hoặc counts/hash không khớp file. Quy trình staging
(nên làm TRƯỚC khi deploy lần đầu để lỗi staging không đốt GPU):

1. Sao lưu 3 file hiện tại của `data/processed/` (`sft_data.jsonl`,
   `dpo_pairs.jsonl`, `provenance.json`) sang thư mục mới
   `results/2026-11-15-hang2-hang5/staging-backup/`; verify hash sau
   khi sao lưu (SFT phải là `4f4d6ad8b63c…`, DPO cũ `a40fa5b1f1b3…`).
2. Chép `dpo_pairs_expanded.jsonl` (thư mục này) đè lên
   `data/processed/dpo_pairs.jsonl`; verify SHA-256 sau khi chép =
   `47b8e0756876a3d627f73ffa6776d19f2011c2d1c26a4894406a5fd0216af19c`.
   File SFT KHÔNG được động tới (verify hash vẫn `4f4d6ad8…`).
3. Viết lại `data/processed/provenance.json` bằng một script MỚI do
   worker viết (không sửa `03`): giữ nguyên mọi trường của manifest
   vòng 2, chỉ đổi `generated_at` (mới), chuỗi `extractor` (ghi rõ
   staging đợt bổ sung + tên script), `counts` thành
   `{"sft": 19, "dpo": 19}`, và `data_sha256["dpo_pairs.jsonl"]` thành
   hash mới. `allow_dry_run` vẫn `false`, `run_tag_filter` vẫn
   `["build2"]`, `live_traces_kept` vẫn 160, `tasks` và `source_traces`
   giữ nguyên 20 task / 160 trace (cùng một tập nguồn — DPO mới chỉ
   trích khác đi từ cùng 160 trace live đó; xem
   `dpo_extraction_audit.json`).
4. Kiểm tra cổng ở local (không tốn GPU): chạy
   `modal run ... --stage sft_then_dpo --epochs 3` sẽ tự chạy
   `validate_data` ở local entrypoint TRƯỚC khi gọi remote — nếu cổng
   báo mismatch thì DỪNG và sửa staging. **TUYỆT ĐỐI KHÔNG dùng
   `--allow-unverified-data`.** (Không có cờ nào khác để bypass; mọi lỗi
   cổng đều là lỗi staging, phải sửa staging.)
5. Sau khi train xong (bước 10): khôi phục 3 file từ `staging-backup/`,
   verify hash khớp manifest vòng 2. `data/processed/` trở về trạng thái
   canonical vòng 2; file DPO đợt bổ sung vẫn nằm bền vững trong thư mục
   này + audit của nó. Ghi rõ việc khôi phục trong báo cáo.

## 4. Từng bước chạy

Làm việc từ repo root. Mọi lệnh `02` đều có `--mode live` và
`--skip-existing`, chia chunk để VM restart chỉ mất tối đa một chunk.
Nhiệt độ 0.0, n=1 cho mọi ô đo (đúng protocol vòng 2). Run tag cho toàn
bộ trace mới: **`suppl`** (rebuild) và **`suppl`** (heldout — tên file
heldout có thêm slug model nên không đụng độ; xem §8). KHÔNG dùng lại
tag `build2`/`rebuild2`/`heldout2`, KHÔNG ghi đè bất kỳ file trace nào
của vòng 2.

**Bước 0 — Chuẩn bị ($0).** Xác nhận Modal auth còn hạn (`modal token`
mới nếu hết hạn — user approve bằng browser của họ); `HELIX_LIVE_BASE_URL`
sẽ lấy từ URL deploy ở bước 2. Ghi SHA-256 của toàn bộ 520 trace hiện có
vào một file mới trong thư mục này (để chứng minh sau đợt chạy rằng
không file cũ nào bị sửa). Chạy test suite bằng modal-venv
(`~/workspace/modal-venv/bin/python -m unittest discover -s closed-loop/tests`;
kỳ vọng 17/17 — đã đạt ngày 2026-11-15). Hoàn tất staging §3 (bước 1–4).

**Bước 1 — Sao lưu adapter vòng 2.** Copy
`/vol/checkpoints/helix-lora-final` →
`/vol/checkpoints/helix-lora-final-round2-20261112` (qua Modal volume
commands/filesystem; xem `modal volume --help` tại thời điểm chạy — ghi
đúng lệnh đã dùng vào báo cáo). Verify số file + kích thước khớp nguồn.
DỪNG nếu không verify được — không train khi chưa có bản sao lưu đã
verify của adapter vòng 2.

**Bước 2 — Deploy endpoint (lần 1).** Deploy `01_modal_vllm.py`
(`modal deploy` hoặc `modal serve` theo quy ước đã dùng ở vòng 2 — ghi
rõ cách đã dùng). Verify `/health` trả `lora_enabled: true`, và routing:
một completion với model id base trả về đúng id base, một completion với
`helix-lora` trả về đúng `helix-lora`; ghi `max_model_len` 8192 nếu
endpoint công bố. DỪNG nếu routing sai (xem addendum proxy trong
`PROVENANCE_AUDIT.md`).

**Bước 3 — Judge pilot (10 ô).** Worker viết runner judge theo đúng spec
ở `JUDGE_PROMPT.md` §1/§4/§5 (prompt nguyên văn, temp 0.0, max_tokens
512, seed 20261115, model base id). Chạy thử 3 ô, kiểm tra bằng mắt
schema JSON + trích dẫn code. Sau đó chạy 10 ô, đo latency trung bình
thực tế, áp dụng checkpoint C1 (§7) để quyết định full 169 hay fallback
55. Pilot 10 ô tính vào tổng số ô đã chấm (không chấm lại).

**Bước 4 — Chạy judge toàn bộ.** Chạy nốt các ô còn lại theo danh sách
đã chọn (primary hoặc fallback) từ `judge_list.json`, tuần tự, ghi
append-only vào `judge_runs/<ngày>/judge_results.jsonl` (thư mục mới).
Ghi latency từng ô. Output hỏng xử lý theo `JUDGE_PROMPT.md` §5 (retry
1 lần, rồi đánh `unparseable` — không sửa tay). Sau bước này có thể dừng
app để tiết kiệm thời gian chờ (bước 7 sẽ deploy lại sau khi train) hoặc
giữ app nếu train chạy ngay sau đó — ghi rõ quyết định; ước tính §6 đã
tính 2 lần deploy và 2 cửa sổ scaledown nên cả hai lựa chọn đều nằm
trong ngân sách.

**Bước 5 — Train.** Chạy lệnh ở §1. Ghi run id, số bước + loss từng
stage (kỳ vọng SFT 9 bước, DPO 9 bước), và xác nhận `04` đã tải
`loss_history.json`/`metadata.json`/`versions.json` xuống
`data/training_runs/<run-id>/` (thư mục mới, không đè run cũ). Verify
metadata: `sample_counts` = SFT 19 / DPO 19, hash khớp file đã stage,
`provenance.allow_dry_run == false`.

**Bước 6 — Lưu adapter mới ra đường dẫn riêng.** Ngay sau khi train
xong, copy `/vol/checkpoints/helix-lora-final` →
`/vol/checkpoints/helix-lora-supplement-20261115`; verify số file +
kích thước. Adapter mới CHỈ được coi là đã lưu khi bản sao này verify
xong.

**Bước 7 — Redeploy endpoint (lần 2).** Redeploy `01` để load adapter
mới; verify lại `/health` + routing như bước 2 (lần này `helix-lora`
phải là adapter mới — không có cách nào phân biệt bằng mắt thường ngoài
run id/metadata của volume; ghi rõ thời điểm redeploy sau thời điểm
train xong + copy xong, và không chạy thêm train nào xen giữa).

**Bước 8 — Đo REBUILD-supplement (80 ô).** Model `helix-lora` (default
của phase rebuild), problem-set `train20`, tag `suppl`, 2 chunk:

```bash
python closed-loop/scripts/02_run_helix_eval.py --phase rebuild --mode live --problem-set train20 --run-tag suppl --skip-existing --start-index 0 --limit 10
python closed-loop/scripts/02_run_helix_eval.py --phase rebuild --mode live --problem-set train20 --run-tag suppl --skip-existing --start-index 10 --limit 10
```

Kỳ vọng 80 file `suppl_lcb_*_*.json`, tất cả `mode: live`,
`model == "helix-lora"`, `temperature == 0.0`.

**Bước 9 — Đo held-out-supplement (60 ô, chỉ model mới).** Model mới
trên `heldout2`, tag `suppl`, 2 chunk. Base model KHÔNG chạy lại (số
base 50/60 của vòng 2 đã có và vẫn là baseline so sánh):

```bash
python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout2 --run-tag suppl --model helix-lora --skip-existing --limit 8
python closed-loop/scripts/02_run_helix_eval.py --phase heldout --mode live --problem-set heldout2 --run-tag suppl --model helix-lora --skip-existing --start-index 8 --limit 7
```

Kỳ vọng 60 file `suppl_helix-lora_held2_*_*.json`, tất cả live.

**Bước 10 — Re-verify + thống kê ($0, offline).** Chạy lại sandbox test
cho MỌI flag `passed` của 140 trace mới (cùng phương pháp
`round2_stats.py::reverify` / `run_test_cases`): yêu cầu **0 mismatch**
trước khi tính bất kỳ thống kê nào. Tính per-harness Pass@1 + Wilson,
union, McNemar có cặp (suppl vs BUILD2; suppl-heldout vs base vòng 2 và
vs LoRA vòng 2), bảng flip — bằng script MỚI do worker viết, lọc đúng
baseline temp 0.0/sample 0, tag `suppl`. So sánh thêm tỉ lệ nhãn judge
theo model/harness (phân tích nhạy cảm, tách khỏi bảng chính — xem
`RUBRIC.md` §8). Verify lại SHA-256 của 520 trace cũ: không file nào
đổi.

**Bước 11 — Khôi phục + dừng.** Khôi phục `data/processed/` từ
`staging-backup/` (§3 bước 5, verify hash). Khôi phục
`/vol/checkpoints/helix-lora-final` từ bản sao lưu vòng 2
`helix-lora-final-round2-20261112` (verify số file/kích thước) để đường
dẫn live trở về trạng thái vòng 2 đã báo cáo; adapter đợt bổ sung vẫn
nằm ở `helix-lora-supplement-20261115`. Dừng Modal app và verify không
còn app chạy / endpoint trả 404 (như vòng 2). Ghi báo cáo theo checklist
§8.

## 5. Những việc worker GPU KHÔNG được làm

- Không dùng `--mode dry-run`, `--allow-dry-run`, `--seed-demo`,
  `--allow-unverified-data` cho bất kỳ dữ liệu nào đi vào train/đo.
- Không sửa prompt judge, rubric, luật DPO, hay file DPO đã trích.
- Không chạy lại BUILD (base) hay held-out base — số vòng 2 đã chốt.
- Không động tới `helix-lora-final-backup-20261112`,
  `helix-lora-final-backup-20261104`, fork, volume KG-R1, hay Drive.
- Không sửa/xóa trace vòng 1/vòng 2; không dùng lại tag cũ.
- Không để app chạy sau khi xong; không train thêm lần 2 nếu loss "xấu"
  mà không báo cáo và xin quyết định (train lại = đợt khác, cần đăng ký
  lại).
- Không trình bày số suppl như số vòng 2, không gọi đợt này là "vòng 3"
  trong bất kỳ file/báo cáo nào.

## 6. Ước tính chi phí (giá A100 $2.50/giờ, thống nhất cho mọi bước)

Cơ sở: latency đã ghi của vòng 2 (`data/analysis_round2.json` + trace):
REBUILD2 80 ô = 2159.9s; held-out v2 LoRA 60 ô = 1459.3s; train vòng 2
≈ $0.70 ở $2.10/giờ ≈ 1200s billed (gồm overhead container/load model;
compute thuần chỉ ~32s). Judge chưa từng chạy: ước 15s/lượt (ô minimal
1 bước của vòng 2 trung bình 13.5–17.9s với prompt ngắn hơn nhưng output
tối đa dài hơn; judge prompt dài hơn, output cap 512 token, kỳ vọng
~120 token) — xem checkpoint C1 để hiệu chỉnh bằng số đo pilot. Mọi dòng
serving/train đều nhân hệ số an toàn 1.15 theo quy ước vòng 2 (trừ dòng
overhead đã là số đệm).

| Bước | Thời gian GPU tính phí (ước) | Chi phí |
|---|---|---|
| Deploy ×2 + idle/scaledown (2 lần deploy ≈300s load + 2×180s scaledown + health check; dòng kém chắc chắn nhất — không có số đo deploy trong repo) | 1080s | $0.75 |
| Judge full: 169 lượt × 15s × 1.15 | 2915s | $2.02 |
| Train SFT→DPO (1200s billed vòng 2 + 300s đệm cho DPO 9 bước thay vì 3) | 1500s | $1.04 |
| Đo REBUILD-suppl: 2159.9s × 1.15 | 2484s | $1.72 |
| Đo held-out-suppl: 1459.3s × 1.15 | 1678s | $1.17 |
| Re-verify + thống kê | 0s (offline) | $0.00 |
| **TỔNG (judge full)** | **9657s (2.68 giờ)** | **$6.70** |
| Tổng nếu judge fallback 55 ô (55×15×1.15 = 949s = $0.66) | 7691s | **$5.34** |

Biên an toàn so với cap $8: **$1.30** (full) / **$2.66** (fallback).
Lưu ý nhạy cảm: `01` hiện deploy trên **A10G**, không phải A100 (dòng
`gpu="A10G"` trong script); `04` train trên A100. Bảng trên tính thống
nhất $2.50/giờ theo yêu cầu nhiệm vụ nên là ước tính BẢO THỦ cho phần
serving: nếu serving vẫn chạy A10G ở $1.10/giờ như vòng 2, tổng thực tế
dự kiến chỉ ≈ $3.53 (serving + overhead ≈ $2.49, train $1.04). Worker
ghi rõ GPU thực tế đã dùng cho từng bước và tính lại cả hai cột trong
báo cáo; KHÔNG tự ý đổi loại GPU của `01` mà không ghi nhận (latency
khác nhau làm sai ước tính).

## 7. Checkpoint và quy tắc dừng

- **C0 (trước mọi GPU, $0):** staging §3 đã qua cổng local; adapter vòng
  2 đã sao lưu + verify; checksum 520 trace đã ghi. Thiếu bất kỳ điều
  nào → dừng, không deploy.
- **C1 (sau judge pilot 10 ô):** chiếu tổng chi phí = judge thực đo
  (mean × số ô còn lại × 1.15) + các dòng còn lại ở §6. Nếu chiếu > $7.20
  → chuyển sang fallback 55 ô TRƯỚC khi chạy nốt judge. Nếu chiếu ≤ $7.20
  → chạy full 169.
- **C2 (sau judge, trước train):** chiếu lại với latency judge thực tế.
  Nếu chiếu > $8.00 → dừng và báo cáo (judge đã xong, train/đo hoãn lại
  — không cắt đo để bù judge, vì đo mới là mục đích của đợt bổ sung).
- **C3 (sau train):** ghi run id + loss; verify metadata (§4 bước 5).
  Train thất bại/gate lỗi → dừng, không thử lại bằng bypass.
- **C4 (sau đo):** re-verify 0 mismatch là điều kiện tiên quyết cho mọi
  thống kê. Mismatch > 0 → dừng, điều tra, không báo cáo số đo.
- **Quy tắc dừng cứng:** tại bất kỳ checkpoint nào, nếu chiếu tổng vượt
  $8.00 thì dừng ngay công việc GPU, hoàn tất phần offline có thể, và báo
  cáo trạng thái dở dang (chunk đã chạy được resume bằng `--skip-existing`
  trong đợt sau — không chạy thêm "chỉ một chunk nữa" để vượt cap).

## 8. Checklist báo cáo của worker GPU (bắt buộc)

1. Run id train + loss history từng stage (số bước thực tế, loss đầu/cuối);
   metadata train (counts, hash, provenance) — khớp §1?
2. Số ô judge đã chấm (full/fallback + lý do nếu fallback), tỉ lệ
   `unparseable`, latency judge trung bình thực tế, file kết quả.
3. Số trace mới: 80 suppl + 60 suppl-heldout, tất cả live, model đúng,
   temp 0.0; số mismatch re-verify (kỳ vọng 0); checksum 520 trace cũ
   không đổi.
4. Bảng Pass@1/union/McNemar/flip của suppl so với BUILD2, LoRA vòng 2,
   base held-out v2 — ghi rõ "đợt bổ sung", không trộn vào bảng vòng 2.
5. Bảng nhãn judge theo (tập, model, harness) + tỉ lệ, tách khỏi bảng
   chính; số ô judge `degenerate`/`suspicious` kèm file.
6. Adapter: bản sao lưu vòng 2 đã verify (số file/kích thước), adapter
   mới ở `helix-lora-supplement-20261115` đã verify, `helix-lora-final`
   đã khôi phục về vòng 2; backup vòng 1 không động tới.
7. `data/processed/` đã khôi phục về trạng thái vòng 2 (hash khớp).
8. App đã dừng + verify; chi phí ước tính thực tế theo latency đã ghi
   (cả hai cột giá A100 $2.50 và giá thực tế theo GPU đã dùng); mọi điểm
   lệch khỏi kế hoạch này + lý do.
