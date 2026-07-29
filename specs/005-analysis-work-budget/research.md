# Research: Analyzer Work Budget

## Deterministic work rather than elapsed time

**Decision**: Enforce a finite, deterministic work-unit budget rather than a wall-clock timeout.

**Rationale**: The local analyzer must run predictably on different Windows machines, and a deadline
can interrupt at different logical points depending on load. Accounting at source discovery, lexing,
parsing, resolution, and runtime enrichment makes the stopping condition repeatable and testable.

**Alternatives considered**:

- Wall-clock timeout: rejected because it is scheduler and hardware dependent, and cannot prove bounded
  logical work.
- Adapter-only timeout: rejected because direct library and dashboard callers would remain unbounded.
- Fix only the four known hot paths: rejected because new or unmeasured paths could bypass the safety
  contract.

## Typed exhaustion before publication

**Decision**: Raise one typed core exhaustion result carrying `phase`, `work_used`, and `work_limit`.

**Rationale**: The graph must remain all-or-nothing. The existing MCP and dashboard already construct a
replacement before publication; a typed exception lets each adapter keep the previous complete state
without treating an expected resource limit as a malformed source failure.

**Alternatives considered**:

- Return a partial graph with warnings: rejected because agents could reason over incomplete call or
  include relationships.
- Convert exhaustion to a generic `ValueError`: rejected because operators cannot tell a retryable limit
  from a parser/input failure.

## Budget configuration and compatibility

**Decision**: Use a default of 1,000,000 work units and accept requested limits from 1 through
10,000,000 units, validated before analysis. Keep successful default calls source-compatible.

**Rationale**: Current callers must gain the safety boundary without changing invocation syntax, while
tests, CI, and operators need small limits to prove stopping behavior. One million units leaves
substantial room above the supported fixture baseline, while ten million keeps an explicitly requested
local run finite. A finite upper validation bound prevents an interface from reintroducing unbounded
work accidentally.

**Alternatives considered**:

- Require every caller to provide a limit: rejected as an avoidable breaking change.
- Store a project-level setting: rejected because persistence is explicitly out of scope and would make
the read-only agent workflow write to user projects.

## Adapter contract

**Decision**: Expose the optional limit on analysis-starting interfaces only: library, `analyze` CLI,
dashboard state, and MCP `index_project`. Query-only Intelligence Kernel operations keep their existing
bounds and do not receive the analysis budget.

**Rationale**: The budget protects graph construction; context/impact/path queries are already governed
by their own explicit traversal bounds. This keeps the MCP adapter thin and avoids semantic duplication.

**Alternatives considered**:

- Add budget to every MCP tool: rejected because it confuses analysis work with query traversal bounds.
- Start a new MCP tool: rejected because `index_project` is the existing lifecycle boundary.
