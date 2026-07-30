# Implementation Plan: Authoritative MQL5 Reference Corpus

**Branch**: `codex/mql5-agent-plugin` | **Date**: 2026-07-30 |
**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-authoritative-reference-corpus/spec.md`

## Summary

Add an optional `reference` package that converts operator-owned, text-bearing PDF references into
immutable page-aware corpus snapshots. Each snapshot contains deterministic JSONL records and a linked
Markdown wiki, retains source hashes and physical page spans, and supports bounded authority-aware lexical
search through one backend-neutral core. The CLI builds and queries snapshots; the experimental MCP adapter may
attach and query an already-built snapshot without write, shell, package-install, or network authority.
An isolated, explicit CLI adapter may invoke an externally installed Graphify 0.9.x to produce a disposable
semantic overlay, but the overlay never becomes normative evidence or a core dependency.

## Technical Context

**Language/Version**: Python 3.11+ with portable `pathlib` filesystem behavior

**Primary Dependencies**: Python standard library; optional `pypdf>=6.10,<7` for outlines/page labels
and `pypdfium2>=5.7.1,<6` for streaming text extraction; existing optional `mcp>=1.28.1,<2`; external
Graphify CLI 0.9.x only for explicit overlay generation

**Storage**: Immutable local directories containing canonical JSON/JSONL and UTF-8 Markdown; atomic
`current.json` pointer; no database, remote object store, or repository-local corpus

**Testing**: `unittest`, deterministic in-test PDF fixtures, fake Graphify executable, CLI/MCP conformance,
full repository test discovery, `compileall`, package metadata checks, and opt-in real-corpus smoke

**Target Platform**: Local Windows and Linux filesystems; CPython 3.11 and the repository's supported
Python matrix

**Project Type**: Python library plus CLI, local MCP adapter, plugin guidance, and public documentation

**Performance Goals**: Stream one page at a time during extraction; search the 10,021-page baseline corpus
without remote calls; default CLI/MCP result bounds of 20 items and 1,200 excerpt characters; Graphify
subprocess bounded by timeout and explicit concurrency

**Constraints**: No third-party PDF redistribution; zero network for build/search/status/excerpt; no OCR
claim in v1; deterministic portable canonical output; failed publication preserves last valid snapshot;
agent adapter stays read-only; Graphify inference remains separate and explicitly authorized

**Scale/Scope**: Three official references, 10,021 physical pages, roughly 5,000 outline-derived sections,
up to 20,000 pages per source and 50 search results per request in v1

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **MQL5 semantic fidelity — PASS**: reference evidence describes platform contracts but does not add or
  infer parser semantics. Unsupported PDF extraction is surfaced as a limitation.
- **Evidence-backed graph — PASS**: document excerpts retain source hash, authority, section, page, and
  character spans. Graphify edges are labeled overlay/inferred evidence and never copied into `CodeGraph`.
- **Deterministic CLI contracts — PASS**: corpus and query contracts are versioned; JSON is stable; errors
  use stderr and non-zero exit codes; canonical paths are relative.
- **Test corpus before claims — PASS**: runtime-generated PDF fixtures and golden search cases cover
  hierarchy, duplicate titles, empty/failed input, authority, publication, and adapter failures.
- **Small composable core — PASS**: `reference` is protocol-neutral; CLI/MCP call it; Graphify is an
  external adapter and is not imported by the parser, indexer, or Intelligence Kernel.
- **Technical constraints — PASS**: workflows are local-first, generated data is ignored, corpus inputs
  are read-only, and no cloud service is required.
- **Workflow gate — PASS**: specification, plan, contracts, data model, ADR, tasks, tests, and journal are
  produced in order.

Post-design re-check: **PASS**. The snapshot contract, separate reference session, and overlay manifest
preserve every gate without an exception.

## Project Structure

### Documentation (this feature)

```text
specs/007-authoritative-reference-corpus/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── reference-corpus-v1.md
│   ├── reference-corpus-v1.schema.json
│   └── reference-interfaces-v1.md
└── tasks.md
```

### Source Code (repository root)

```text
src/mql5_codegraph/
├── reference/
│   ├── __init__.py
│   ├── builder.py
│   ├── corpus.py
│   ├── graphify_adapter.py
│   └── models.py
├── cli.py
└── mcp/
    ├── server.py
    └── service.py

tests/
├── reference_corpus/
│   ├── helpers.py
│   ├── test_builder.py
│   ├── test_corpus.py
│   └── test_graphify_adapter.py
├── mcp_adapter/
│   ├── test_protocol.py
│   └── test_service.py
└── test_cli.py

docs/
├── reference-corpus.md
├── architecture.md
├── decisions/ADR-0008-authoritative-reference-corpus.md
└── project-journal/

plugins/mql5-codegraph-intelligence/
├── references/reference-corpus.md
└── skills/
```

**Structure Decision**: Extend the existing single Python distribution. The protocol-neutral
`mql5_codegraph.reference` package owns corpus identity, validation, extraction, search, and overlay
contracts. Existing CLI and MCP modules remain thin adapters. Generated corpora and Graphify output live
outside this tree and are never package data.

## Complexity Tracking

No constitutional violations require an exception.
