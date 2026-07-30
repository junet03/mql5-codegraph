# Tasks: Authoritative MQL5 Reference Corpus

**Input**: Design documents from `specs/007-authoritative-reference-corpus/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by FR-019 and written before or alongside each implementation increment.

**Organization**: Tasks are grouped by user story and ordered so each phase has an independent checkpoint.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add the optional dependency and package skeleton without changing current behavior.

- [X] T001 Add the `reference` optional dependency and install it in CI in `pyproject.toml` and `.github/workflows/ci.yml`
- [X] T002 Create the public reference package exports in `src/mql5_codegraph/reference/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish stable entities, failures, serialization, and generated fixture support used by all
stories.

**⚠️ CRITICAL**: No story implementation begins until these contracts are reviewable.

- [X] T003 [P] Add a deterministic text-PDF/outline fixture generator in `tests/reference_corpus/helpers.py`
- [X] T004 Define reference versions, limits, dataclasses, authority ranks, and stable errors in `src/mql5_codegraph/reference/models.py`
- [X] T005 Implement canonical JSON/JSONL, hashing, confined relative paths, and atomic pointer helpers in `src/mql5_codegraph/reference/models.py`

**Checkpoint**: Shared reference contracts are importable without pypdf or Graphify.

---

## Phase 3: User Story 1 - Build a trustworthy local reference corpus (Priority: P1) 🎯 MVP

**Goal**: Convert explicitly selected local PDFs into a deterministic, complete, page-aware Markdown
snapshot without replacing the prior valid snapshot on failure.

**Independent Test**: Build the generated fixture twice, compare canonical bytes/IDs, account for every
physical page, then simulate a changed/failed source and verify `current.json` still identifies the first
snapshot.

### Tests for User Story 1

- [X] T006 [US1] Add source-manifest, outline partition, page-state, deterministic rebuild, integrity, and failed-publication tests in `tests/reference_corpus/test_builder.py`

### Implementation for User Story 1

- [X] T007 [US1] Implement known-source defaults, explicit manifest validation, source bounds, symlink rejection, and before/after hashing in `src/mql5_codegraph/reference/builder.py`
- [X] T008 [US1] Implement optional pypdf/PDFium loading, nested-outline flattening, page labels, per-page extraction states, and normalization in `src/mql5_codegraph/reference/builder.py`
- [X] T009 [US1] Implement non-overlapping outline-derived sections, page-character spans, portable IDs, linked Markdown, and JSONL records in `src/mql5_codegraph/reference/builder.py`
- [X] T010 [US1] Implement staged validation, content-addressed snapshot publication, same-build reuse, and atomic `current.json` switching in `src/mql5_codegraph/reference/builder.py`
- [X] T011 [US1] Add `reference build` and `reference status` CLI contracts and error formatting in `src/mql5_codegraph/cli.py`

**Checkpoint**: US1 passes without Graphify and no third-party document is present in Git.

---

## Phase 4: User Story 2 - Find authoritative answers with inspectable citations (Priority: P2)

**Goal**: Validate an immutable snapshot and return deterministic, authority-aware, page-cited lexical
search and exact excerpts.

**Independent Test**: Run exact identifiers, phrases, ambiguous authority ties, punctuation, Unicode, no
match, truncation, and corrupt-snapshot cases; repeat and compare complete JSON results.

### Tests for User Story 2

- [X] T012 [US2] Add snapshot validation, golden ranking, exact citation, excerpt-bound, no-match, and truncation tests in `tests/reference_corpus/test_corpus.py`

### Implementation for User Story 2

- [X] T013 [US2] Implement pointer/manifest/file/invariant validation and immutable record loading in `src/mql5_codegraph/reference/corpus.py`
- [X] T014 [US2] Implement identifier-aware normalization, explainable deterministic ranking, authority tie-breaking, page-span excerpts, and completion metadata in `src/mql5_codegraph/reference/corpus.py`
- [X] T015 [US2] Add `reference search` and `reference excerpt` CLI contracts plus CLI/core conformance tests in `src/mql5_codegraph/cli.py` and `tests/test_cli.py`

**Checkpoint**: US1 and US2 work with only the `reference` build extra and zero network.

---

## Phase 5: User Story 3 - Give agents the same bounded reference evidence (Priority: P3)

**Goal**: Attach one valid corpus independently of the project graph and expose only bounded status,
search, and excerpt operations to the experimental local MCP beta.

**Independent Test**: Compare MCP and core results for one corpus, assert independent revisions and
fingerprints, and verify invalid/stale loads leave the active corpus unchanged.

### Tests for User Story 3

- [X] T016 [US3] Add reference-session lifecycle, stale fingerprint, failed replacement, and core conformance tests in `tests/mcp_adapter/test_service.py`
- [X] T017 [US3] Add four MCP tool schema/protocol tests and update expected tool inventory in `tests/mcp_adapter/test_protocol.py`

### Implementation for User Story 3

- [X] T018 [US3] Implement the independently locked immutable `ReferenceSession` in `src/mql5_codegraph/mcp/service.py`
- [X] T019 [US3] Register `load_reference_corpus`, `reference_status`, `search_reference`, and `get_reference_excerpt` without build/shell/network capabilities in `src/mql5_codegraph/mcp/server.py`
- [X] T020 [US3] Update plugin contract assertions and agent evidence guidance in `tests/test_plugin_bundle.py`, `plugins/mql5-codegraph-intelligence/references/reference-corpus.md`, and relevant `plugins/mql5-codegraph-intelligence/skills/*/SKILL.md`

**Checkpoint**: MCP clients can use cited documentation while project and reference evidence remain
separate.

---

## Phase 6: User Story 4 - Add an optional semantic navigation overlay (Priority: P4)

**Goal**: Explicitly invoke a supported external Graphify installation against normalized Markdown and
publish only a validated, separately labeled overlay.

**Independent Test**: Use a fake executable to test version acceptance/rejection, local/remote authority,
argument construction, timeout/non-zero/malformed output, atomic preservation, and successful manifest
publication.

### Tests for User Story 4

- [X] T021 [US4] Add fake-Graphify version, privacy-boundary, timeout, malformed-output, isolation, and publication tests in `tests/reference_corpus/test_graphify_adapter.py`

### Implementation for User Story 4

- [X] T022 [US4] Implement supported-version probing, explicit processing authority, `shell=False` invocation, bounded output validation, overlay hashing, and atomic publication in `src/mql5_codegraph/reference/graphify_adapter.py`
- [X] T023 [US4] Add the explicit `reference graphify` CLI contract and boundary disclosure in `src/mql5_codegraph/cli.py`

**Checkpoint**: Authoritative build/search remain unchanged when Graphify is absent or fails.

---

## Phase 7: User Story 5 - Adopt and extend as an open-source contributor (Priority: P5)

**Goal**: Document ownership, setup, updates, evidence classes, extension contracts, limitations, and
attribution so users can operate the feature without implementation knowledge.

**Independent Test**: Follow the public quickstart in a clean environment with generated fixtures and
confirm package contents include code/docs/notices but no PDF or generated corpus bytes.

### Tests for User Story 5

- [X] T024 [P] [US5] Add package, notice, no-PDF, generated-output-ignore, and public-doc link assertions in `tests/test_packaging_policy.py`

### Implementation for User Story 5

- [X] T025 [P] [US5] Write the user/operator/contributor guide and source-manifest example in `docs/reference-corpus.md`
- [X] T026 [P] [US5] Add independent-project acknowledgements for Safi Shamsi, Graphify contributors, OpenAI Codex, and OpenAI in `ACKNOWLEDGEMENTS.md`
- [X] T027 [US5] Update feature navigation, architecture boundaries, install extras, and generated-output ignores in `README.md`, `docs/architecture.md`, `.gitignore`, and `pyproject.toml`

**Checkpoint**: A new user can build/search locally and understands what may leave their machine.

---

## Phase 8: Polish & Cross-Cutting Verification

**Purpose**: Prove the integrated behavior, record evidence, and refresh generated project intelligence.

- [X] T028 Run focused reference, CLI, MCP, plugin, and packaging tests under `tests/` and resolve regressions
- [X] T029 Run `python -m unittest discover -s tests`, `python -m compileall -q src tests tools`, package metadata checks, and `git diff --check`
- [X] T030 Run an opt-in smoke on `D:\mql5-pdf`, verify 10,021-page accounting and at least 20 golden queries, while keeping all output outside Git
- [X] T031 Run incremental Graphify update and directed multigraph diagnostics, then keep `graphify-out/` uncommitted
- [X] T032 Mark the feature spec/checklist/tasks complete and record exact evidence, limitations, and next objective in `specs/007-authoritative-reference-corpus/spec.md` and `docs/project-journal/`
- [X] T033 Add backend-scoped Graphify subprocess environments and tests that exclude unrelated provider and GitHub credentials
- [X] T034 Audit tracked history, release artifacts, Python dependencies, bundled web dependencies, and static security findings
- [X] T035 Prepare versioned public-release metadata, third-party notices, acknowledgements, community links, and durable release notes
- [ ] T036 Run the complete Python/web/package/Graphify release gate and publish v0.3.0 only after hosted protections pass
- [X] T037 Bind dashboard analysis and source reads to operator-authorized startup paths and add regression coverage
- [ ] T038 Clear the first public CodeQL findings through source fixes, then rerun all hosted release gates

---

## Dependencies & Execution Order

### Phase dependencies

- Setup → Foundational → US1.
- US2 requires a complete US1 snapshot.
- US3 requires US2's validated reader and search contract.
- US4 requires US1/US2 only; it is otherwise isolated from MCP.
- US5 can start after contracts stabilize, but its final verification follows US1–US4.
- Polish follows every selected story.

### User story dependencies

```text
US1 build ──> US2 search ──> US3 agent tools
    └───────────────> US4 Graphify overlay
US1 + US2 + US3 + US4 ──> US5 final public guidance
```

### Parallel opportunities

- T003 can proceed independently of T004 after contract names are fixed.
- T024, T025, and T026 touch separate files and can proceed in parallel after public interfaces stabilize.
- US3 and US4 can proceed in parallel after US2 because they use different adapters and files.

## Parallel Example: User Story 5

```text
Task: "Add packaging-policy assertions in tests/test_packaging_policy.py"
Task: "Write the operator/contributor guide in docs/reference-corpus.md"
Task: "Write ACKNOWLEDGEMENTS.md"
```

## Implementation Strategy

### MVP first

1. Complete Setup and Foundational contracts.
2. Implement US1 with generated fixture tests.
3. Stop and validate deterministic, failure-safe snapshot publication.

### Incremental delivery

1. Add US2 deterministic citations.
2. Add US3 read-only agent parity.
3. Add US4 optional semantic discovery.
4. Finish US5 public release documentation and policy checks.
5. Run full and local-real-corpus gates.

## Notes

- `[P]` means different files with no dependency on unfinished work.
- Tests must prove failure and ambiguity behavior, not only the happy path.
- Generated PDFs in tests are created in temporary directories; no official PDF fixture is committed.
- Do not commit corpus snapshots, Graphify output, cache, logs, build output, or local documents.
