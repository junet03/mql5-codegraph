# ADR-0006: Analyzer-wide deterministic work budget

- Status: Accepted
- Date: 2026-07-29
- Owners: Project maintainers

## Context

MQL5 CodeGraph is a local, trusted-input static analyzer, but the parser and resolver contain several
valid source shapes whose work can amplify: function-range membership checks, nested argument scans,
binding-list scans, and ambiguous call-target fan-out. Existing transport deadlines and Intelligence
Kernel traversal bounds do not limit the initial construction of a graph.

## Decision

- Give every canonical analysis request one deterministic `AnalysisBudget` that is consumed by source
  discovery, lexing, parsing, resolution, and runtime enrichment.
- Use a default limit of 1,000,000 work units; accept an explicit limit from 1 through 10,000,000 for
  a single local operation.
- Stop before the next unit would exceed the limit and raise the stable
  `analysis_budget_exceeded` result with phase, consumed work, and limit.
- Return or publish only complete graphs. CLI does not write an output graph on exhaustion; dashboard
  and MCP retain their last valid graph/snapshot.
- Expose the optional limit only where analysis starts: direct library call, `analyze` CLI command,
  dashboard analysis request/startup, and MCP `index_project`.

## Consequences

- Positive: every supported route through canonical analysis has a deterministic finite ceiling.
- Positive: an agent can distinguish a retryable resource limit from malformed MQL5 input and will not
  receive partial graph evidence.
- Positive: MCP snapshot replacement remains atomic under budget exhaustion.
- Cost: normal analysis performs accounting at structural iteration boundaries and callers must choose
  a higher explicit limit for unusually large trusted projects.
- Limit: this is not a wall-clock guarantee, compiler parity claim, or authorization to ingest untrusted
  repositories in a hosted/multi-user environment.

## Guardrails

- Adapters must delegate accounting to the core analyzer; they may only validate the requested limit and
  translate the typed result into their established error envelope.
- Work budgets must not persist project data or change the read-only/no-network boundary.
- Successful analysis must preserve existing graph evidence, ordering, and deterministic serialization.
- New expensive parser/resolver paths must consume the same request budget and include a bounded regression.
