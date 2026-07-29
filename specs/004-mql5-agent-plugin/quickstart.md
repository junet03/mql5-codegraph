# Quickstart: Private MQL5 Agent Plugin

## Build and install the consumer MCP runtime

```powershell
uvx --from build pyproject-build
python -m pip install "mcp>=1.28.1,<2"
python -m pip install --force-reinstall --no-deps (Resolve-Path .\dist\mql5_codegraph-*.whl)
python -m pip show mql5-codegraph
```

The package details must not contain `Editable project location`. Consumer agents must run the wheel
installation so the MCP entry point does not import live code from this source checkout.

An editable install (`python -m pip install -e ".[mcp]"`) is reserved for an explicit MQL5 CodeGraph
maintainer session. Reinstall the wheel before returning the machine to consumer-agent use.

## Run the server directly

```powershell
mql5-codegraph-mcp
```

The command uses stdio and is normally launched by Codex; it does not print user-facing logs to stdout.
It emits bounded `mql5-codegraph-mcp.lifecycle` JSON records to stderr for startup, clean stdin EOF, and
unhandled failure.

For a configurable idle regression (30 minutes shown):

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
$env:MQL5_CODEGRAPH_MCP_IDLE_TEST_SECONDS = '1800'
python -m unittest tests.mcp_adapter.test_protocol.McpProtocolTests.test_idle_session_survives_and_reports_clean_stdio_eof
Remove-Item Env:\MQL5_CODEGRAPH_MCP_IDLE_TEST_SECONDS
```

This proves the server remains live while its client transport remains open. It does not prove that Codex
Desktop will respawn a child process it has externally ended. If a task reports `Transport closed`, reload
the task/app MCP host and re-index; retrying the same dead transport cannot restore the in-memory snapshot.

## Install the repo marketplace

```powershell
codex plugin marketplace add D:\mql5-codegraph
codex plugin add mql5-codegraph-intelligence@mql5-codegraph-internal
```

Restart Codex and use `/mcp` to verify the bundled server. Do not attach this source repository as a
writable consumer workspace. In a new task rooted at the actual MQL5 project:

1. Call `project_status`.
2. Call `index_project` with the trusted absolute project root when needed.
3. Use `query_symbols`, `get_context`, `get_impact`, `find_paths`,
   `get_context_package`, `get_diagnostics`, or `correlate_compiler_log` with an explicitly supplied
   bounded MetaEditor log.
4. Re-index after source changes before making freshness-sensitive claims.

All four skills load the bundled consumer safety policy. They treat this source repository, the plugin
source/cache, marketplace, and Python installation as immutable toolchain material. This policy prevents
accidental changes; genuinely untrusted agents still require a read-only workspace or a separate
OS/container identity.

## Verification

On 2026-07-23, the official MCP client used the installed `mql5-codegraph-mcp` entry point to initialize
the server, discover the original eight-tool surface, index `tests/fixtures/basic_ea`, query `OnTick`, and
receive a structured pre-index tool error without crashing. The focused service/protocol suite passed
9 tests, the plugin and all four skills passed their official validators, and Codex reported
`mql5-codegraph-intelligence` version `0.1.0+codex.20260723151025` as installed and enabled.

On 2026-07-24, the consumer runtime was rebuilt and reinstalled from its wheel. `pip show` no longer
reported an editable project, the import resolved under `C:\Python314\Lib\site-packages`, the nine MCP
adapter tests passed, and Codex installed policy-hardened plugin version
`0.1.0+codex.20260724032118`.

On 2026-07-29, the non-editable wheel was refreshed after compiler-evidence added BOM-marked UTF-16
MetaEditor-log support. The official installed MCP stdio client discovered the nine-tool surface, including
`correlate_compiler_log`, and returned `current` / `success` for the isolated supported log fixture.
Codex installed plugin version `0.1.0+codex.20260729212553`.

On 2026-07-30, transport-lifecycle telemetry and idle/crash regressions were added after a Codex Desktop
task retained a dead stdio client without respawning its child. The server-side evidence now distinguishes
clean EOF and unhandled failure; Codex host-side respawn remains outside this repository. Codex installed
plugin version `0.1.0+codex.20260730002910`.

The original alpha evidence and consumer-isolation evidence are recorded in
`docs/project-journal/2026-07-23-002-private-mcp-plugin-alpha.md` and
`docs/project-journal/2026-07-24-001-plugin-consumer-isolation.md`.
