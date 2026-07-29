# Known Limitations and Roadmap

The MVP is a tolerant structural analyzer, not a MetaEditor compiler frontend. It can correlate an
operator-supplied, supported MetaEditor log with a current graph, but it does not start MetaEditor, create
compiler artifacts, or claim compiler/runtime parity.

- Macro bodies and conditional compilation are recorded but not fully expanded.
- Overload resolution uses scope and arity hints, not complete MQL5 type inference.
- Template-like constructs and complex declarators may be recovered only partially.
- Standard-library calls are represented as external nodes unless their source is included in scope.
- Dynamic dispatch, function pointers, reflective indicator loading, and runtime-generated names are
  not resolved statically.

## Evidence and runtime guarantees

- A stored source location identifies where evidence was observed during analysis; it does not prove that
  the file still exists or has not changed.
- CLI and HTTP currently do not configure a filesystem freshness probe. Located evidence therefore reports
  `unknown/probe_not_configured`; locationless evidence reports `unknown/location_missing`.
- `runtime` edges model documented MetaTrader dispatch or consequences. They do not prove that a handler
  executed in a particular terminal session.
- `inferred` edges remain hypotheses with explicit origin and confidence. Path and context results never
  promote them to extracted or resolved facts.
- Static absence of a path is meaningful only when the eligible bounded search completes. Depth or expansion
  exhaustion is reported as incomplete, not as proof that symbols are disconnected.
- Ambiguous names and unresolved external nodes remain visible. The kernel does not silently choose one
  equal-ranked interpretation.

## Context and performance limits

- `structural_record_v1` is a deterministic graph-record budget, not a model tokenizer estimate and not a
  promise about downstream prompt size.
- Context packages return summaries and evidence metadata, not raw source text.
- The one-second target is an opt-in benchmark result for the documented local machine and fixed synthetic
  workload. It is not a latency guarantee for every repository or hardware profile.
- Analysis and normalized intelligence remain local, single-user, read-only operations over one published
  graph snapshot.

## Release security boundary

- The local dashboard is intentionally unauthenticated and loopback-only. Network binds are rejected rather
  than treated as an operator opt-in.
- Socket reads are bounded by both a two-second idle timeout and a ten-second absolute request-read deadline.
  This controls slow-drip slot retention but does not impose a wall-clock deadline on completed analysis work.
- Include resolution rejects absolute, drive-qualified, UNC, and canonically escaping targets before a
  filesystem existence probe. Explicit include roots remain approved read boundaries.
- Saved graph metadata cannot authorize source reads. The source viewer requires an explicit active root.
- Parser range membership, nested-argument scans, binding-list scans, and ambiguous call-edge fan-out
  consume the analyzer-wide deterministic work budget. Exhaustion prevents a partial graph from being
  returned or published, but it is not a universal wall-clock guarantee or a performance claim.
- The private MCP plugin inherits this local trusted-input boundary. It keeps one in-memory snapshot and
  exposes bounded Intelligence Kernel operations plus a bounded initial analysis operation. Hosted or
  multi-user ingestion remains out of scope pending broader resource, tenancy, and security design.
- The stdio server reports bounded lifecycle evidence to stderr, but it cannot respawn itself after its
  host transport or process is gone. A host-side `Transport closed` recovery requires a new MCP process,
  initialization, and re-index; the prior in-memory snapshot is intentionally not restored.
- Compiler correlation accepts only a <=2 MiB log explicitly supplied under the selected trusted root. It
  supports UTF-8 and BOM-marked UTF-16 logs with the documented English
  `Result: <errors> errors, <warnings> warnings` summary and bounded error/warning records; unsupported
  locales or variants return incomplete evidence rather than a success claim. MetaEditor process control
  remains out of scope.

Planned milestones include a formal Tree-sitter MQL5 grammar, richer type inference, incremental indexing,
Graphify/Neo4j adapters, protected evidence freshness probes, MetaEditor process-control review, and a
real operator-log corpus. The experimental private MCP adapter now exists; a stable public MCP surface remains deferred
until its contracts can preserve the same versioning, evidence, ambiguity, completion, and resource-budget
semantics.
