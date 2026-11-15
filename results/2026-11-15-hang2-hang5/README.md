# Đợt bổ sung hàng 2+5 — file chuẩn bị offline (2026-11-15)

Chuẩn bị offline cho đợt bổ sung hàng 2+5 (KHÔNG phải vòng 3). Không GPU,
không Modal, không push, không Drive. Không file hiện có nào bị sửa; mọi
file dưới đây đều là file MỚI trong thư mục này.

## Đọc theo thứ tự

1. `RUBRIC.md` — rubric nhãn critic/filter (clean/suspicious/degenerate),
   đăng ký trước. Nhãn chỉ dùng cho phân tích, không đổi flag `passed`.
2. `DPO_RULES.md` — luật trích DPO mở rộng, đăng ký trước (luật A sibling
   cap 3/task + luật B fail→fixed cap 1/trace, cổng provenance).
3. `HEURISTIC_NOTES.md` — phương pháp + ngưỡng + kết quả heuristic.
4. `JUDGE_PROMPT.md` — prompt judge cố định (nguyên văn) + danh sách ô.
5. `GPU_RUN_PLAN.md` — từng bước chạy GPU, config DPO, đường dẫn adapter,
   staging provenance, ước tính chi phí, checkpoint dừng.

## File dữ liệu + script (xác định, chạy lại cho cùng hash)

| File | Nội dung |
|---|---|
| `heuristic_labels.py` (v2) | Script heuristic offline trên toàn bộ trace |
| `heuristic_labels.csv` / `.json` | Nhãn + tín hiệu cho 520/520 trace (SHA-256 trong `HEURISTIC_NOTES.md` §8) |
| `extract_dpo_expanded.py` (v1) | Script trích DPO theo đúng `DPO_RULES.md` |
| `dpo_pairs_expanded.jsonl` | 19 cặp DPO (SHA-256 `47b8e075…`) |
| `dpo_extraction_audit.json` | Audit cổng provenance, bảng theo task, 51 ứng viên bị loại + lý do, disposition luật B |
| `build_judge_list.py` (v1) | Script sinh danh sách judge (seed 20261115) |
| `judge_list.json` | Primary 169 ô, 15 cặp flip, fallback 55 ô, biến thể cả-hai-phía 70 ô |

## Số chốt (số thật, không ước tính)

- Trace: **520** (vòng 2: build2 160, rebuild2 80, heldout2 120; vòng 1: 160).
- Ô PASS baseline vòng 2: BUILD2 60/80, REBUILD2 66/80, held-out v2 50/60 + 53/60.
- Heuristic: 430/430 ô PASS `clean` ở mức literal; 15 trace rỗng + 7 trace
  sai tên hàm, toàn bộ FAIL (xem `HEURISTIC_NOTES.md` §5–§7).
- DPO mới: **19 cặp** (luật A 18 = 3/task × 6 task có tương phản; luật B 1
  = `lcb_009` bước 1→2, đã verify sandbox). 13 task toàn PASS + `lcb_002`
  toàn FAIL cho 0 cặp. SFT giữ nguyên 19 mẫu.
- Judge: primary **169** ô (vượt kỳ vọng ~140 — là số thật); fallback 55 ô.
- Test suite: 17/17 đạt (chạy bằng `~/workspace/modal-venv/bin/python`,
  2026-11-15; python hệ thống thiếu module `modal`).
- Ước tính GPU: **$6.70** (full) / **$5.34** (fallback) theo giá A100
  $2.50/giờ, dưới cap $8 (xem `GPU_RUN_PLAN.md` §6–§7).

## Chưa làm (thuộc về worker GPU, xem `GPU_RUN_PLAN.md`)

Chạy judge, staging DPO + manifest, train SFT→DPO, đo REBUILD-suppl 80 ô +
held-out-suppl 60 ô, re-verify, thống kê, khôi phục adapter +
`data/processed/`, dừng app. Không việc nào trong số đó được bắt đầu ở đây.
