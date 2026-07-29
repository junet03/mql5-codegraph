# 2026-07-30 — MCP transport lifecycle evidence

## Objective

Make a future `Transport closed` incident attributable at the MQL5 CodeGraph process boundary, verify that
an idle stdio session remains usable, and deploy the fixed runtime without terminating active MCP sessions.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `5d73fc0`.
- Relevant specification: feature 004, especially the local MCP tool contract and plugin quickstart.
- Known constraints: Codex Desktop retained a dead client after its MCP child disappeared; this repository
  cannot make the host respawn a child. Five other live MCP process trees could not be stopped safely.
- The global Python installation had drifted back to an editable install pointing at
  `D:\mql5-codegraph\src`.

## Work completed

- Added one-line, JSON lifecycle records on stderr for MCP `starting`, clean `stopped`, and unexpected
  `crashed` outcomes. Records include process/runtime versions, PID/parent PID, exit classification, and no
  project roots, arguments, or environment values.
- Classified a normal FastMCP stdio return as `stdio_eof`, preserved `KeyboardInterrupt` and `SystemExit`
  semantics, and re-raised unexpected exceptions after recording their type.
- Added protocol coverage proving an indexed session remains usable after a configurable idle interval and
  emits `starting` followed by clean `stdio_eof`; added unit coverage for an unhandled startup/runtime crash.
- Documented the ownership boundary: the MCP process can report why it ended, but only the host can replace a
  dead transport and reinitialize a new child. Consumer guidance now stops futile retries and requires a fresh
  task or app reload followed by `project_status` and re-indexing.
- Built and installed a non-editable wheel into `C:\Python314\Lib\site-packages` without replacing the locked
  console launcher. The exact editable `.pth` file was moved to a recoverable disabled filename; no live MCP
  process was terminated.
- Refreshed the installed plugin to `0.1.0+codex.20260730002910`.

## Decisions

- Lifecycle evidence is adapter observability only; analysis remains in the backend-neutral Intelligence
  Kernel, so no ADR was required.
- Lifecycle records use stderr because stdout is reserved for MCP protocol frames.
- Server self-respawn was rejected: once stdio or the child process is gone, the owning host must create the
  replacement transport. The in-memory project snapshot must then be indexed again.
- Existing live MCP trees were preserved. Runtime refresh used a wheel-to-`site-packages` deployment that did
  not touch their locked launcher.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Focused lifecycle/protocol tests | `python -m unittest tests.mcp_adapter.test_lifecycle tests.mcp_adapter.test_protocol` | 4 tests passed |
| MCP adapter suite | `python -m unittest discover -s tests/mcp_adapter` | 14 tests passed |
| Configurable idle regression | `MQL5_CODEGRAPH_MCP_IDLE_TEST_SECONDS=2` with the idle protocol test | Passed after the idle interval with revision preserved |
| Full Python suite | `python -m unittest discover -s tests` after the non-editable wheel deployment | 135 tests passed in 12.519 seconds |
| Bytecode compilation | `python -m compileall -q src tests` | Passed |
| Patch whitespace | `git diff --check` | Passed |
| Wheel build | `uvx --from build pyproject-build --wheel` | Built `mql5_codegraph-0.2.0-py3-none-any.whl` |
| Installed import | `python -c "import mql5_codegraph.mcp.server as s; print(s.__file__)"` | Resolved from `C:\Python314\Lib\site-packages`, not the source tree |
| Installed dependency health | `python -m pip check` | No broken requirements; pip still warns about older invalid-distribution remnants |
| Installed MCP smoke test | Official MCP client started `mql5-codegraph-mcp`, listed tools, called `project_status`, then closed | 9 tools, `not_indexed` revision 0, lifecycle sequence `starting` then `stopped` with `stdio_eof` and exit 0 |
| Current Codex host transport | Called the live `project_status` MCP tool from the active task | Returned `not_indexed`, revision 0, in 12 ms |
| Plugin refresh | `codex plugin add mql5-codegraph-intelligence@mql5-codegraph-internal --json` | Installed and enabled version `0.1.0+codex.20260730002910` |
| Directed graph health | Incremental `graphify` update plus directed multigraph diagnostic | 1,830 nodes, 3,216 edges, no dangling, duplicate, collapsed, or ambiguous endpoint groups |

## Risks and unresolved questions

- This repository cannot correct Codex Desktop's host-side failure to respawn or reinitialize a dead MCP
  transport. The new records make the next occurrence diagnosable but do not change that host behavior.
- A production-length Codex host idle/resume soak has not yet been run. The regression uses a configurable
  short interval because the server has no idle timeout of its own.
- Pip reports old invalid-distribution remnants under `C:\Python314\Lib\site-packages`. They do not shadow the
  verified wheel import, and cleanup was intentionally deferred to a maintenance window.
- Graphify CLI `0.9.20` is older than skill `0.9.27`; the directed flag still requires post-update correction.

## Next objective

Run a 30-minute Codex Desktop idle/resume soak in a fresh task, correlate the host result with the lifecycle
stderr records, and file a host-side respawn issue if a dead client is retained again.
