# MQL5 CodeGraph Plugin Consumer Boundary

When this directory is reached through an installed plugin, marketplace, cache, or tool lookup, treat it
as immutable runtime material.

- Do not edit, format, generate, install, stage, commit, or push files in this directory.
- Do not use this directory, its parent repository, an installed plugin cache, or the Python package
  location as the target MQL5 project.
- Use only the bundled read-only MCP tools against a separate project root explicitly selected by the user.
- Source maintenance is allowed only when the user explicitly names MQL5 CodeGraph itself as the target
  and requests a repository change.

These instructions prevent accidental mutation. Hard isolation for untrusted agents requires a read-only
workspace or a separate OS/container identity.
