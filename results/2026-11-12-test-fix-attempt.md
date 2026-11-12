# Cố gắng sửa 13 lỗi assertion và 6 lỗi timeout - 2026-11-12

Checkout thử nghiệm: HELIX `a090aba675be000b608e821f40ded4dc705e92af` tại
`~/workspace/helix-repro-clean-2026-11-11`, Node v24.22.1, npm 10.9.4, VM 1,5 CPU
chia sẻ. KHÔNG push, KHÔNG commit. Mọi sửa đổi chỉ nằm trên checkout này.

Log full test trước lượt này (11/11, đã có `node-pty` build tay):
`results/2026-11-11-npm-test-with-pty.txt` - 19 file fail / 89 pass,
29 test fail / 805 pass, 291 giây.

Log full test sau lượt này (12/11, chạy song song mặc định):
`results/2026-11-12-npm-test-after-fix.txt` - 18 file fail / 90 pass,
25 test fail / 809 pass, 293 giây.

Log full test chạy tuần tự (12/11, `--no-file-parallelism`, xem §6):
`results/2026-11-12-npm-test-sequential.txt` - 14 file fail / 94 pass,
18 test fail / 816 pass, 361 giây, 0 timeout.

## 0. Kết quả tóm tắt

- Đã sửa được 4 test trong full run: capture-dry-run 2, cli mock capture 1,
  current-module-placeholder-audit nhóm 2 (groups source-file) 1. Từ 29 fail
  xuống 25 fail.
- Đã sửa được thêm 2 test khi chạy riêng file (todo27-misleading và cli
  dry-run manifests), nhưng 2 test này vẫn timeout khi chạy full suite song
  song vì máy yếu, xem §4.
- Phát hiện quan trọng nhất: 8 trong 13 "lỗi assertion" theo phân loại cũ
  thực ra là lỗi symlink ENOENT, không phải assertion. Phân loại cũ sai vì
  log 11/11 chỉ in được 14/29 khối chi tiết lỗi. Số lỗi assertion thật chỉ
  còn 5, và cả 5 đã sửa xong.
- 6 timeout theo phân loại cũ thực ra là 7 timeout trong full run mới (thêm
  todo27 và cli dry-run, vốn là assertion trước đây nhưng giờ timeout vì
  tranh chấp CPU). Cả 7 đều pass khi chạy riêng file.
- Không có lỗi assertion thật nào còn lại trong phạm vi 13 + 6 này.

## 1. Sửa đổi đã thực hiện (2 file)

### 1a. `packages/external-tools/src/verifiers.ts` - sửa lỗi thật của source

Hàm `runManifestEnvAllowlistSupported` dùng regex `/^[A-Z_][A-Z0-9_]*$/`,
chỉ chấp nhận tên biến môi trường toàn chữ hoa. Nhưng chính `runner.ts`
trong cùng package có `CAPTURE_ENV_EXACT_ALLOWLIST` cho phép cả
`http_proxy`, `https_proxy`, `all_proxy`, `no_proxy` (chữ thường), và
`externalToolChildEnv` đưa các biến này vào manifest. Kết quả: manifest
do runner sinh ra bị chính verifier của repo bác bỏ, check
`run-manifest.env-allowlist` fail, mỗi khi môi trường có đặt biến proxy
chữ thường (như trên VM/sandbox này). Trên máy tác giả có thể không đặt
các biến này nên test từng pass.

Sửa: regex thành `/^[A-Za-z_][A-Za-z0-9_]*$/`, kèm chú thích giải thích
mâu thuẫn nội bộ này. Đây là sửa phía source (verifier quá chặt), không
phải sửa test, không làm yếu assertion: verifier vẫn bắt tên rỗng, tên
chứa ký tự lạ và tên trùng lặp.

Kiểm chứng: script tái hiện bằng tsx in toàn bộ report verification, chỉ
đúng 1 check fail là `run-manifest.env-allowlist`. Sau sửa, file
capture-dry-run 11/11 pass, `npm run typecheck` sạch.

Chỗ khác dùng regex hoa-only (`packages/recipes/src/installed-harness.ts:1169`)
KHÔNG đụng tới: đó là validator tên biến lúc kích hoạt profile, không liên
quan tới các lỗi này, và test của nó đang fail vì symlink (ngoài phạm vi).

### 1b. `packages/conformance/todo27-misleading-native-copy.conformance.test.ts` - sửa kỳ vọng sai trong test

Test yêu cầu file `TODO/TODO-027.md` phải có trong danh sách file được
audit, nhưng: thư mục `TODO/` nằm trong `.gitignore` (dòng 13) từ đầu, file
này chưa từng xuất hiện trong bất kỳ commit nào (`git log --all` không có),
12 file bắt buộc còn lại đều tồn tại. Kỳ vọng này không thể thỏa trên bất
kỳ clone mới nào, chỉ pass trên máy tác giả nơi file tồn tại local.

Sửa: bỏ `TODO/TODO-027.md` khỏi `REQUIRED_AUDITED_FILES`, kèm chú thích
ghi rõ lý do. Không bịa file mới, không bỏ check nào khác: test vẫn kiểm
tra đủ 12 file bắt buộc còn lại, vẫn quét toàn bộ text surfaces, vẫn bắt
`unguarded` phải rỗng và `guarded` phải chứa đủ 3 pattern. Sau sửa, file
này 1/1 pass khi chạy riêng.

## 2. Bảng từng test trong phạm vi 13 assertion + 6 timeout

### 2a. Nhóm assertion - 8 test thực ra là lỗi symlink (ngoài phạm vi)

Cả 8 test đều chưa từng chạm tới assertion nào: chúng crash ngay ở bước
lint/quét repo với `ENOENT: stat '.../fixtures/tasks/livecodebench-v6-000-abc387-b'`
từ `packages/recipes/src/boundary-lint.ts:203` (`statSync` trên symlink hỏng).
Chạy riêng từng file ngày 12/11 đều tái hiện đúng lỗi này.

| File test | Tên case | Kết quả |
| --- | --- | --- |
| block-ledger | keeps the catalog, port fixtures, recipe bindings, package exports, and boundary lint in sync | ENOENT symlink, chưa sửa (ngoài phạm vi) |
| compatible-bridge-visibility | keeps the completed TODO27 compatible bridge set empty across Builder, Flow, and audits | ENOENT symlink, chưa sửa |
| nanobot-lego-depth | audits Nanobot as decomposed lego atoms rather than a monolithic adapter | ENOENT symlink, chưa sửa |
| p1-native-like-visibility | keeps P1 native-like projections completed and prevents any native-like residuals | ENOENT symlink, chưa sửa |
| preview-metadata-retention-visibility | keeps preview shells completed while metadata overlays remain visibly non-executable | ENOENT symlink, chưa sửa |
| product-turn-profile-visibility | keeps product turn atoms visible after the profile-compatible queue drains | ENOENT symlink, chưa sửa |
| recipe-targets | freezes atom-level target shapes for OpenCode, Pi Mono, neutral minimal, and binding-only swaps | ENOENT symlink, chưa sửa |
| reverse-assembly | proves product recipes can be assembled back into harness surfaces | ENOENT symlink, chưa sửa |

Lưu ý: `boundary-lint.ts:203` dùng `statSync` không bắt lỗi nên một symlink
hỏng làm sập cả lần quét. Có thể tranh luận là nên sửa lint cho chịu được
symlink hỏng, nhưng làm vậy sẽ giấu lỗi fixture thật mà các test này vốn
được viết ra để phát hiện. Vì vậy không sửa lint; gốc lỗi vẫn là 101
symlink, thuộc phạm vi đã chốt là không đụng tới.

### 2b. Nhóm assertion - 5 test lỗi thật, đã sửa xong

| File test | Tên case | Nguyên nhân | Sửa |
| --- | --- | --- | --- |
| capture-dry-run | writes a run manifest without launching the external tool | Verifier regex hoa-only bác env-allowlist chứa proxy chữ thường (§1a) | §1a, pass 11/11 khi chạy riêng, pass cả trong full run |
| capture-dry-run | runs a mock external tool capture and records artifacts | Cùng nguyên nhân §1a (verify manifest của lần capture thật) | §1a, pass trong full run |
| cli | runs claude-tap capture through a mock CLI binary | Cùng nguyên nhân §1a (CLI exit 1 vì verification bên trong fail) | §1a, pass trong full run (không còn trong danh sách fail) |
| cli | writes claude-tap capture dry-run manifests through the CLI | Cùng nguyên nhân §1a về mặt assertion, nhưng trong full run mới lại timeout 15s vì tranh chấp CPU (xem §4). Khi chạy riêng file: pass, 3951ms | §1a + xem §4 |
| todo27-misleading-native-copy | keeps fake/compatible/preview/metadata/native-like wording guarded across repository text surfaces | Kỳ vọng file `TODO/TODO-027.md` không thể thỏa trên clone mới (§1b) | §1b, pass 1/1 khi chạy riêng; trong full run mới lại timeout 5s vì tranh chấp CPU (xem §4) |

### 2c. Nhóm timeout - 7 test trong full run mới, đều pass khi chạy riêng

| File test | Tên case | Timeout đặt | Thời gian trong full run mới | Thời gian khi chạy riêng file | Kết luận |
| --- | --- | --- | --- | --- | --- |
| cli | reports claude-tap preflight readiness without leaking credential values | 120000ms | 120089ms (vượt 89ms) | 92298ms, pass | Tranh chấp CPU, xem §4 |
| cli | writes claude-tap capture dry-run manifests through the CLI | 15000ms | 15010ms (vượt 10ms) | 3951ms, pass | Tranh chấp CPU |
| cli | runs an OpenCode recipe through the CLI entrypoint | 5000ms | 5005ms (vượt 5ms) | 2197ms, pass | Tranh chấp CPU |
| config-prompt-ui | builds Nanobot memory, skills, recent history, archived summary, and Dream prompts from upstream templates | 15000ms | 19314ms | pass, 52/52, 2 lần chạy riêng đều pass | Tranh chấp CPU |
| current-module-placeholder-audit | lists every current module gap with owner TODO, evidence, lossiness, and next action | 5000ms | 6580ms | pass, 5/5, 2 lần chạy riêng đều pass | Tranh chấp CPU |
| current-module-placeholder-audit | is available through the public CLI and writes verifiable report artifacts | 5000ms | 7016ms | pass, 5/5, 2 lần chạy riêng đều pass | Tranh chấp CPU |
| todo27-misleading-native-copy | keeps fake/compatible/preview/metadata/native-like wording guarded across repository text surfaces | 5000ms | 5084ms (vượt 84ms) | 26ms, pass | Tranh chấp CPU |

## 3. Tổng kết full test

| Lượt chạy | Test files fail / pass | Test fail / pass | Ghi chú |
| --- | --- | --- | --- |
| 11/11, song song, có node-pty | 19 / 89 | 29 / 805 | Baseline trước lượt này |
| 12/11, song song, sau 2 sửa | 18 / 90 | 25 / 809 | 4 test sửa xong; 25 fail còn lại = 18 symlink + 7 timeout |
| 12/11, tuần tự `--no-file-parallelism`, sau 2 sửa | 14 / 94 | 18 / 816 | 0 timeout; 18 fail còn lại toàn là symlink ENOENT |

Trong 25 fail của full run song song ngày 12/11, không còn lỗi assertion
thật nào trong phạm vi: 18 fail là ENOENT symlink, 7 fail là timeout.
Các file khác (89 file trước đây pass) vẫn pass, không làm hỏng test nào.

## 4. Vì sao kết luận 7 timeout là do máy yếu, không phải lỗi code

- Cùng một test, cùng một code, chạy riêng file thì pass nhanh: todo27 chỉ
  26ms, OpenCode 2197ms, cli dry-run 3951ms, audit 5/5 hai lần đều
  pass, config-prompt-ui 52/52 hai lần đều pass, cli 37/37 pass trong
  123 giây.
- Trong full run song song, 108 file test chạy cùng lúc trên VM chỉ có 1,5
  CPU chia sẻ. 3 test vượt timeout với biên độ chỉ 5-89ms (OpenCode vượt
  5ms, cli dry-run vượt 10ms, todo27 vượt 84ms, preflight vượt 89ms) - tức
  là code gần như đã xong việc, chỉ thiếu vài chục ms vì CPU bị chia.
- Test todo27 là bằng chứng rõ nhất: nó chỉ đọc file đồng bộ, chạy riêng
  mất 26ms, vậy mà trong full run mất 5084ms (chậm gấp ~195 lần). Không
  có lỗi logic nào làm một test 26ms thành 5 giây; chỉ có tranh chấp CPU
  mới làm được vậy.
- Không sửa bằng cách tăng timeout trong test: các timeout 5s/15s/120s là
  timeout do tác giả đặt (vitest mặc định 5s, các test dài đặt riêng 15s
  và 120s), không có tài liệu nào trong repo nói các giá trị này sai. Tăng
  timeout chỉ để ép pass trên máy yếu là làm yếu test. Cách đúng là chạy
  trên máy khỏe hơn hoặc chạy tuần tự (xem §6).

## 5. `git diff --stat` của checkout thử nghiệm

```
 docs/reports/current-module-placeholder-audit.json | 1438 ++++++------
 docs/reports/current-module-placeholder-audit.md   |    4 +-
 docs/reports/task-parity-split/manifest.json       |  162 +--
 packages/conformance/todo27-misleading-native-copy.conformance.test.ts | 6 +-
 packages/external-tools/src/verifiers.ts           |   7 +-
 5 files changed, 813 insertions(+), 804 deletions(-)
```

3 file đầu là từ lượt sửa trước (11/11), không đụng tới trong lượt này.
2 file cuối là sửa của lượt này (§1a, §1b). Kiểm chứng thêm sau khi sửa:
`npm run typecheck` sạch, `npm run current-module:audit:verify` exit 0
(`ok: true`, `issues: []`), `npm run task:parity:split:verify` exit 0.

## 6. Full test chạy tuần tự (kiểm chứng giả thuyết tranh chấp CPU)

Lệnh: `npx vitest run --no-file-parallelism` (các file test chạy nối tiếp
nhau thay vì song song), 361 giây, exit 1.

Kết quả: **14 file fail / 94 pass, 18 test fail / 816 pass, 0 timeout.**

18 fail còn lại toàn là nhóm symlink ENOENT ở §7a, không có test nào khác
fail. Cụ thể các file trong phạm vi lượt này đều pass trọn vẹn khi chạy
tuần tự:

- cli: 37/37 pass (105207ms) - cả preflight 120s, dry-run manifests,
  mock capture và OpenCode recipe đều pass.
- config-prompt-ui: 52/52 pass (6876ms).
- current-module-placeholder-audit: 5/5 pass (8539ms).
- todo27-misleading-native-copy: 1/1 pass.
- capture-dry-run: không còn trong danh sách fail (11/11 pass).

Đây là bằng chứng quyết định cho §4: cùng một code, cùng một máy, chỉ đổi
từ chạy song song sang chạy tuần tự mà 7 timeout biến mất hết. Timeout là
hậu quả của việc 108 file test tranh nhau 1,5 CPU, không phải lỗi code.
Tổng thời gian chạy tuần tự (361 giây) còn lâu hơn chạy song song (293
giây) vì không tận dụng được song song, nhưng kết quả thì sạch hơn.

## 7. Lỗi còn lại

### 7a. 18 lỗi symlink ENOENT - ngoài phạm vi lần này

block-ledger, boundary-lint, compatible-bridge-visibility, docs-site 4,
installed-harness, nanobot-lego-depth, p1-native-like-visibility,
preview-metadata-retention-visibility, product-turn-profile-visibility,
recipe-targets, reverse-assembly, todo29-builder-flow-visibility 2,
package-exports, task-parity. Tất cả cùng một gốc: 101 symlink trong
`packages/conformance/fixtures/tasks` trỏ tới đường dẫn tuyệt đối trên máy
tác giả. Cần file fixture của tác giả hoặc dựng lại từ dữ liệu công khai,
ghi rõ là fixture mới.

### 7b. 7 lỗi timeout - cần máy khỏe hơn, không phải sửa code

Liệt kê ở §2c. Trên máy có CPU dư dả hoặc chạy tuần tự, các test này pass
(xem §6). Không nên sửa lặng lẽ bằng cách tăng timeout.

## 8. Lỗi thật của upstream mà nhóm không nên tự sửa lặng lẽ

1. **Verifier env-allowlist quá chặt (§1a)** - lỗi thật trong source của
   tác giả: producer và verifier mâu thuẫn nhau về tên biến môi trường
   chữ thường. Sửa lần này là đúng phía (verifier), nhưng nếu đưa lên
   upstream thì nên báo cho tác giả kèm bằng chứng là chính allowlist của
   họ có `http_proxy`, chứ không nên sửa lặng trong fork rồi coi như xong.
2. **Test todo27 yêu cầu file gitignored không tồn tại (§1b)** - lỗi thật
   trong test của tác giả: kỳ vọng không thể thỏa trên clone mới. Sửa lần
   này chỉ bỏ một dòng kỳ vọng, nhưng quyết định đúng đắn về lâu dài là
   hoặc commit file TODO-027 thật, hoặc bỏ kỳ vọng này ở upstream.
3. **101 symlink tuyệt đối + `statSync` không bắt lỗi ở boundary-lint** -
   lỗi thật về tính tái lập của repo tác giả, đã biết từ lượt trước, chưa
   đụng tới.
