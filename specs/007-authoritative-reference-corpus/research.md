# Research: Authoritative MQL5 Reference Corpus

## Decision 1: Keep source PDFs and generated corpora outside Git

**Decision**: Users supply lawful local PDF copies and an optional source manifest. The project ships
code, schemas, test generators, and documentation only. The default corpus output is an operator-selected
directory and is covered by ignore guidance.

**Rationale**: The three MQL5 documents are third-party publications. Converting them does not transfer
their rights to this MIT project, and generated Markdown remains derived content. Local inputs also permit
byte-level hashing and edition detection.

**Alternatives considered**:

- Commit PDFs or generated Markdown: rejected because it creates redistribution and repository-size risk.
- Download official URLs automatically: rejected for v1 because it adds network, terms, integrity, and
  availability concerns.
- Keep only PDFs and extract on every query: rejected because citations and search behavior would vary
  with extractor state and incur high latency.

## Decision 2: Use a hybrid pypdf/PDFium build extra

**Decision**: Add `reference = ["pypdf>=6.10,<7", "pypdfium2>=5.7.1,<6"]`. Import both only in the PDF
builder. Use pypdf for outlines, page labels, destination resolution, and encryption checks; stream each
page's full-Unicode text through pypdfium2/PDFium. Status, validation, search, excerpt, CLI, and MCP
operation over an existing corpus use the standard library.

**Rationale**: pypdf exposes the structure metadata needed by the page-aware contract. Its text extractor
was too slow and memory-intensive for the observed 10,021-page corpus. pypdfium2 ships portable PDFium
wheels, exposes bounded full-Unicode page extraction, and has liberal licensing; a 20-page local benchmark
took about 0.16 seconds versus about 41 seconds with pypdf. Both exact observed versions enter the corpus
fingerprint. PDF text still has no inherent semantic layout and image-only pages still require OCR, so v1
preserves extraction state and never invents layout or OCR content.

**Sources**:

- [pypdf outline handling](https://pypdf.readthedocs.io/en/stable/user/handling-outlines.html)
- [pypdf text extraction limits](https://pypdf.readthedocs.io/en/stable/user/extract-text.html)
- [pypdfium2 text-page API](https://pypdfium2.readthedocs.io/en/stable/python_api.html#text-page)
- [pypdfium2 package and licensing](https://pypi.org/project/pypdfium2/)

**Alternatives considered**:

- Reuse Graphify's PDF conversion: rejected as canonical extraction because its simple text conversion
  does not preserve the page-aware contract and its docs/PDF semantic pass requires a model.
- `pypdf` for both structure and text: portable but rejected after the full-corpus smoke showed
  impractical extraction time and high memory pressure.
- `pdfplumber`: faster than pypdf in the local benchmark but much slower than PDFium and adds a larger
  layout-analysis stack not needed by the v1 contract.
- Poppler command-line conversion: mature, but creates a system-binary dependency and makes portable CI
  and error normalization harder.
- OCR by default: rejected because it is expensive, nondeterministic across engines/models, and can
  silently corrupt identifiers.

## Decision 3: Partition all pages with outline-derived section starts

**Decision**: Treat physical pages as the evidence ledger. Flatten the nested outline while retaining
ancestry. For each unique physical start page, choose the deepest deterministic outline entry as the
content section and use all entries as navigation metadata. A section ends before the next unique start;
front matter and outline-free PDFs receive synthetic sections. Split spans above the configured maximum.

**Rationale**: This preserves hierarchy while assigning every physical page exactly once. It handles
multiple parent/child bookmarks on one page without duplicated evidence and makes empty or failed pages
visible. Stable IDs derive from source ID, outline path, physical range, and deterministic occurrence.

**Alternatives considered**:

- One Markdown file per PDF: too coarse for retrieval and citation.
- One file per physical page: exact but poor semantic navigation and creates more than 10,000 tiny files.
- One file per bookmark including parents: duplicates page content and inflates matches.
- Infer headings from typography: too layout-dependent for v1.

## Decision 4: Publish immutable versioned snapshots through an atomic pointer

**Decision**: Build in a sibling staging directory, validate it, rename it to
`snapshots/<corpus-fingerprint>/`, then atomically replace only `current.json`. Existing same-identity
snapshots are validated and reused; they are not mutated.

**Rationale**: Replacing a non-empty directory is unreliable on Windows. A small pointer file can be
flushed and replaced atomically while the prior snapshot remains available. The corpus fingerprint covers
source IDs/hashes, authority metadata, schema, normalization settings, and extractor identity; the
manifest separately records hashes of canonical files.

**Alternatives considered**:

- Overwrite one output tree: exposes partial builds.
- SQLite as canonical storage: binary bytes are not a portable deterministic review contract and schema
  migrations become harder.
- Timestamped snapshots: portable but not content-addressed and duplicate unchanged builds.

## Decision 5: Use deterministic lexical ranking as normative retrieval

**Decision**: Store canonical section JSONL with page-to-character spans. Search scans validated section
records, uses Unicode-normalized identifier-aware tokens, and sorts by an explicit integer/boolean score
tuple: exact alias/title, exact phrase, query-term coverage, authority rank, occurrence count, then stable
source/section IDs. Authority therefore breaks ties at the same exactness and coverage level without
allowing a weak normative match to eclipse a more exact specialist match.

**Rationale**: The baseline corpus is small enough for a bounded in-process scan, while deterministic
ranking is easy to test and explain. Excerpt page spans are derived from stored character ranges.

**Alternatives considered**:

- Persisted SQLite FTS5: fast but ranking/build details can vary with SQLite builds and the binary index is
  disposable rather than canonical.
- Embeddings/vector database: nondeterministic, introduces model/network/storage dependencies, and makes
  exact identifier search weaker.
- Graphify query as primary search: semantic and useful for discovery, but inferred/model-derived output
  is not the document citation authority.

## Decision 6: Attach a separate immutable reference session in MCP

**Decision**: Add a `ReferenceSession` next to `ProjectSession`. It can load a complete explicit corpus,
report status, search, and return bounded excerpts. A failed load leaves the prior snapshot active. The
reference revision/fingerprint and code-graph revision/fingerprint remain independent.

**Rationale**: Platform documentation and project-source analysis are different evidence domains. A
separate session prevents accidental identity merging and lets CLI/MCP delegate to the same corpus core.

**Alternatives considered**:

- Add reference nodes to canonical `CodeGraph`: violates evidence/backend boundaries.
- Let tools read arbitrary PDF/Markdown paths: grants filesystem browsing and bypasses snapshot validation.
- Build PDFs through MCP: introduces mutation, long work, optional dependencies, and model/network risk to
  the read-only agent surface.

## Decision 7: Integrate Graphify as an external, explicit overlay producer

**Decision**: Support observed Graphify CLI versions `>=0.9.0,<1.0.0` through `subprocess` with
`shell=False`, a timeout, explicit backend, explicit `local` or `remote` processing boundary, and isolated
output. `local` permits only `ollama`; `remote` additionally requires `--allow-remote`. Validate the
produced graph and publish a separate overlay manifest tied to the corpus fingerprint and Graphify version.

**Rationale**: Graphify 0.9.27 already handles Markdown/doc corpora and records extracted/inferred/
ambiguous relationships, making it valuable for conceptual discovery. Its own documentation states that
docs and PDFs enter a model-based semantic pass; therefore the adapter cannot silently auto-detect a
provider. Keeping it external avoids vendoring Apache-2.0 source or binding core installation to a
pre-1.0 CLI.

**Sources**:

- [Graphify repository and privacy behavior](https://github.com/safishamsi/graphify)
- Local observed CLI: `graphify 0.9.27`, `graphify extract <path> --out <dir> --backend <name>`

**Alternatives considered**:

- Fork or copy Graphify into the repository: duplicates maintenance and complicates licenses/upgrades.
- Reimplement a semantic graph pipeline: large unrelated scope and discards a capable upstream project.
- Run Graphify automatically during corpus build: violates zero-network/offline defaults and couples
  authoritative publication to optional inference.
- Feed original PDFs to Graphify: loses the canonical normalized/page-marker handoff and duplicates
  extraction policy.

## Decision 8: Acknowledge tools without implying endorsement

**Decision**: Add an acknowledgements document thanking Safi Shamsi and Graphify contributors, and thanking
OpenAI Codex and OpenAI for the agent-assisted development workflow. State that MQL5 CodeGraph remains an
independent community project; maintainers own and review the delivered code; no named party is claimed to
sponsor or endorse it.

**Rationale**: Gratitude and provenance help open-source users, but tool assistance is not authorship
transfer or a trademark license.

**Alternatives considered**:

- No acknowledgement: misses the user's explicit intent and upstream contribution.
- Marketing-style attribution: risks misleading affiliation and endorsement claims.
