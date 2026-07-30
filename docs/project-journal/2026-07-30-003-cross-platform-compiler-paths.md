# 2026-07-30 — Cross-platform compiler paths

## Objective

Fix the two failing Ubuntu jobs on draft PR #1 without changing compiler-evidence meaning or weakening
project containment.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `5537f7a`
- Relevant specification: `specs/006-compiler-correlation/spec.md`
- Known constraints: preserve exact/no-declaration/outside-project evidence states; never probe a
  diagnostic path outside the selected project root.

## Work completed

- Confirmed both Python 3.11 and 3.14 Ubuntu jobs failed the same existing regression:
  `C:\outside\Secret.mqh` was classified as `no_declaration` instead of `outside_project`.
- Updated diagnostic path classification to detect absolute Windows and POSIX syntax independently of
  the host `pathlib.Path` flavor before resolving a candidate.
- Added a regression containing both `C:\outside\WindowsSecret.mqh` and
  `/outside/PosixSecret.mqh`; both remain locationless `outside_project` evidence on Windows and Linux.

## Decisions

- No new ADR. This restores the accepted compiler-evidence containment contract and removes
  host-dependent behavior.
- Foreign absolute paths are classified without a filesystem probe. Native paths continue through the
  existing resolved-root containment check.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Failing hosted jobs | GitHub Actions run `30558156261`, jobs `90923902943` and `90923903045` | Both reproduced the same path-flavor assertion failure |
| Focused regression | `python -m unittest tests.test_compiler_evidence -v` | 8 tests passed |
| Full regression | `python -m unittest discover -s tests` | 159 tests passed in 19.132 s |
| Bytecode | `python -m compileall -q src tests tools` | Passed |
| Graph refresh | `graphify update D:\mql5-codegraph` plus directed multigraph diagnostic | 2,422 nodes and 4,333 valid directed edges; no dangling, missing, self-loop, duplicate, or collapsed edges |
| Patch hygiene | `git diff --check` | Passed |

## Risks and unresolved questions

- The local Windows suite proves native Windows and foreign POSIX absolute paths. The hosted Ubuntu
  rerun remains the authoritative proof for foreign Windows absolute paths on POSIX.
- MetaEditor execution is not part of this CI fix; compiler evidence still correlates only an
  operator-supplied log.

## Next objective

Push the focused fix to draft PR #1 and verify all six hosted CI jobs reach a terminal passing state.
