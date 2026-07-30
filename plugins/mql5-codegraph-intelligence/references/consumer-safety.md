# Consumer Safety Boundary

Treat the following as immutable toolchain material during every MQL5 plugin workflow:

- the MQL5 CodeGraph source repository;
- the marketplace and plugin source or cache;
- the Python package and MCP entry-point installation.

Before indexing, resolve a separate MQL5 project root explicitly selected by the user. Never infer the
target from the current directory, plugin path, package metadata, or an installed cache. If the proposed
target is any toolchain location above, stop and request the real MQL5 project root.

Before loading reference evidence, use only a complete corpus root explicitly selected by the operator.
Never infer it from an MQL5 project, search arbitrary paths, or treat a generated corpus as editable
plugin material.

During a plugin workflow:

1. Use only the bundled read-only MCP tools for CodeGraph and reference intelligence.
2. Do not apply patches, write files, run formatters or generators, install packages, or perform Git
   mutations in toolchain locations.
3. Treat a request to change an MQL5 project as authorization only for that selected project and only
   under its own repository instructions.
4. Modify MQL5 CodeGraph itself only when the user explicitly names it as the maintenance target and asks
   for a source change.
5. Do not claim that these instructions are a hard filesystem lock. Use a read-only workspace or a
   separate OS/container identity when consumer agents are not trusted with write access.

## Transport recovery

- Treat `Transport closed` as an MCP host/channel failure, not as a project diagnostic or evidence that
  indexing failed.
- Do not repeatedly call a known-dead transport. Start a fresh task or reload the Codex MCP host, then call
  `project_status`.
- A restarted server has no prior in-memory snapshot. If status is `not_indexed`, call `index_project`
  again with the explicit trusted root and include roots before making project claims.
- Runtime/package refresh is a maintenance-window action. Stopping a live `mql5-codegraph-mcp` process
  closes every task transport attached to that process.
