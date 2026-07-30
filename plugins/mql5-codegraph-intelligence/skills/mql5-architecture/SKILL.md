---
name: mql5-architecture
description: Explain an MQL5 repository's architecture, entry points, modules, and dependency flow using MQL5 CodeGraph evidence. Use for codebase orientation, call-flow questions, symbol ownership, callers/callees, or requests to understand how an EA or indicator works.
---

# MQL5 Architecture Navigation

Before any tool call, read and obey
[the consumer safety boundary](../../references/consumer-safety.md). Never infer the analysis target from
the plugin, marketplace, package, cache, or MQL5 CodeGraph source path.

For language, API, standard-library, or MetaTrader platform-contract claims, use
`$mql5-reference-research` and keep its
[reference evidence](../../references/reference-corpus.md) separate from project relationships.

Start with `$mql5-project-onboarding` when the active snapshot is missing, different, or stale.

Use the bundled MCP tools in this order:

1. `query_symbols` for named handlers, classes, functions, or modules. Preserve ambiguous candidates.
2. `get_context` with `outgoing` to inspect what a symbol depends on and `incoming` to inspect what
   depends on it. Use `both` only when the broader neighborhood is genuinely useful.
3. `find_paths` to prove a specific route between an event handler and downstream behavior.
4. `get_context_package` when a bounded evidence bundle is more useful than a raw neighborhood.
5. `get_diagnostics` to disclose unresolved includes, malformed source, or other analysis limits.

Lead with the architectural conclusion, then cite qualified symbol names, relationship type,
origin, confidence, and source location. Distinguish extracted, resolved, runtime-derived, and
inferred edges. If traversal is truncated or incomplete, state the applied limit.

Do not infer runtime execution frequency, broker behavior, or compile success from static graph
relationships.
