# ADR-0008: Keep authoritative references page-aware and Graphify optional

**Status**: Accepted

**Date**: 2026-07-30

## Context

MQL5 CodeGraph can explain a selected project's source relationships, but it does not contain the official
language and API contracts needed to answer many MQL5 questions. Users may already own local official PDF
references. Direct PDF reads are slow and lose stable citations, while committing the documents or
derived Markdown would create redistribution and repository-size problems.

Graphify can build a useful semantic graph from documents, but its document path uses a model backend and
its pre-1.0 output is inferred navigation rather than normative evidence. Folding that output into the
canonical `CodeGraph` would erase provenance and couple the core to a specific adapter.

## Decision

We will:

1. Build a separate backend-neutral `ReferenceCorpus` from explicitly selected, user-owned local PDFs.
2. Preserve source hashes, physical page records, outline hierarchy, extraction states, non-overlapping
   section ranges, and exact excerpt spans.
3. Publish deterministic JSON/JSONL and linked Markdown as immutable content-addressed snapshots, switching
   only an atomic `current.json` pointer after complete validation.
4. Use deterministic bounded lexical search as the offline normative retrieval path, with authority as an
   explicit relevance tie-breaker.
5. Keep reference-document evidence, source-code graph evidence, and external compiler evidence as
   independent identities and classes.
6. Expose only status, search, and excerpt reads to agents after an operator attaches a complete snapshot.
7. Integrate Graphify only as an externally installed 0.9.x CLI adapter invoked explicitly outside MCP.
   Its output is isolated, versioned, tied to a corpus fingerprint, and labeled semantic inference.
8. Require an explicit processing boundary and remote-data authority before Graphify may send normalized
   documentation to a remote model.
9. Ship no third-party PDF bytes or generated corpus data in the source distribution.
10. Use pypdf for structural metadata and pypdfium2/PDFium for page text; record both observed versions
    in corpus identity so extractor upgrades cannot silently reuse an old snapshot.

## Consequences

### Positive

- Answers can cite exact document bytes and physical pages.
- Core build/search work remains offline and usable without Graphify or an MCP installation.
- Failed builds and overlays cannot replace the last valid snapshot.
- Windows and Linux use the same relative canonical identities.
- Graphify can evolve or be replaced behind a conformance-tested adapter.
- Agent answers can distinguish project facts, compiler evidence, reference statements, and semantic
  discovery.

### Negative

- v1 PDFium text layout remains lossy for some tables, code formatting, columns, and spaced glyphs.
- Local corpora can consume substantial disk space and must be rebuilt when sources/extractor policy change.
- Lexical scans trade some semantic recall for determinism.
- Graphify document extraction requires a separately operated model backend and explicit privacy choices.

### Deferred

- OCR and layout reconstruction
- hosted/multi-user corpora
- dashboard corpus authoring
- embeddings or alternate retrieval backends
- Graphify 1.x compatibility

## Attribution and licensing

MQL5 CodeGraph remains MIT-licensed and independent. Graphify is an external Apache-2.0 project and is not
vendored by this decision. User-supplied documents and their local derivatives remain subject to their
respective rights and terms.
