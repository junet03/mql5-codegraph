# Feature Specification: Authoritative MQL5 Reference Corpus

**Feature Branch**: `codex/mql5-agent-plugin`

**Created**: 2026-07-30

**Status**: Complete

**Input**: Build an open-source, durable workflow that lets users transform their own official MQL5
PDF references into a local page-aware Markdown wiki, search it with trustworthy citations, optionally
derive a Graphify semantic overlay, and expose the same bounded knowledge to users and agents without
redistributing third-party documents or weakening MQL5 CodeGraph's evidence boundaries.

## User Scenarios & Testing

### User Story 1 - Build a trustworthy local reference corpus (Priority: P1)

As an MQL5 developer, I can select official PDF references already present on my machine and build a
local Markdown corpus that preserves document identity, hierarchy, page provenance, and extraction
limitations without copying those documents into the MQL5 CodeGraph repository.

**Why this priority**: Search and agent answers are trustworthy only when every derived section can be
traced back to the exact local document bytes and page range from which it came.

**Independent Test**: Build a corpus from a fixture PDF containing a hierarchy, prose, a table, and code;
repeat the build and confirm that the source is unchanged, the manifest and section identities are stable,
and every emitted section identifies its source document and physical PDF page range.

**Acceptance Scenarios**:

1. **Given** a readable operator-selected PDF directory and an empty output directory, **When** a build is
   requested, **Then** the system publishes a complete local corpus containing a deterministic manifest,
   navigable Markdown sections, page markers, source hashes, authority metadata, and disclosed extraction
   warnings.
2. **Given** the same PDF bytes and configuration, **When** the corpus is rebuilt, **Then** canonical
   manifest content, section identifiers, normalized text, links, and ordering are semantically identical.
3. **Given** an unreadable, unsupported, changed-during-build, or partly extractable PDF, **When** a build
   is requested, **Then** no partial corpus replaces the last complete corpus and the failure or limitation
   is reported without inventing missing content.

---

### User Story 2 - Find authoritative answers with inspectable citations (Priority: P2)

As a developer or maintainer, I can search the local corpus by exact MQL5 symbol or natural-language
phrase and receive bounded, deterministically ranked excerpts whose document, authority level, section,
page range, and content identity are immediately visible.

**Why this priority**: A fast answer without provenance can misstate platform behavior or elevate a
tutorial example above the language reference.

**Independent Test**: Run a golden set containing exact API names, language concepts, tutorial questions,
ambiguous terms, and absent terms; verify deterministic ranking, authority precedence, page citations,
bounded excerpts, and explicit no-match/truncation outcomes.

**Acceptance Scenarios**:

1. **Given** the same complete corpus and query, **When** search is repeated, **Then** result order,
   excerpts, citations, completion state, and truncation metadata are identical.
2. **Given** equally relevant statements from the language reference and a tutorial, **When** a general
   MQL5 behavior question is searched, **Then** the normative reference ranks first while both sources
   remain visible with their authority levels.
3. **Given** no supported match or a result limit that omits candidates, **When** search completes,
   **Then** the response distinguishes exhaustive no-match from bounded or truncated search.

---

### User Story 3 - Give agents the same bounded reference evidence (Priority: P3)

As an agent user, I can attach a complete local reference-corpus snapshot to an MQL5 CodeGraph session and
ask for reference status, search results, and cited excerpts through read-only agent tools without giving
the agent raw filesystem, shell, package-install, network, or corpus-mutation capabilities.

**Why this priority**: Agent guidance must be based on the same contract as human-facing search and must
not bypass consumer isolation or silently combine document claims with source-code facts.

**Independent Test**: Load a fixture project and fixture reference corpus through the official agent
client, compare tool results with direct core results, and confirm that invalid corpus roots, stale
snapshots, and pre-load requests return stable sanitized errors without changing either snapshot.

**Acceptance Scenarios**:

1. **Given** a complete corpus explicitly selected by the operator, **When** it is attached to a live
   session, **Then** the session reports its identity, document/section counts, authority catalog, and
   immutable revision without rebuilding it.
2. **Given** the same query through command-line and agent interfaces, **When** both target the same corpus
   identity, **Then** they return semantically equivalent ranked evidence and completion metadata.
3. **Given** a source-code question and a platform-contract question, **When** an agent composes an answer,
   **Then** project graph evidence and reference-document evidence remain separately labeled and neither is
   promoted into the other's evidence class.

---

### User Story 4 - Add an optional semantic navigation overlay (Priority: P4)

As an advanced local user, I can explicitly run a supported external Graphify installation against the
normalized Markdown corpus and receive a separate conceptual graph/wiki whose tool version, input corpus
identity, provenance, and inferred relationships are recorded.

**Why this priority**: Semantic navigation is valuable for discovery, but it is not required for exact
reference search and must never become an undeclared cloud dependency or overwrite the authoritative wiki.

**Independent Test**: Use a deterministic fake Graphify executable to validate invocation, version
capture, output isolation, timeout/failure handling, and graph acceptance; separately run an opt-in smoke
against a pinned real installation without treating semantic edges as normative citations.

**Acceptance Scenarios**:

1. **Given** a complete corpus and a supported Graphify executable, **When** the operator explicitly
   requests an overlay, **Then** outputs are written outside the authoritative corpus and identify both the
   Graphify version and input corpus fingerprint.
2. **Given** Graphify is absent, unsupported, times out, or returns malformed output, **When** overlay
   generation is requested, **Then** authoritative build/search remain usable and the prior valid overlay
   is not replaced.
3. **Given** an operation that may transmit corpus content to a remote model, **When** no explicit remote
   processing authority was supplied, **Then** the operation is refused before content is transmitted.

---

### User Story 5 - Adopt and extend the feature as an open-source contributor (Priority: P5)

As an open-source user or contributor, I can understand installation choices, data ownership, copyright
boundaries, offline defaults, agent behavior, extension points, verification, and third-party attribution
without reading implementation internals.

**Why this priority**: A durable open-source feature needs reproducible setup and honest attribution as
much as code.

**Independent Test**: Follow the public quickstart in a clean environment using a fixture PDF, build and
search a corpus, optionally exercise the Graphify adapter, and verify that acknowledgements credit Graphify,
its author/contributors, OpenAI Codex, and OpenAI without claiming endorsement or changing the project's
independent status.

**Acceptance Scenarios**:

1. **Given** a clean supported environment, **When** a user follows the documented local workflow, **Then**
   they can build and search the fixture corpus without placing third-party PDFs or generated corpus files
   in Git.
2. **Given** a contributor wants another document converter or semantic backend, **When** they read the
   architecture and contracts, **Then** they can identify the backend-neutral boundaries and required
   conformance tests.
3. **Given** public project documentation, **When** attribution is reviewed, **Then** it distinguishes
   gratitude from authorship, sponsorship, affiliation, and endorsement.

### Edge Cases

- The input directory is missing, contains no PDFs, contains symlinks, or overlaps the output directory.
- A PDF is encrypted with no permitted text extraction, has no outline, has duplicate bookmark titles,
  uses non-Latin fonts, contains scanned pages, or returns empty/malformed text for only some pages.
- Printed page numbers differ from physical PDF pages; one section spans hundreds of pages or multiple
  bookmarks target the same page.
- Extraction produces repeated headers, footers, table-of-contents noise, broken inter-letter spacing,
  malformed code blocks, or text that cannot be normalized safely.
- Two documents define the same symbol, document editions conflict, or authority metadata is missing.
- A corpus build is interrupted, disk space is exhausted, files change during extraction, or the output
  already contains a valid snapshot.
- A query contains punctuation-heavy identifiers, Unicode, only stop words, an extremely long expression,
  or requests more results/excerpt text than allowed.
- A corpus snapshot is copied between Windows and Linux or moved to another absolute path.
- Graphify writes a wiki containing stale files, changes its CLI/output format, or generates more than
  5,000 nodes.
- A user points the corpus builder at the MQL5 CodeGraph source repository, plugin cache, or another
  immutable toolchain directory.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST build only from an explicitly selected local input directory and MUST keep
  source PDFs, generated corpus data, caches, logs, and semantic overlays outside the distributed source
  repository by default.
- **FR-002**: The system MUST hash every source PDF, record stable document identity and metadata, and
  detect if any source changes while a build is in progress.
- **FR-003**: The system MUST preserve physical PDF page provenance and document hierarchy for every
  emitted section; printed-page labels MAY be retained separately but MUST NOT replace physical page
  identity.
- **FR-004**: The system MUST emit deterministic, portable Markdown navigation and machine-readable
  manifest data for the same document bytes and configuration.
- **FR-005**: The system MUST distinguish raw extraction, deterministic normalization, and unsupported or
  lossy recovery. Empty, failed, OCR-required, and layout-ambiguous pages MUST remain visible as limitations.
- **FR-006**: The system MUST publish a new corpus atomically only after all required documents, sections,
  links, manifests, and indexes pass validation; failed builds MUST preserve the last complete snapshot.
- **FR-007**: The system MUST support deterministic bounded search over exact identifiers and prose, with
  authority-aware ranking, cited excerpts, explicit completion/truncation state, and no mandatory remote
  service.
- **FR-008**: Every search result MUST identify the corpus, source document, document hash, authority level,
  section identity/path, physical PDF page range, and excerpt boundaries needed to inspect the evidence.
- **FR-009**: The system MUST treat the official language reference as normative, general programming books
  as explanatory, and specialist books as scoped guidance by default while allowing an operator-authored
  manifest to declare additional sources without silently elevating them.
- **FR-010**: The reference corpus and semantic overlay MUST remain separate from canonical `CodeGraph`
  entities, relationships, diagnostics, fingerprints, and compiler evidence.
- **FR-011**: Human and agent interfaces MUST delegate build-independent search and status semantics to one
  backend-neutral reference core and MUST return equivalent evidence for the same corpus identity.
- **FR-012**: Agent tools MUST be read-only, bounded, local by default, and free of raw filesystem
  browsing, shell execution, source/corpus mutation, package installation, and undeclared network access.
- **FR-013**: Attaching an invalid, incomplete, stale, or incompatible corpus MUST NOT replace the last valid
  active corpus snapshot.
- **FR-014**: Graphify integration MUST be optional, externally installed, version-observed, bounded, and
  isolated behind an adapter; its output MUST be stored separately and its inferred relationships MUST NOT
  be presented as normative document facts.
- **FR-015**: Any operation that may send document content to a remote model MUST require explicit
  operator authority for that invocation and MUST disclose the selected processing boundary before work
  begins.
- **FR-016**: The project MUST NOT vendor Graphify source. Distributed integration metadata MUST retain
  applicable third-party license and notice requirements and MUST permit the core package to install and
  operate without Graphify.
- **FR-017**: Public documentation MUST explain local data ownership, third-party PDF copyright,
  non-redistribution defaults, generated-output ignores, supported extraction limits, offline behavior,
  update/rebuild procedures, agent evidence rules, and extension/conformance requirements.
- **FR-018**: Public acknowledgements MUST thank Safi Shamsi and Graphify contributors for Graphify and
  thank OpenAI Codex and OpenAI for enabling the agent-assisted development workflow, while explicitly
  avoiding claims of authorship transfer, affiliation, sponsorship, or endorsement.
- **FR-019**: Fixture coverage MUST include outlines, duplicate headings, page-range boundaries, code,
  tables, empty pages, encrypted/unsupported input, deterministic rebuilds, search authority, stale or
  malformed snapshots, Graphify adapter failures, and CLI/agent conformance.
- **FR-020**: The feature MUST support local Windows and Linux workflows and MUST use portable corpus-relative
  identities rather than persisting workstation-specific absolute paths in canonical outputs.

### Key Entities

- **Reference Source**: Operator-declared document metadata including stable source ID, title, authority,
  official URL, expected role, local filename, byte hash, page count, and extraction state.
- **Reference Section**: One stable navigable unit derived from a source hierarchy and physical page range,
  containing normalized text, source markers, warnings, aliases, and links.
- **Reference Corpus Snapshot**: One immutable, complete manifest plus sections and search index identified
  by a deterministic fingerprint independent of its absolute filesystem location.
- **Reference Search Result**: A ranked cited excerpt with authority, source/section identity, page range,
  score components, and completion metadata.
- **Semantic Overlay**: Optional Graphify-derived graph/wiki tied to one corpus fingerprint and tool version;
  it is disposable navigation data rather than normative source evidence.
- **Reference Session Snapshot**: The active read-only corpus identity and revision attached to an agent
  session independently of the active MQL5 project graph.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Rebuilding an unchanged fixture corpus 100 times yields identical canonical manifest,
  section, link, citation, and search-result content.
- **SC-002**: One hundred percent of fixture search results resolve to an existing document hash, section,
  and physical PDF page range; no result with missing provenance is returned as usable evidence.
- **SC-003**: A golden set of at least 20 exact-symbol and conceptual MQL5 questions returns the expected
  authority tier and a correct inspectable citation in every supported case.
- **SC-004**: One hundred percent of interrupted, changed-source, malformed, incompatible, and failed-overlay
  tests preserve the last valid corpus and report a non-success completion state.
- **SC-005**: A complete corpus built from the three operator-supplied references covers all 10,021 physical
  pages with every empty, failed, or ambiguous page explicitly accounted for.
- **SC-006**: Repeated command-line and official agent-client requests against the same snapshot produce
  semantically equivalent status and search evidence.
- **SC-007**: Default build, search, status, and excerpt workflows complete with zero network requests and
  without Graphify installed.
- **SC-008**: A new user can follow the fixture quickstart to build, inspect, and search a corpus in under
  15 minutes without modifying the source repository or committing generated/reference content.
- **SC-009**: Public package, documentation, license, notice, and attribution checks contain no bundled
  third-party PDF bytes and no statement implying MetaQuotes, Graphify, OpenAI, or their contributors
  sponsor or endorse MQL5 CodeGraph.

## Assumptions

- Users obtain and retain their own lawful local copies of official MQL5 references; the project does not
  redistribute or automatically download those documents.
- Version 1 targets text-bearing PDFs with usable outlines. OCR may be reported as required but is not
  performed automatically.
- Exact/lexical reference search is the required offline baseline. Semantic search is optional and cannot
  weaken deterministic citation or authority ranking.
- Generated Markdown is a local derivative corpus and remains subject to the source documents' rights and
  terms even though MQL5 CodeGraph's own source code is MIT-licensed.
- Graphify is an optional external tool and its pre-1.0 CLI/output compatibility is protected by version
  checks, adapter validation, and fixture tests rather than assumed.
- Corpus attachment is explicitly operator-selected and independent of the selected MQL5 project root.
- The first implementation may expose reference status/search/excerpt through CLI and the existing private
  MCP alpha; dashboard authoring and hosted/multi-user corpus services are deferred.
