# Architecture

The pipeline is intentionally layered:

```text
AnalysisBudget -> source discovery -> lexer -> structural parser -> repository resolver
                 -> MQL5 runtime enrichment -> canonical CodeGraph
                 -> immutable GraphIndex -> IntelligenceKernel
                                         -> CLI/Web/experimental MCP adapters
```

Reference documents use a separate evidence pipeline:

```text
operator-owned PDFs -> ReferenceBuilder -> immutable JSONL + Markdown snapshot
                                      -> ReferenceCorpus -> CLI/experimental MCP reads
                                      -> optional external Graphify 0.9.x overlay
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

## Authoritative reference boundary

`ReferenceCorpus` is backend-neutral and independent of `CodeGraph` and `IntelligenceKernel`. Its
content-addressed snapshot owns document hashes, authority declarations, physical page records,
outline-derived sections, page-to-character spans, extraction states, and canonical file hashes. Search
and excerpt semantics live in the reference core; CLI and MCP only normalize arguments and project results.

A corpus build stages every file, validates page/section coverage and hashes, then renames the immutable
snapshot and atomically replaces `current.json`. This pointer-based publication works on Windows without
replacing a non-empty active directory. Failed builds and invalid MCP attachments keep the prior snapshot.

The MCP process owns `ProjectSession` and `ReferenceSession` independently. Each has a revision and
fingerprint. A response cannot promote reference content to a project edge, and an agent may require
`expected_corpus_fingerprint` on follow-up calls.

Graphify is not imported or vendored by the core. The explicit CLI adapter invokes an observed 0.9.x
executable with `shell=False`, an explicit model backend/processing boundary, a timeout, isolated output,
and a child environment limited to runtime variables plus the selected backend's endpoint, model, and
credential variables. The version probe receives no provider credentials. Its artifacts are tied to one
corpus fingerprint and always labeled
`semantic_overlay_inference`. They never enter `ReferenceCorpus` or `CodeGraph`.

## Analysis work budget

Each graph construction owns one deterministic `AnalysisBudget`. It is consumed across discovery,
lexing, parsing, resolution, and runtime enrichment; exhaustion returns no graph. The default is
1,000,000 units, and a local operator may explicitly request 1 through 10,000,000 for one analysis.
This is a logical-work boundary, not a wall-clock guarantee. CLI never writes a partial graph, while
dashboard and MCP publish replacements only after the full analysis succeeds.

## Adapter and compatibility matrix

| Surface | Contract | Role |
| --- | --- | --- |
| Direct Python | Intelligence contract `1.0.0` | Authoritative normalized result |
| `intelligence` CLI namespace | Intelligence contract `1.0.0` | Argument normalization and JSON/error projection |
| `/api/v1/intelligence/*` | Intelligence contract `1.0.0` | Route defaults, HTTP status, JSON projection |
| `compiler-evidence` CLI | Compiler evidence contract `1.0.0` | Read-only correlation of a supplied log with a saved graph |
| Reference CLI namespace | Reference contract `1.0.0` | Offline build, validation, cited search, excerpt, and explicit Graphify adapter |
| MCP stdio beta | Experimental 13-tool projection | Independent trusted project/reference snapshots and structured tool errors |
| Legacy CLI and unversioned HTTP | Frozen historical shapes | Exact compatibility projector over the same snapshot |
| GraphML and representation exporters | Canonical graph schema | Transform representation without reinterpreting semantics |

The Intelligence contract and canonical graph schema are versioned independently. Patch releases preserve
valid shapes and semantics. Minor Intelligence versions may add optional fields. Changed defaults, ranking,
errors, removed fields, or incompatible behavior require a new major and a new `/api/vN` HTTP prefix.

The experimental MCP tool names are not part of the stable compatibility promise. Its official SDK dependency
is optional and capped below 2.x so a major protocol-runtime migration remains deliberate.

The stdio entry point writes machine-readable lifecycle events to stderr, never stdout. `starting`
identifies the process/runtime versions, `stopped` with `stdio_eof` identifies a clean host-side stdin
closure, and `crashed` identifies an unhandled server exception. If a `starting` record has no matching
terminal event, the available evidence supports external termination rather than a server-classified
shutdown. Respawning and reinitializing a dead child transport remain responsibilities of the MCP host;
any new server process begins without the prior in-memory snapshot.

## Evidence and uncertainty

Every relationship, path hop, and diagnostic result retains an `EvidenceReference` with origin,
confidence, source location when known, and an explicit state:

- `extracted`: visible structural source evidence;
- `resolved`: a repository resolver linked an extracted reference;
- `runtime`: documented MetaTrader runtime behavior, never a direct source call;
- `inferred`: a weaker structural hypothesis that remains visibly distinct.

Cross-domain evidence is also explicitly classified:

- `code_graph`: canonical project-source relationships and diagnostics;
- `reference_document`: cited text from one hashed document/section/physical-page span;
- `external_compiler_evidence`: one supplied bounded compiler-log observation;
- `semantic_overlay_inference`: disposable model-derived Graphify navigation.

These classes may support one answer but are never merged into one identity or promoted into another
class.

Freshness state is separately `available`, `stale`, `unavailable`, or `unknown`. Locationless evidence is
always unknown. Without a protected evidence probe, a stored source location remains unknown rather than
being promoted to available.

## Compiler evidence

Compiler evidence is a separate, immutable result that pairs an operator-supplied bounded MetaEditor log
with one graph identity and a fresh source observation. It records `current`, `stale`, or `incomplete`
state independently of static graph diagnostics. A compiler finding may identify a graph declaration only
when its project-contained file and line exactly match that declaration; text resembling a symbol name is
never enough. The core does not launch MetaEditor, persist a log, add edges or diagnostics to `CodeGraph`,
or claim that a successful compile proves terminal or trading behavior.

## Structural context packages

Context packages use provider-neutral `structural_record_v1` units. Each node summary, relationship,
diagnostic, or ambiguity alternative costs one unit. Relationships are packed atomically with both endpoint
summaries. Ranking and omission summaries are deterministic, and no package may exceed its declared budget.
