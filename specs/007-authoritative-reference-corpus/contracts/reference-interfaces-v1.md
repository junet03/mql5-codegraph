# Reference Interfaces Contract v1

## CLI

All commands support stable JSON with `--json`. Successful JSON goes to stdout. Structured errors go to
stderr and return exit code `1`; not-found search is a successful exhaustive response.

### Build

```text
mql5-codegraph reference build <input-dir> --output <corpus-root>
  [--sources <sources.json>]
  [--max-pdf-bytes N]
  [--max-pages-per-source N]
  [--max-pages-per-section N]
  [--json]
```

Does not fetch URLs or invoke Graphify. On success returns pointer path, corpus fingerprint, reuse flag,
counts, sources, and warnings.

### Status

```text
mql5-codegraph reference status <corpus-root> [--json]
```

Validates and reports the current snapshot identity, counts, authority catalog, and warnings.

### Search

```text
mql5-codegraph reference search <corpus-root> <query>
  [--limit N] [--max-excerpt-chars N] [--json]
```

Bounds: query 1–512 characters, limit 1–50, excerpt 80–4,000 characters. The response includes complete
ranking components and exhaustive/truncated metadata.

### Excerpt

```text
mql5-codegraph reference excerpt <corpus-root> <section-id>
  [--start N] [--max-chars N] [--json]
```

Returns an exact bounded section slice and the intersecting physical page range. Bounds: start ≥ 0 and
max chars 80–8,000.

### Graphify overlay

```text
mql5-codegraph reference graphify <corpus-root> --output <overlay-root>
  --graphify <executable>
  --backend <backend>
  --processing-boundary local|remote
  [--model <model>]
  [--allow-remote]
  [--timeout-seconds N]
  [--max-concurrency N]
  [--json]
```

- The executable must report a supported 0.9.x version.
- `local` permits only the explicit `ollama` backend.
- `remote` is refused unless `--allow-remote` is present.
- Invocation uses `shell=False`; source Markdown is read-only; output is isolated.
- Successful validation publishes a separate overlay pointer. Failure preserves any prior overlay.
- Overlay output is labeled `semantic_overlay_inference` and is never a reference citation.

## Core Python API

```text
build_reference_corpus(request) -> BuildResult
ReferenceCorpus.open(root) -> ReferenceCorpus
ReferenceCorpus.status() -> dict
ReferenceCorpus.search(query, *, limit, max_excerpt_chars) -> dict
ReferenceCorpus.excerpt(section_id, *, start, max_chars) -> dict
build_graphify_overlay(request) -> OverlayResult
```

Adapters may format results but must not reimplement validation, ranking, excerpt selection, or evidence
classification.

## MCP tools

The private local MCP alpha adds four read-only tools:

### `load_reference_corpus`

Arguments:

```json
{"corpus_root": "D:\\Knowledge\\mql5-reference"}
```

Loads only an existing complete corpus. Returns status plus `revision` and `reused`. It does not extract,
repair, update, enumerate, install, or invoke Graphify.

### `reference_status`

No arguments. Returns `not_loaded` with revision `0`, or the active validated snapshot summary.

### `search_reference`

Arguments:

```json
{
  "query": "OrderSend",
  "limit": 10,
  "max_excerpt_chars": 1200,
  "expected_corpus_fingerprint": null
}
```

The expected fingerprint precondition prevents stale-agent answers. Results match core/CLI semantics.

### `get_reference_excerpt`

Arguments:

```json
{
  "section_id": "mql5-reference-ordersend-p123-p126",
  "start": 0,
  "max_chars": 1200,
  "expected_corpus_fingerprint": null
}
```

Returns a bounded exact excerpt with page and content identity.

Stable adapter errors:

- `reference_not_loaded`
- `reference_snapshot_stale`
- `invalid_tool_arguments`
- core validation codes from the corpus contract, sanitized without a traceback

## Evidence composition rule

MCP clients and agent guidance must label:

- project source/code relationships as `code_graph`;
- supplied compiler results as `external_compiler_evidence`;
- corpus citations as `reference_document`;
- Graphify outputs as `semantic_overlay_inference`.

These classes may be cited together in an answer but must not be merged or promoted.
