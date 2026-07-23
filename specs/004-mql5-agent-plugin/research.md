# Research: MQL5 Agent Plugin and MCP Alpha

## Official MCP SDK

**Decision**: Use the official Python MCP SDK v1 line through the optional requirement
`mcp>=1.28.1,<2`.

**Rationale**: The SDK supplies protocol negotiation, stdio framing, tool schema generation,
structured output, and client test utilities. The upper bound prevents the announced v2 breaking
release from silently changing the adapter.

**Alternative rejected**: A hand-written JSON-RPC server would avoid dependencies but would duplicate
protocol behavior and create a larger compatibility/security surface.

## Snapshot lifecycle

**Decision**: Keep exactly one active graph/kernel snapshot in memory. `index_project` constructs the
replacement completely before atomically publishing it.

**Rationale**: This preserves the existing Web snapshot pattern, avoids persistent private project
data, and guarantees that failed re-indexing cannot corrupt the usable session.

**Alternative rejected**: Saving graph JSON automatically would turn a read-only agent workflow into
a filesystem-writing operation and require retention/path policy.

## Tool granularity

**Decision**: Expose session tools (`project_status`, `index_project`) plus direct projections for the
six Intelligence Kernel operations.

**Rationale**: One-to-one projection makes conformance testable and prevents tool-specific semantic
drift. Skills can compose the tools for architecture and change-impact workflows.

**Alternative rejected**: Convenience tools such as `find_callers` would either duplicate filtering
logic or hide direction and ambiguity. Agents can call `get_context` with `incoming` or `outgoing`.

## Plugin distribution

**Decision**: Store the plugin and repo-local marketplace in the private source repository.

**Rationale**: Internal agents can install one versioned bundle, while plugin source, skills, and MCP
configuration receive the same review and Git history as the engine.

**Alternative rejected**: A personal unversioned plugin outside the repository would be quicker but
would drift from the engine and be harder to reproduce or share.

## Security posture

**Decision**: Local stdio only, no HTTP listener, no network calls, no source reads beyond the explicit
index operation, no source-content tool in v0.1, and all tools annotated non-destructive/open-world false.

**Known limitation**: Indexing trusted local repositories can still consume unbounded analysis time on
adversarial input. Hosted or untrusted ingestion remains blocked pending analyzer work budgets.
