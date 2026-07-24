# Consumer Safety Boundary

Treat the following as immutable toolchain material during every MQL5 plugin workflow:

- the MQL5 CodeGraph source repository;
- the marketplace and plugin source or cache;
- the Python package and MCP entry-point installation.

Before indexing, resolve a separate MQL5 project root explicitly selected by the user. Never infer the
target from the current directory, plugin path, package metadata, or an installed cache. If the proposed
target is any toolchain location above, stop and request the real MQL5 project root.

During a plugin workflow:

1. Use only the bundled read-only MCP tools for CodeGraph intelligence.
2. Do not apply patches, write files, run formatters or generators, install packages, or perform Git
   mutations in toolchain locations.
3. Treat a request to change an MQL5 project as authorization only for that selected project and only
   under its own repository instructions.
4. Modify MQL5 CodeGraph itself only when the user explicitly names it as the maintenance target and asks
   for a source change.
5. Do not claim that these instructions are a hard filesystem lock. Use a read-only workspace or a
   separate OS/container identity when consumer agents are not trusted with write access.
