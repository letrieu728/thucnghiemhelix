# Smoke test: harness HELIX lắp thật + LoRA 7B — KẾT QUẢ & CHẨN ĐOÁN

Ngày: 2026-11-12, chạy 21:26–21:39 +07. Đề bài và tiêu chí đã cam kết trước
trong TASK_SPEC.md (không sửa sau khi chạy).

## Kết luận ngắn

**Chưa ghép được.** Harness lắp thật (pi-mono, 297 module) assemble thành công
và chạy tới bước gọi model, nhưng request tới endpoint chết ở tầng proxy
streaming: server trả 200, client (CLI) nhận 502 Bad Gateway rỗng. Ngoài ra
còn một blocker thứ hai độc lập ở tầng model: cả base lẫn LoRA đều sinh tool
call theo định dạng XML `<function_call>` mà parser Hermes không nhận ra
(`tool_calls: []`), nên kể cả khi streaming thông thì tool cũng không bao giờ
được thực thi. Không phải lỗi do LoRA — base model cũng y hệt.

## Đánh giá tiêu chí (theo TASK_SPEC.md)

- (a) CLI chạy xong không lỗi hạ tầng: **FAIL**. Process exit 0 nhưng output
  JSON ghi `finish: "provider_error"`, error: `Provider openai-compatible
  request failed (502 Bad Gateway): ` (xem harness_run_lora.clean.json).
- (b) Endpoint thực sự nhận request từ harness: **FAIL (một nửa)**. Request
  CÓ tới được server — log Modal ghi `POST /v1/chat/completions -> 200 OK
  (12.7s)` cho lần chạy của CLI — nhưng response không tới được CLI (502
  rỗng), transcript không có nội dung nào do model sinh ra.
- (c) Harness gọi tool hoặc vòng lặp transcript hoạt động: **FAIL**. 1 step
  duy nhất, kết thúc bằng provider error, `blockedTools: []`, không có tool
  call nào, transcript chỉ có prompt + thông báo lỗi.
- (d) Code cuối cùng chạy đúng (in 15): **FAIL**. `workspace/buggy.py` không
  bị sửa (byte-identical), chạy thật vẫn in `10`.

## Chuyện gì xảy ra, từng bước

1. Setup local: `npm install --ignore-scripts` trong upstream clone (đã mất
   node_modules từ lần trước), 13 giây, OK. Đọc code CLI xác nhận: lệnh `run`
   assemble harness thật (`assembleHarness` -> `assemblePiMonoHarness`, recipe
   piMonoRecipe), `runTurn` gọi provider openai-compatible, provider LUÔN gửi
   `stream: true` và kèm `tools` khi harness có tool (pi-mono có 4 tool thật:
   bash, edit, read, write).
2. Độ lệch bắt buộc: `minimal` KHÔNG phải product chạy được (`parseProduct`
   chỉ chấp nhận opencode/pi-mono/hybrid/nanobot/hermes-agent). Dùng pi-mono.
3. Deploy endpoint từ script gốc trong repo (không sửa): OK, /health 200,
   `lora_enabled: true`, /v1/models liệt kê cả base và `helix-lora`.
4. Probe trực tiếp (mô phỏng đúng request của harness: stream + tools):
   HTTP 400 `"auto" tool choice requires --enable-auto-tool-choice and
   --tool-call-parser to be set`. Chẩn đoán rõ: thiếu parser. Không chạy
   harness vào endpoint đã biết chắc sẽ 400 — dùng 1 lần redeploy được phép.
5. Redeploy 1 lần duy nhất từ bản copy có thêm `--enable-auto-tool-choice`
   và `--tool-call-parser hermes` (diff 4 dòng, file 01_modal_vllm_smoke.py).
   Bản gốc trong repo không bị động vào. Endpoint nóng lên: health 200,
   đủ 2 model.
6. Probe stream + tools sau redeploy: server log 200 (10.5s, 3.25s) nhưng
   client nhận 0 byte / HTTP 502 rỗng. Lặp lại 2 lần, cùng kết quả.
7. Probe non-stream + tools (LoRA): HTTP 200, body về đầy đủ. Nhưng model
   sinh tool call dạng XML `<function_call>` trong `<response>`, và
   `tool_calls: []` — parser Hermes không parse được.
8. Probe chẩn đoán bằng base model (1 lần duy nhất được phép, non-stream +
   tools): Y HỆT LoRA — cùng định dạng XML, `tool_calls: []`. Kết luận:
   không phải lỗi do LoRA, mà là hành vi của base model/template.
9. Chạy harness thật 1 lần (lệnh trong TASK_SPEC.md, --max-steps 8,
   --max-retries 0): assemble OK (graph 297 module, session tạo), 1 step,
   `finish: provider_error`, 502 Bad Gateway. Server log ghi request này
   200 trong 12.7s — model đã sinh response phía server nhưng response
   không qua được proxy tới CLI.
10. Tắt app ngay: `modal app stop --yes`, kiểm chứng: app stopped, 0 task,
    0 container đang chạy, endpoint trả 404.

## Chẩn đoán theo tầng

| Tầng | Trạng thái | Bằng chứng |
|---|---|---|
| Lắp ráp harness (CLI assemble) | OK | graph 297 module, session tạo, chạy tới bước gọi provider |
| Endpoint vLLM + LoRA serving | OK | health 200, 2 model, non-streaming trả 200 + nội dung |
| Tool-call parser (server flags) | ĐÃ SỬA (1 redeploy) | 400 -> 200 sau khi bật hermes parser |
| Định dạng tool call của model | BLOCKER | base + LoRA đều sinh `<function_call>` XML, `tool_calls: []` với parser Hermes |
| Proxy FastAPI + SSE streaming | BLOCKER | non-streaming: server 200 -> client 200; streaming: server 200 -> client 502/rỗng (3/3 lần). CLI bắt buộc stream:true. Nguyên nhân khả dĩ nhất: proxy đệm toàn bộ response và copy nguyên header hop-by-hop (transfer-encoding...) của vLLM, gây lỗi framing ở edge proxy. |

## Có đáng thử tiếp không

Đáng, nhưng cần 2 lần sửa, mỗi lần đều ngoài scope của smoke test này:

1. Sửa proxy trong 01_modal_vllm.py: dùng StreamingResponse + lọc header
   hop-by-hop (hoặc bỏ proxy, cho Modal serve thẳng vLLM). Sau đó deploy
   lại và chạy lại harness — lần này CLI sẽ nhận được response.
2. Sửa định dạng tool call: thử chat-template override kiểu Hermes
   (`--chat-template`) hoặc parser khác khớp định dạng XML của Qwen2.5-Coder;
   cần thực nghiệm vì chưa chắc model sẽ đổi định dạng theo template.

Chỉ khi cả hai xong thì harness thật mới gọi tool được. Ngoài ra còn một
rủi ro chưa được kiểm chứng: chính sách quyền tool mặc định của recipe
pi-mono trả "ask" cho mọi tool call, trong chế độ headless tool có thể bị
chặn (trường blockedTools) — chỉ biết được sau khi 2 blocker trên được gỡ.

## Chi phí & trạng thái cuối

- GPU: 2 container A10G (1 bản gốc + 1 bản parser), tổng thời gian chạy
  ~12–15 phút gồm 2 lần cold start. Ước tính ~$0.2–0.4 (ước tính theo giờ
  GPU, không đọc được số dư chính xác qua CLI), dưới cap $2. Tiền từ credit.
- App `helix-vllm-engine`: STOPPED 21:39 +07, 0 task, 0 container, endpoint
  trả 404. Deployment đang lưu trên Modal là bản CÓ parser (từ file copy
  trong thư mục này); muốn về đúng bản trong repo thì deploy lại script gốc
  trong thucnghiemhelix (không tốn GPU nếu không gọi request).
- Không push gì lên remote nào, không động Drive/deck/báo cáo/Kaggle.

## File bằng chứng (thư mục này)

- TASK_SPEC.md — đề bài + đáp án kỳ vọng + lệnh + tiêu chí (viết trước)
- workspace/buggy.py — file bài (không bị sửa), chạy thật vẫn in 10
- modal_deploy_smoke.log, modal_deploy_smoke_parser.log — 2 lần deploy
- 01_modal_vllm_smoke.py — bản copy có thêm 2 cờ parser (diff 4 dòng)
- direct_probe_tools.txt — probe đầu: HTTP 400 thiếu parser
- direct_probe_tools_parser.txt — 0 byte (streaming qua proxy: server 200,
  client rỗng)
- direct_probe_nonstream_tools.txt — LoRA non-stream: 200, XML function_call,
  tool_calls []
- direct_probe_base_nonstream_tools.txt — base non-stream: y hệt LoRA
- harness_run_lora.json — output thô của CLI (kèm banner npm)
- harness_run_lora.clean.json — output JSON của CLI (finish: provider_error)
- harness_run_lora.stderr — rỗng
