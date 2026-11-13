# Smoke test: harness HELIX lắp thật + model LoRA 7B — ĐỀ BÀI & CAM KẾT TRƯỚC

Ngày: 2026-11-12 (tối, giờ +07). Người duyệt: Triệu. Scope: 1 task × 1 harness × model LoRA.

## Độ lệch khỏi kế hoạch gốc (ghi rõ, có căn cứ code)

Kế hoạch gốc nói product `minimal`, nhưng `parseProduct` trong
`packages/cli/src/index.ts` (dòng ~3999) CHỈ chấp nhận: opencode, pi-mono,
opencode-pi-hybrid, nanobot, hermes-agent. `minimal` chỉ là tên recipe lắp
ghép (`coding-agent.minimal`), không chạy được bằng lệnh `run`.
=> Harness dùng cho smoke: **pi-mono** (harness thật đơn giản nhất chạy được,
cũng là harness tham chiếu Pi của paper). 4 tool của pi-mono (đọc từ code
`createPiDefaultTools`, packages/lego-tools/src/default-tools.ts): bash,
edit, read, write.

## Đề bài (viết TRƯỚC khi chạy, không sửa sau)

File: `workspace/buggy.py` (thư mục làm việc riêng, cô lập).

```python
def sum_first_n(n):
    """Return 1 + 2 + ... + n."""
    total = 0
    for i in range(n):
        total += i
    return total


if __name__ == "__main__":
    print(sum_first_n(5))
```

Lỗi: off-by-one — `range(n)` cộng 0..n-1 thay vì 1..n.
Hành vi lỗi (đã chạy thật bằng python3 trước khi test): in ra `10`.
Đáp án kỳ vọng sau khi sửa: in ra `15` (1+2+3+4+5).
Bản sửa đúng tối thiểu: `range(1, n + 1)` hoặc `range(n + 1)`.

## Prompt gửi cho harness (tiếng Anh, nguyên văn)

"The file buggy.py in the working directory has an off-by-one bug:
sum_first_n(5) prints 10 instead of 15. Read the file, fix the bug, then
run the file to verify it prints 15. Only modify buggy.py."

## Lệnh chạy (điền endpoint thật sau khi deploy)

```
cd ~/workspace/helix-eval/upstream
timeout 600 npm run helix -- run pi-mono \
  --provider openai-compatible \
  --model helix-lora \
  --base-url <ENDPOINT>/v1 \
  --api-key dummy \
  --prompt "<prompt trên>" \
  --json \
  --max-steps 8 \
  --cwd <logdir>/workspace \
  --storage-dir <logdir>/storage
```

Model `helix-lora` = adapter LoRA vòng 2 (helix-lora-final trên Modal volume).
Endpoint: app Modal `helix-vllm-engine` (A10G), vLLM OpenAI-compatible.

## Tiêu chí thành công (đánh giá từng cái PASS/FAIL sau khi chạy)

(a) Lệnh CLI chạy xong, exit code 0, không lỗi hạ tầng.
(b) Endpoint thực sự nhận request từ harness (output JSON/transcript có nội
    dung do model sinh ra; lỗi provider nếu có phải ghi rõ).
(c) Harness có gọi tool (read/edit/bash) HOẶC vòng lặp transcript hoạt động
    (nhiều step, model phản hồi theo transcript).
(d) Code cuối cùng trong buggy.py chạy đúng: `python3 buggy.py` in ra `15`
    (chạy thật, không đoán). Nếu model chỉ trả code trong text mà không sửa
    file thì (d) FAIL theo nghĩa "harness sửa file", nhưng ghi rõ code trong
    text có đúng không.

## Lưu ý đã biết trước (từ đọc code, chưa kiểm chứng bằng chạy)

- Endpoint vLLM hiện tại KHÔNG có cờ --tool-call-parser /
  --enable-auto-tool-choice trong 01_modal_vllm.py. pi-mono gửi `tools`
  trong request chat completions. Nếu lỗi 400 do tool call thì mới redeploy
  1 lần có bật parser (hermes) rồi thử lại đúng 1 lần.
- Chính sách quyền tool mặc định của recipe pi-mono trả về trạng thái "ask"
  cho mọi tool call; trong chế độ headless (NoopUI) tool có thể bị chặn
  (trường blockedTools trong output JSON). Quan sát thực tế khi chạy.
