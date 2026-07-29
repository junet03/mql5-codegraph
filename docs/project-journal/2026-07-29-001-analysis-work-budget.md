# 2026-07-29 — Analyzer work-budget implementation

## Objective

Bound one local MQL5 analysis operation across discovery, parsing, resolution, and runtime enrichment
without publishing a partial graph or replacing a valid agent snapshot after exhaustion.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `d6beb20`.
- Relevant specification: `specs/005-analysis-work-budget/spec.md`.
- Known constraints: local trusted-input analysis only; no persistent index, remote transport, MetaEditor
  control, compiler correlation, or raw-source MCP retrieval expansion.

## Work completed

- Added the canonical request-scoped `AnalysisBudget` and typed `AnalysisBudgetExceeded` result in
  `src/mql5_codegraph/analysis_budget.py`.
- Threaded the same budget through source discovery, lexing, parsing, include/call resolution, and
  runtime enrichment. Completed graphs keep their previous deterministic serialization.
- Added `max_work` projections for the library, CLI, dashboard startup/API/jobs, and MCP
  `index_project`. CLI does not create its output on exhaustion; dashboard and MCP retain their last
  complete graph/snapshot.
- Added focused phase, fan-out, no-mutation, CLI, dashboard, and MCP regression coverage.
- Documented the public contract, limitations, architecture, changelog, and accepted decision in
  [ADR-0006](../decisions/ADR-0006-analysis-work-budget.md).

## Decisions

- Use 1,000,000 deterministic work units by default and validate an explicit per-operation value from
  1 through 10,000,000. This is a finite analysis-work boundary, not a wall-clock promise. See
  [ADR-0006](../decisions/ADR-0006-analysis-work-budget.md).
- Keep the graph and MCP snapshot transactional: exhaustion is an actionable error, never incomplete
  evidence. MetaEditor/compiler correlation remains a separate feature.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Focused budget contracts | `python -m unittest tests.test_analysis_budget tests.test_parser tests.test_indexer tests.test_cli tests.test_web_state tests.mcp_adapter.test_service` with `PYTHONPATH=src` | 42 tests passed |
| Full Python regression | `python -m unittest discover -s tests` with `PYTHONPATH=src` | 124 tests passed in 10.137s |
| Python compilation | `python -m compileall -q src tests tools` | Passed |
| Dashboard quality gate | `npm run lint` and `npm run build` in `web/` | Passed; production assets built |
| CLI quickstart success | `python -m mql5_codegraph.cli analyze tests/fixtures/basic_ea --output <temp>/basic-ea.codegraph.json --json` | Exit 0; 3 files, 16 nodes, 22 edges, 5 diagnostics |
| CLI budget exhaustion | Same fixture with `--max-work 1` | Exit 1; `analysis_budget_exceeded`, `source_discovery`, used/limit `1/1`; no output file |
| Graphify code refresh | `graphify update .` | 1,768 nodes, 3,184 edges, 152 communities; generated output kept uncommitted |
| Graph health | `graphify diagnose multigraph --graph graphify-out/graph.json --directed --json` | No dangling endpoints, self loops, duplicate edges, or same-endpoint collapses; directed graph retained all 3,184 edges |

## Risks and unresolved questions

- The limit accounts deterministic analyzer work, not filesystem latency, CPU time, memory, or a
  MetaEditor compile/Strategy Tester outcome.
- The current private plugin installation is not rebuilt or reinstalled by this source change; a
  release/package step is still needed before a separate Codex installation consumes it.
- Graphify's terminal update refreshes code structurally but reports that changed prose requires
  semantic extraction. No Gemini/Google semantic-extraction credential was configured in this session;
  current source and tests remain the authority for this feature.

## Next objective

Design and validate a separate compiler-correlation gate against an actual local MetaEditor fixture,
without weakening the read-only analysis boundary.
