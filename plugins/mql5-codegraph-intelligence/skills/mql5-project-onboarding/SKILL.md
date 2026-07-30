---
name: mql5-project-onboarding
description: Index and orient a trusted local MQL5 repository with the bundled MQL5 CodeGraph MCP server. Use when entering a new MQL5 project, when the active project is unknown or stale, or before architecture, impact, diagnostics, or release analysis.
---

# MQL5 Project Onboarding

Before any tool call, read and obey
[the consumer safety boundary](../../references/consumer-safety.md). Never infer the analysis target from
the plugin, marketplace, package, cache, or MQL5 CodeGraph source path.

Use this workflow to establish a current evidence-backed snapshot before making project claims.

1. Resolve the current repository root and read applicable `AGENTS.md` guidance.
2. Call `project_status` from the bundled `mql5-codegraph` MCP server.
3. Call `index_project` with the trusted absolute repository root when:
   - no project is active;
   - the active root differs;
   - tracked MQL5 source changed after the active snapshot;
   - the user explicitly requests a refresh.
4. Supply include roots only when the project or user identifies them. Never guess a private
   MetaTrader installation path.
5. Report the indexed file, node, edge, and diagnostic counts plus the source fingerprint.
6. Treat an empty project as a valid result. Do not claim that an empty graph proves the repository
   has no behavior.

The index is in memory only. It does not modify source or persist graph files.

Before a freshness-sensitive follow-up, compare the expected source fingerprint or re-index. Live
source and tests remain more authoritative than the graph.

Reference attachment is optional and independent. If the task needs MQL5 platform documentation, hand off
to `$mql5-reference-research`; do not infer or discover a corpus path during project onboarding. See the
[reference evidence rules](../../references/reference-corpus.md).
