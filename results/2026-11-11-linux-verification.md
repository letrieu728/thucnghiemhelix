# Offline verification on Linux — 2026-11-11

Source HELIX: clean clone of `https://github.com/Vietng-XPrince7/HELIX`,
checked out at `a090aba675be000b608e821f40ded4dc705e92af`, `git status` clean
before every run. Environment: Linux (kernel 7.0.0-44-generic, this VM),
Node `v24.22.1`, npm `10.9.4`. No API key, no model calls, no paid benchmarks
(no LiveCodeBench, SWE-bench, live provider, native CLI, full search).
Raw logs for every command are in this folder
(`2026-11-11-<command>.txt`); each log starts with timestamp, commit,
Node/npm versions, the exact command, and its exit code.

## Install deviation (recorded, not hidden)

Plain `npm ci` **FAILED** (exit 1): the `node-pty` native build could not
extract the node headers tarball —
`TAR_ENTRY_ERROR EPERM: operation not permitted, fchown`
(see `2026-11-11-npm-ci-failed.txt`). The sandbox blocks `chown` even as
root. Fallback used for all runs in this batch: `npm ci --ignore-scripts`
(exit 0; the native `node-pty` build was skipped, `tsx`/`vitest`/`tsc` all
present). Consequences of the fallback: the two test files that load
`node-pty` fail to load (`docs-site`, `installed-harness` — 0 tests each).
The `tsx`/`tsc` verifiers do not load `node-pty` and are unaffected.

## Verifier results — identical to Windows 2026-11-10

| Command | Result | Evidence |
| --- | --- | --- |
| `npm run typecheck` | PASS (exit 0) | `tsc` finished, no diagnostics |
| `npm run assembly:contract:verify` | PASS (exit 0) | Strict verification, 5 products |
| `verify-flow-graph` (9 artifacts) | PASS (9/9) | 5 blueprint + 4 comparison artifacts |
| `npm run executable:audit:verify` | PASS (exit 0) | Fingerprint `44370eff3ea1ca3a` |
| `npm run todo27:inventory:verify` | PASS (exit 0) | Fingerprint `e12a2bb0941ac9c7` |
| `npm run todo27:opencode:acceptance:verify` | PASS (exit 0) | `ready-for-review`, 108/124 native |
| `npm run task:parity:verify` | FAIL (exit 1) | 3 failing checks, all `artifact.acceptance-timing.drift-metadata` (missing acceptance-timing drift metadata) |
| `npm run task:parity:cadence:verify` | FAIL (exit 1) | Same missing acceptance-timing drift metadata |
| `npm run task:parity:split:verify` | FAIL (exit 1) | 161 failing checks: attachment hash/byte-size mismatch vs manifest (e.g. `multi-file-refactor-*`, `read-only-answer-*`) |
| `npm run current-module:audit:verify` | FAIL (exit 1) | Artifact fingerprint `ce386d45f16fbeda` vs recomputed `413e63553ad22ce5` |

Nothing changed between Windows 10/11 and Linux 11/11 on any verifier:
same 6 PASS, same 4 FAIL, same fingerprints. The four failures are
properties of the committed artifacts, not of the operating system.

## Cassette regeneration — BLOCKED on Linux too, different cause

`npm run task:parity` on the clean checkout: exit 1, no artifact written
(`git status` stayed clean). The error is **not** the Windows `EPERM`:

```text
ENOENT: no such file or directory, stat '.../packages/conformance/fixtures/tasks/livecodebench-v6-000-abc387-b'
```

Root cause (checked, not guessed): the fixture entries are symlinks
committed in git, and all **101** of them point to an absolute path on the
author's machine:

```text
packages/conformance/fixtures/tasks/livecodebench-v6-000-abc387-b
  -> /home/HarnessLego-pi-lcb-eval/packages/conformance/fixtures/tasks/livecodebench-v6-000-abc387-b
```

All 101 symlinks are broken on any machine without
`/home/HarnessLego-pi-lcb-eval` (101/101 broken here; `git ls-files` shows
these are the only 101 symlinks in the whole repo). So cassette
regeneration cannot work from a clean checkout anywhere until the fixtures
are real files or relative links. The Windows `EPERM` was an earlier,
different failure point; even past it, the symlinks would still block
regeneration.

## Full test suite — first complete totals (2026-11-11)

`npm test` (`vitest run`), 13:29:04–13:34:23 UTC, duration 317.07s,
exit 1:

- Test files: **20 failed / 88 passed (108)**
- Tests: **26 failed / 797 passed (823)**

Failed files (20): `current-module-placeholder-audit` (3 tests),
`config-prompt-ui` (1), `docs-site` (0 tests, failed to load),
`capture-dry-run` (2), `task-parity` (1), `installed-harness`
(0 tests, failed to load), `cli` (4), `todo27-opencode-split-acceptance`
(1), `todo29-builder-flow-visibility` (2), `package-exports` (2),
`preview-metadata-retention-visibility` (1),
`product-turn-profile-visibility` (1),
`todo27-misleading-native-copy` (1), `p1-native-like-visibility` (1),
`reverse-assembly` (1), `compatible-bridge-visibility` (1),
`block-ledger` (1), `boundary-lint` (1), `recipe-targets` (1),
`nanobot-lego-depth` (1).

Classification by cause, read from the log (labels are mine, counts are
from the log):

- **Broken fixture symlinks (ENOENT, same cause as above): 4 tests** —
  `task-parity` (1), `todo29-builder-flow-visibility` (2),
  `package-exports` "keeps tests on public package exports" (1).
- **Missing `node-pty` native build (install fallback, not the repo):
  2 files, 0 tests** — `docs-site`, `installed-harness` fail to load with
  `Failed to load native module: pty.node`.
- **Timeouts (5s / 15s / 120s) on a shared 1.5-CPU VM: 8 tests** —
  `current-module-placeholder-audit` (3 × 5s), `todo27-opencode-split-acceptance`
  (1 × 5s), `config-prompt-ui` (1 × 15s), `cli` (1 × 120s, 1 × 5s),
  `package-exports` (1 × 120s). These may be environment slowness rather
  than repo defects; do not read them as content failures without a rerun
  on a faster machine.
- **Assertion failures: 12 tests** — `capture-dry-run` (2),
  `todo27-misleading-native-copy` (1), `cli` mock capture (1),
  `block-ledger`, `boundary-lint`, `compatible-bridge-visibility`,
  `nanobot-lego-depth`, `p1-native-like-visibility`,
  `preview-metadata-retention-visibility`,
  `product-turn-profile-visibility`, `recipe-targets`, `reverse-assembly`
  (1 each).

One genuine Linux-vs-Windows difference: `tools.conformance`
(26 tests) and `hooks.conformance` (22 tests) **PASSED** on Linux, where the
Windows run had observed 4 failures in tools and 1 in hooks (without a
final suite summary).

## What changed vs 2026-11-10 (Windows)

- Verifier outcomes: **no change** (6 PASS / 4 FAIL, same fingerprints).
- Full test: **now has final totals** (was inconclusive on Windows).
- Tools/hooks conformance: **pass on Linux** (failed on Windows).
- Cassette regeneration: **still BLOCKED, root cause now identified**
  (absolute symlinks), not just the Windows `EPERM`.
- Install: plain `npm ci` is also blocked in this Linux sandbox
  (`node-pty` EPERM on `fchown`); the `--ignore-scripts` fallback is what
  made the runs above possible, and it costs the 2 `node-pty`-loading test
  files.

## What is still missing after this round

1. Fix the 101 absolute fixture symlinks (real files or relative links),
   then regenerate the task-parity cassette and re-verify.
2. Regenerate / correct the three failing verifier artifacts: task-parity
   acceptance-timing drift metadata, split-parity manifest hashes/sizes,
   current-module audit fingerprint.
3. Re-run the full suite on a machine with a working `node-pty` build to
   separate install artifacts (2 files) and possible timeout artifacts
   (8 tests) from real failures.
4. Paid benchmarks (LiveCodeBench, SWE-bench, live provider, native CLI,
   full search) remain not run — out of scope for this repo by design.
