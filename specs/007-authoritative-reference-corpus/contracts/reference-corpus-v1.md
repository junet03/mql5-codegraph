# Reference Corpus Contract v1

## Layout

```text
<corpus-root>/
├── current.json
└── snapshots/
    └── <64 lowercase hex corpus fingerprint>/
        ├── manifest.json
        ├── index.md
        ├── records/
        │   ├── outlines.jsonl
        │   ├── pages.jsonl
        │   └── sections.jsonl
        └── documents/
            └── <source-id>/
                ├── index.md
                └── sections/
                    └── <section-id>.md
```

`current.json` is the publication boundary. Readers must not discover or select a snapshot by directory
enumeration. They validate the pointer, manifest hash, snapshot path confinement, complete flag, supported
major version, file hashes, source/page/section invariants, and corpus fingerprint before use.

## Source declaration file

The optional input JSON has this shape:

```json
{
  "contract_version": "1.0.0",
  "sources": [
    {
      "source_id": "mql5-reference",
      "filename": "mql5.pdf",
      "title": "MQL5 Reference",
      "authority": "normative",
      "role": "language_reference",
      "official_url": "https://www.mql5.com/files/docs/mql5.pdf",
      "expected_sha256": null
    }
  ]
}
```

When omitted, recognized official filenames receive built-in metadata and other `*.pdf` files receive a
stable source ID with `unclassified` authority. Discovery is non-recursive and rejects symlinks.

## Canonical identity

`corpus_fingerprint` is lowercase SHA-256 over canonical JSON containing:

- contract and normalization versions;
- structure and text extractor names and observed versions;
- effective build limits that affect sectioning;
- sorted source declarations;
- actual source SHA-256 and byte size.

Absolute paths, timestamps, hostnames, usernames, staging names, and output paths are excluded.

`manifest.json` inventories every other canonical snapshot file with byte size and SHA-256. The pointer
stores the manifest hash. Files use UTF-8, LF newlines, sorted JSON keys, and deterministic ordering.

## Markdown evidence markers

Each section begins with generated front matter:

```yaml
---
reference_contract: "1.0.0"
corpus_fingerprint: "<sha256>"
source_id: "mql5-reference"
source_sha256: "<sha256>"
authority: "normative"
section_id: "mql5-reference-order-send-p123-p126"
physical_pages: [123, 126]
evidence_class: "reference_document"
---
```

The body contains breadcrumbs, previous/next links, and explicit `## Physical PDF page N` markers before
each page's normalized text. Empty or failed pages contain a warning marker, never fabricated content.

## Validation failures

Stable failure codes:

- `invalid_reference_root`
- `reference_not_built`
- `invalid_reference_pointer`
- `unsupported_reference_contract`
- `reference_snapshot_outside_root`
- `reference_snapshot_incomplete`
- `reference_integrity_failed`
- `invalid_source_manifest`
- `invalid_reference_source`
- `reference_dependency_missing`
- `reference_build_failed`
- `reference_source_changed`
- `reference_limit_exceeded`

A failure must not update `current.json` or an active reference session.

## Authority rules

Default ranks are:

1. `normative` — official language/API reference
2. `explanatory` — general programming book
3. `specialist` — topic-scoped book or guide
4. `unclassified` — no implicit authority

Authority is a relevance tie-breaker, not permission to return an unrelated result. A result always
displays its tier.
