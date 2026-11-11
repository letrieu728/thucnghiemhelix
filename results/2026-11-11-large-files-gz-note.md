# Hai file log lớn - lưu dạng nén gzip + base64

Hai file gốc dưới đây quá lớn để đẩy lên GitHub qua API (bản thô 5,1MB và
7,8MB đều bị lỗi HTTP 413, request body too large), và file `.gz` nhị phân
cũng không đẩy được qua công cụ snapshot (chỉ nhận file text UTF-8).
Nên hai file được lưu dạng `.gz.b64`: nén gzip rồi mã hóa base64 thành text.
Nội dung sau khi giải mã và giải nén khớp đúng với bản gốc, đã kiểm chứng
bằng sha256.

| File trên repo | File gốc | Kích thước gốc | sha256 của file gốc sau khi khôi phục |
| --- | --- | --- | --- |
| `results/2026-11-11-assembly-contract-verify.txt.gz.b64` | `results/2026-11-11-assembly-contract-verify.txt` | 5.147.108 byte | `8739d860dee9aef3440a9f9dbcc66aa1e5a1ccc808ea44383b8ce2ac44a9bd4b` |
| `results/2026-11-11-fixed-artifacts/current-module-placeholder-audit.regenerated-2026-11-11.json.gz.b64` | `results/2026-11-11-fixed-artifacts/current-module-placeholder-audit.regenerated-2026-11-11.json` | 7.853.945 byte | `741379d69b6eae880ee376b22e0a8c9478a04549ce77fefb0703d793982cf186` |

Cách lấy lại bản gốc:

```bash
base64 -d results/2026-11-11-assembly-contract-verify.txt.gz.b64 | gunzip > results/2026-11-11-assembly-contract-verify.txt
base64 -d results/2026-11-11-fixed-artifacts/current-module-placeholder-audit.regenerated-2026-11-11.json.gz.b64 | gunzip > results/2026-11-11-fixed-artifacts/current-module-placeholder-audit.regenerated-2026-11-11.json
sha256sum results/2026-11-11-assembly-contract-verify.txt results/2026-11-11-fixed-artifacts/current-module-placeholder-audit.regenerated-2026-11-11.json
```

Bản gốc chưa nén vẫn còn ở máy local tại
`~/workspace/thucnghiemhelix-push-2026-11-11/results/`.
