# Tình trạng harness thật + benchmark thật — HELIX (13/11/2026)

> Chỉ tóm tắt tình trạng theo bằng chứng đã có; không chạy thêm thí nghiệm, không suy diễn số.

## (a) Đã thử gì và kết quả

- Smoke test tối 12/11 (21:26–21:39 +07), 1 task × 1 harness × 1 model: sửa lỗi off-by-one trong `buggy.py` (`sum_first_n(5)` in 10, kỳ vọng in 15, chỉ được sửa file này); harness pi-mono lắp thật; model `helix-lora` (LoRA vòng 2) qua endpoint vLLM trên Modal.
- `minimal` không phải product chạy được (`parseProduct` chỉ chấp nhận opencode/pi-mono/hybrid/nanobot/hermes-agent) nên buộc dùng pi-mono: assemble OK (graph 297 module, 4 tool thật bash/edit/read/write), chạy tới bước gọi model.
- Kết luận: **CHƯA GHÉP ĐƯỢC.** Cả 4 tiêu chí cam kết trước đều FAIL: (a) CLI kết thúc bằng `provider_error` (502 rỗng); (b) request có tới server (log 200 trong 12,7s) nhưng transcript không có nội dung nào do model sinh ra; (c) chỉ 1 step, không có tool call nào; (d) `buggy.py` không bị sửa (byte-identical), chạy thật vẫn in 10.
- Chi phí ~$0,2–0,4 từ credit (dưới cap $2); app đã tắt ngay sau khi chạy, endpoint trả 404.

## (b) Hai blocker + bằng chứng

- **Blocker 1 — proxy FastAPI làm hỏng streaming.** CLI bắt buộc `stream: true`; khi streaming, server trả 200 nhưng CLI nhận 502 rỗng, 3/3 lần (2 probe + 1 lần chạy harness); không streaming thì 200 bình thường. Chẩn đoán khả dĩ nhất (chưa chứng minh dứt điểm): proxy đệm toàn bộ response và copy nguyên header hop-by-hop của vLLM.
- **Blocker 2 — định dạng tool call.** Cả base lẫn LoRA đều sinh tool call dạng XML `<function_call>`, parser Hermes không nhận (`tool_calls: []`), nên tool không bao giờ được thực thi. Không phải lỗi LoRA: probe chẩn đoán bằng base cho kết quả y hệt.
- Đã redeploy 1 lần duy nhất, bật `--enable-auto-tool-choice` + `--tool-call-parser hermes` (từ bản copy, file gốc trong repo không động vào): probe stream + tools từ 400 thành 200 phía server — nhưng phía client vẫn kẹt ở blocker 1.

## (c) Cần sửa gì để thử tiếp

1. Sửa proxy trong `01_modal_vllm.py`: dùng `StreamingResponse` + lọc header hop-by-hop (hoặc bỏ proxy, cho Modal serve thẳng vLLM), rồi deploy lại.
2. Sửa định dạng tool call: thử chat-template override kiểu Hermes (`--chat-template`) hoặc parser khác khớp định dạng XML của Qwen2.5-Coder — chưa chắc model đổi định dạng theo template, cần thực nghiệm.
- Rủi ro chưa kiểm chứng: policy tool mặc định của pi-mono trả `"ask"` cho mọi tool call; ở chế độ headless tool có thể bị chặn — chỉ biết được sau khi gỡ 2 blocker trên.

## (d) Benchmark thật: vì sao chưa làm được

- 101 fixture symlink trong repo upstream trỏ tới đường dẫn tuyệt đối trên máy tác giả; nội dung không có trong repo, nhóm không bịa fixture. Vì vậy không chạy được benchmark của tác giả.
- 3 artifact FAIL đã đóng dạng FAIL(bản gốc)/PASS(bản tái sinh ngày 11/11/2026) — đó là bằng chứng tái tạo, không phải điểm benchmark.
- Bối cảnh: paper dùng 65 ứng viên × 100 bài LiveCodeBench-derived + 55 bài SWE-bench Verified, model cố định MiniMax-M2.7-highspeed, và KHÔNG train model (§9.5). Nhóm dùng 35 bài tự viết + 4 harness mô phỏng bằng prompt (system prompt + vòng lặp chat), nên không được suy diễn kết quả offline thành chất lượng benchmark.

## (e) Đối chiếu slide 35 — KHỚP, không vênh

- Slide 35 ("Hạn chế & lưu ý", deck v2 đã đồng bộ) nêu đúng 2 lỗi của smoke test (proxy hỏng streaming; tool call XML mà parser không nhận) và đúng "3 artifact FAIL đã đóng bằng bằng chứng tái tạo 11/11; 101 symlink vẫn gãy".
- Slide không nêu chi tiết (4 tiêu chí FAIL, 502 3/3, base cũng sinh XML, 1 lần redeploy, chi phí, rủi ro "ask") — đây là lược bớt của slide tóm tắt, không phải mâu thuẫn.
- Lưu ý khi trả lời thầy: câu "4 harness … chưa phải recipe đã assemble thật" trên slide nói về 4 harness mô phỏng dùng trong vòng train/đánh giá, không phủ nhận việc smoke test đã assemble pi-mono thật (297 module, assemble OK). Cần phân biệt rõ hai việc này.

## Nguồn

- `helix-eval/logs/smoke-harness-2026-11-12/RESULTS.md`, `TASK_SPEC.md` (bằng chứng cũng ở repo, `results/2026-11-12-real-harness-smoke-test/`).
- Deck `Bao_cao_HELIX-v2-so-lieu-vong2.pptx`, slide 35 (trích text trực tiếp từ file, đã kiểm tra thứ tự slide).
