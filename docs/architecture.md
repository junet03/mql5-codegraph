# Architecture

The pipeline is intentionally layered:

```text
source discovery -> lexer -> structural parser -> repository resolver
                 -> MQL5 runtime enrichment -> canonical CodeGraph
                 -> immutable GraphIndex -> IntelligenceKernel
                                         -> CLI/Web/private MCP adapters
```

The lexer owns source fidelity and recovery. The parser extracts declarations and call sites without
requiring complete source. The resolver works across all parsed files, resolves includes and symbols,
and records ambiguity rather than inventing certainty. Runtime enrichment adds terminal-driven event
edges with `origin=runtime`. Exporters depend only on the canonical graph model.

Every relationship contains an origin and confidence. `calls` means a visible call expression;
`runtime_dispatches` means the terminal invokes a valid event entry point; `may_trigger_event` records
a documented runtime consequence rather than a direct call.

## Authoritative intelligence boundary

The canonical `CodeGraph` owns deterministic entities, relationships, diagnostics, metadata, and
serialization. It does not own transport defaults or presentation. `GraphIndex` derives immutable sorted
lookup and adjacency tables from one graph snapshot. `IntelligenceKernel` owns:

- ambiguity-preserving matching;
- bounded context and impact traversal;
- evidence-ranked directed path search;
- diagnostic projection;
- deterministic structural context packaging;
- contract version negotiation, completion semantics, and stable normalized errors.

One kernel instance observes one immutable graph identity. `DashboardState` atomically publishes the graph,
kernel, repository root, and revision, so a request cannot mix snapshots during reload.

Analysis semantics must not be implemented in CLI, Web, or the MCP adapter. Adapters may normalize
transport-derived defaults, map HTTP status or CLI exit codes, and preserve legacy projections.

## Adapter and compatibility matrix

| Surface | Contract | Role |
| --- | --- | --- |
| Direct Python | Intelligence contract `1.0.0` | Authoritative normalized result |
| `intelligence` CLI namespace | Intelligence contract `1.0.0` | Argument normalization and JSON/error projection |
| `/api/v1/intelligence/*` | Intelligence contract `1.0.0` | Route defaults, HTTP status, JSON projection |
| Private MCP stdio alpha | Experimental eight-tool projection | One trusted in-memory snapshot and structured tool errors |
| Legacy CLI and unversioned HTTP | Frozen historical shapes | Exact compatibility projector over the same snapshot |
| GraphML and representation exporters | Canonical graph schema | Transform representation without reinterpreting semantics |

The Intelligence contract and canonical graph schema are versioned independently. Patch releases preserve
valid shapes and semantics. Minor Intelligence versions may add optional fields. Changed defaults, ranking,
errors, removed fields, or incompatible behavior require a new major and a new `/api/vN` HTTP prefix.

The private MCP tool names are not part of the stable compatibility promise. Its official SDK dependency
is optional and capped below 2.x so a major protocol-runtime migration remains deliberate.

## Evidence and uncertainty

Every relationship, path hop, and diagnostic result retains an `EvidenceReference` with origin,
confidence, source location when known, and an explicit state:

- `extracted`: visible structural source evidence;
- `resolved`: a repository resolver linked an extracted reference;
- `runtime`: documented MetaTrader runtime behavior, never a direct source call;
- `inferred`: a weaker structural hypothesis that remains visibly distinct.

Freshness state is separately `available`, `stale`, `unavailable`, or `unknown`. Locationless evidence is
always unknown. Without a protected evidence probe, a stored source location remains unknown rather than
being promoted to available.

## Structural context packages

Context packages use provider-neutral `structural_record_v1` units. Each node summary, relationship,
diagnostic, or ambiguity alternative costs one unit. Relationships are packed atomically with both endpoint
summaries. Ranking and omission summaries are deterministic, and no package may exceed its declared budget.
