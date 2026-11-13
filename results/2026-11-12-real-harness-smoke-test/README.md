# Smoke test: ghép LoRA 7B với harness HELIX lắp thật (12/11/2026)

## Kết luận: chưa ghép được

Thử nghiệm chạy 1 bài sửa lỗi Python qua 1 harness lắp thật bằng CLI của
tác giả (pi-mono, 297 module), dùng adapter LoRA vòng 2 (`helix-lora`) qua
endpoint vLLM trên Modal. Harness assemble thành công và chạy tới bước gọi
model, nhưng **không ghép được**, do 2 blocker độc lập, cả hai đều đã chẩn
đoán rõ bằng probe trực tiếp:

1. **Proxy FastAPI + streaming:** CLI bắt buộc `stream: true`; server vLLM
   trả 200 nhưng response không qua được proxy tới CLI (CLI nhận 502 rỗng,
   3/3 lần). Chạy không streaming thì vẫn 200 bình thường.
2. **Định dạng tool call của model:** cả model gốc lẫn LoRA đều sinh tool
   call dạng XML `<function_call>`, parser Hermes không nhận ra
   (`tool_calls: []`), nên tool không bao giờ được thực thi. Đây không phải
   lỗi do LoRA — model gốc cũng sinh y hệt.

Chi tiết đầy đủ, từng bước và chẩn đoán theo tầng: xem
[RESULTS.md](./RESULTS.md). Đề bài, lệnh và tiêu chí PASS/FAIL đã cam kết
trước khi chạy: xem [TASK_SPEC.md](./TASK_SPEC.md).

## File trong thư mục này

| File | Nội dung |
| --- | --- |
| `TASK_SPEC.md` | Đề bài, đáp án kỳ vọng, lệnh chạy, tiêu chí (viết trước khi chạy) |
| `RESULTS.md` | Kết quả, chẩn đoán theo tầng, chi phí, trạng thái cuối |
| `workspace/buggy.py` | File bài có lỗi off-by-one (không bị sửa; chạy thật vẫn in `10`) |
| `storage/2026-11-12T14-37-48-019Z_ses_….jsonl` | Session transcript của CLI (prompt + `provider_error` 502) |
| `harness_run_lora.clean.json` | Output JSON của lệnh `run` (graph 297 module, `finish: provider_error`) |
| `direct_probe_tools.txt` | Probe đầu: HTTP 400 vì server thiếu tool-call parser |
| `direct_probe_tools_parser.txt` | **File rỗng — đó chính là bằng chứng:** probe streaming sau redeploy, server 200 nhưng client nhận 0 byte |
| `direct_probe_nonstream_tools.txt` | Probe LoRA không streaming: 200, tool call XML, `tool_calls: []` |
| `direct_probe_base_nonstream_tools.txt` | Probe model gốc không streaming: y hệt LoRA |
| `modal_deploy_smoke.log` | Log deploy endpoint từ script chuẩn trong repo |
| `modal_deploy_smoke_parser.log` | Log redeploy 1 lần từ bản sao có parser |
| `01_modal_vllm_smoke.py` | **Bản sao chẩn đoán** của script serve (thêm 4 dòng cờ parser); script chuẩn nằm ở `closed-loop/scripts/01_modal_vllm.py` |

## Những gì cố tình không đưa lên

- Output thô của CLI (`harness_run_lora.json`): trùng toàn bộ nội dung
  `harness_run_lora.clean.json`, chỉ thêm banner npm; lệnh chạy đầy đủ đã
  ghi trong `TASK_SPEC.md`.
- `stderr` của lần chạy: file rỗng, không thêm thông tin (đã ghi trong
  `RESULTS.md`).

## Trạng thái sau thử nghiệm

App Modal `helix-vllm-engine` đã tắt ngay sau khi chạy (0 task, endpoint
trả 404). Chi phí GPU ước tính ~$0,2–0,4 từ credit, dưới trần $2 đã duyệt.
Muốn ghép được cần 2 lần sửa ngoài scope smoke test này: sửa proxy để
stream đúng chuẩn, và sửa định dạng tool call của model (xem mục "Có đáng
thử tiếp không" trong `RESULTS.md`).
