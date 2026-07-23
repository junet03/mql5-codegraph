# Quickstart: Private MQL5 Agent Plugin

## Install the optional MCP runtime

```powershell
python -m pip install -e ".[mcp]"
```

## Run the server directly

```powershell
mql5-codegraph-mcp
```

The command uses stdio and is normally launched by Codex; it does not print user-facing logs to stdout.

## Install the repo marketplace

```powershell
codex plugin marketplace add D:\mql5-codegraph
codex plugin add mql5-codegraph-intelligence@mql5-codegraph-internal
```

Restart Codex and use `/mcp` to verify the bundled server. In a new MQL5 project task:

1. Call `project_status`.
2. Call `index_project` with the trusted absolute project root when needed.
3. Use `query_symbols`, `get_context`, `get_impact`, `find_paths`,
   `get_context_package`, or `get_diagnostics`.
4. Re-index after source changes before making freshness-sensitive claims.

## Verification

On 2026-07-23, the official MCP client used the installed `mql5-codegraph-mcp` entry point to initialize
the server, discover the exact eight-tool surface, index `tests/fixtures/basic_ea`, query `OnTick`, and
receive a structured pre-index tool error without crashing. The focused service/protocol suite passed
9 tests, the plugin and all four skills passed their official validators, and Codex reported
`mql5-codegraph-intelligence` version `0.1.0+codex.20260723151025` as installed and enabled.

The complete release-gate commands and results are recorded in
`docs/project-journal/2026-07-23-002-private-mcp-plugin-alpha.md`.
