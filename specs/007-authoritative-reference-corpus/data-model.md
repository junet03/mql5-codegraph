# Data Model: Authoritative MQL5 Reference Corpus

## Contract versions

- Corpus pointer and manifest: `1.0.0`
- Search/status/excerpt response: `1.0.0`
- Graphify overlay manifest: `1.0.0`

Readers accept only the supported major version. Minor additions must be optional and deterministic.

## Source Declaration

Operator-authored metadata read before extraction.

| Field | Type | Rules |
| --- | --- | --- |
| `source_id` | string | Required portable slug; unique; 1–64 lowercase ASCII characters/digits/hyphens |
| `filename` | string | Required basename ending in `.pdf`; no path separators or symlinks |
| `title` | string | Required non-empty display title |
| `authority` | enum | `normative`, `explanatory`, `specialist`, or `unclassified` |
| `role` | string | Required stable descriptive role; does not alter authority by itself |
| `official_url` | string/null | Optional HTTPS provenance URL; never fetched by the builder |
| `expected_sha256` | string/null | Optional 64-character lowercase SHA-256 used to pin an edition |

Known filenames may receive documented defaults, but unknown sources default to `unclassified`.

## Reference Source

Immutable source result recorded in a complete snapshot.

| Field | Type | Rules |
| --- | --- | --- |
| declaration fields | values | Canonicalized from the source declaration |
| `sha256` | string | Hash before extraction and verified again after extraction |
| `byte_size` | integer | Non-negative |
| `page_count` | integer | Positive and within configured bound |
| `outline_entries` | integer | Non-negative |
| `section_count` | integer | Positive |
| `page_states` | object | Counts whose sum equals `page_count` |
| `warnings` | array[string] | Sorted, stable warning codes |

## Reference Page

One physical PDF page. Page records are stored in source/physical-page order.

| Field | Type | Rules |
| --- | --- | --- |
| `source_id` | string | Existing source |
| `physical_page` | integer | One-based, continuous, unique within source |
| `printed_label` | string/null | PDF label only; never replaces physical page |
| `state` | enum | `text`, `empty`, or `extraction_failed` |
| `raw_text` | string | Extractor output normalized only for Unicode/newlines |
| `normalized_text` | string | Deterministic search/display normalization |
| `warnings` | array[string] | Includes unsupported/lossy conditions |

Every page appears exactly once, including empty and failed pages.

## Outline Entry

Navigation metadata, including parent entries that do not own a separate content span.

| Field | Type | Rules |
| --- | --- | --- |
| `outline_id` | string | Stable content-derived identity |
| `source_id` | string | Existing source |
| `title` | string | Normalized non-empty title or explicit untitled marker |
| `path` | array[string] | Ordered ancestry including this title |
| `depth` | integer | Zero-based |
| `physical_page` | integer/null | One-based destination or unresolved |
| `state` | enum | `resolved` or `unresolved` |

## Reference Section

One non-overlapping content span covering one or more consecutive pages.

| Field | Type | Rules |
| --- | --- | --- |
| `section_id` | string | Stable source/path/range/occurrence-derived slug |
| `source_id` | string | Existing source |
| `title` | string | Chosen deepest outline title or synthetic title |
| `path` | array[string] | Navigation ancestry |
| `aliases` | array[string] | Sorted unique alternate same-page outline titles |
| `physical_page_start/end` | integer | Inclusive valid range |
| `text` | string | Concatenated normalized page text |
| `page_spans` | array[object] | Per-page half-open character spans into `text` |
| `warnings` | array[string] | Union of section/page limitations |
| `markdown_path` | string | Portable snapshot-relative POSIX path |
| `content_sha256` | string | Hash of normalized text and provenance envelope |

For a source, section page ranges are ordered, do not overlap, and cover every physical page exactly once.

## Corpus Configuration

| Field | Type | Rules |
| --- | --- | --- |
| `normalization_version` | string | Exact deterministic algorithm version |
| `extractors` | object | `structure` and `text`, each with a package name and observed version |
| `max_pdf_bytes` | integer | Positive |
| `max_pages_per_source` | integer | Positive |
| `max_pages_per_section` | integer | 1–256 |

## Reference Corpus Manifest

| Field | Type | Rules |
| --- | --- | --- |
| `contract_version` | string | `1.0.0` |
| `corpus_fingerprint` | string | SHA-256 of canonical source/config/extractor identity |
| `configuration` | object | Canonical corpus configuration |
| `sources` | array[Reference Source] | Sorted by `source_id` |
| `counts` | object | Documents, pages, sections, and warnings |
| `files` | array[object] | Relative path, byte size, SHA-256; excludes manifest itself |
| `complete` | boolean | Must be `true` before publication |

Canonical files are UTF-8 with LF line endings. JSON keys are sorted, compact JSONL has one trailing LF,
and no timestamp or absolute workstation path participates in canonical identity.

## Corpus Pointer

The only mutable publication record.

| Field | Type | Rules |
| --- | --- | --- |
| `contract_version` | string | `1.0.0` |
| `corpus_fingerprint` | string | Must match snapshot directory and manifest |
| `snapshot_path` | string | `snapshots/<lowercase-hex>` only |
| `manifest_sha256` | string | Hash of the complete snapshot manifest |

## Reference Search Result

| Field | Type | Rules |
| --- | --- | --- |
| corpus identity | object | Contract/fingerprint |
| source evidence | object | Source ID/title/hash/authority/URL |
| section evidence | object | ID/path/full page range/relative Markdown path |
| citation | object | Physical page start/end and half-open section character offsets |
| `excerpt` | string | Bounded exact slice of normalized section text |
| `score` | object | Explainable integer/boolean components |
| completion | object | Exhaustive flag, candidates, returned, limit, truncated, no-match |

## Reference Session Snapshot

In-memory state containing validated corpus metadata and search records.

| Field | Type | Rules |
| --- | --- | --- |
| `root` | Path | Resolved local corpus root; response path is operator-visible but not canonical |
| `revision` | integer | Starts at 1; increments only after a valid different load |
| `corpus_fingerprint` | string | Active immutable identity |
| `corpus` | Reference Corpus | Shared protocol-neutral reader |

### Session transitions

`not_loaded → validating → loaded`

- Validation failure returns to the prior `not_loaded` or `loaded` state unchanged.
- Loading the same valid fingerprint returns `reused=true` and keeps the revision.
- Loading a different valid fingerprint increments the revision atomically.

## Semantic Overlay

| Field | Type | Rules |
| --- | --- | --- |
| `contract_version` | string | `1.0.0` |
| `overlay_fingerprint` | string | Corpus fingerprint + Graphify version + normalized invocation |
| `corpus_fingerprint` | string | Existing complete corpus |
| `producer` | object | `graphify`, observed version, supported range |
| `processing_boundary` | enum | `local` or `remote` |
| `backend` | string | Explicit; `local` currently requires `ollama` |
| `model` | string/null | Explicit override if supplied |
| `artifacts` | array[object] | Relative paths and hashes for accepted output |
| `evidence_class` | string | Always `semantic_overlay_inference` |
| `complete` | boolean | Must be true before overlay pointer publication |

Overlay publication state mirrors corpus publication but uses a separate operator-selected root. It never
changes a corpus pointer or a project graph.
