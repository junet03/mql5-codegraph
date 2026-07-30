---
name: mql5-change-impact
description: Assess the blast radius and risk of changing MQL5 symbols with upstream impact, directed paths, diagnostics, and evidence. Use before modifying handlers, trading logic, risk management, shared includes, public functions, or runtime-dispatch targets.
---

# MQL5 Change Impact

Before any tool call, read and obey
[the consumer safety boundary](../../references/consumer-safety.md). Never infer the analysis target from
the plugin, marketplace, package, cache, or MQL5 CodeGraph source path.

Start with `$mql5-project-onboarding` when snapshot freshness is uncertain.

When impact depends on a documented MQL5 API or runtime contract, use `$mql5-reference-research` and
retain the separate [reference evidence class](../../references/reference-corpus.md).

1. Resolve the target with `query_symbols`; never silently pick one ambiguous match.
2. Call `get_impact` to identify upstream dependants under explicit depth and item bounds.
3. Use `get_context` with `outgoing` to identify downstream dependencies and side-effect paths.
4. Use `find_paths` for critical routes such as event handler -> signal -> order/risk operation.
5. Call `get_diagnostics` and include relevant unresolved or malformed-source caveats.
6. Classify findings:
   - direct: extracted or resolved edge with source location;
   - runtime-dependent: MetaTrader dispatch or other runtime-derived edge;
   - uncertain: inferred, ambiguous, unresolved, stale, or truncated evidence.

Report affected symbols, why they are affected, the strongest source evidence, and the tests or
compile checks that should be run. A missing path means only "not found within these bounds" unless
completion explicitly says the search finished and the nodes are not connected.
