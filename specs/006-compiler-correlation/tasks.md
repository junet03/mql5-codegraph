# Tasks: Compiler Evidence Correlation

**Input**: Design documents from `specs/006-compiler-correlation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and
`contracts/compiler-evidence-v1.md`

**Tests**: Tests are required by the constitution and FR-008/FR-010. Add fixture-based regressions before
each implementation slice and run the full Python suite before handoff.

## Phase 1: Setup

**Purpose**: Establish the reviewed compiler-evidence contract and fixtures without introducing compiler
process control.

- [x] T001 Record the compiler-evidence boundary and no-process-control decision in `docs/decisions/ADR-0007-compiler-evidence-correlation.md`
- [x] T002 [P] Add documented English MetaEditor fixture logs and their `.gitignore` exception in `tests/fixtures/compiler_logs/` and `.gitignore`
- [x] T003 [P] Update the compiler-evidence limitation statement in `docs/limitations.md`

---

## Phase 2: Foundational Compiler-Evidence Core

**Purpose**: Create the immutable, bounded core and deterministic source-identity verification used by all
entry points.

**⚠️ CRITICAL**: No user story is complete until all core results remain separate from `CodeGraph` and
verify that the active graph fingerprint represents current source.

- [x] T004 [P] Write direct-core validation, log-bound, parser-summary, and freshness regressions in `tests/test_compiler_evidence.py`
- [x] T005 Add reusable deterministic source-identity observation in `src/mql5_codegraph/indexer.py`
- [x] T006 Implement bounded log validation, English summary parsing, immutable evidence reports, and stable core errors in `src/mql5_codegraph/compiler_evidence.py`
- [x] T007 Verify repeated core reports are deterministic and leave graph/source/log hashes unchanged in `tests/test_compiler_evidence.py`

**Checkpoint**: A direct core call safely returns a complete current/stale/incomplete report or a stable
validation error, with no project or graph mutation.

---

## Phase 3: User Story 1 - See Whether Compiler Evidence Is Current (Priority: P1) 🎯 MVP

**Goal**: An operator can distinguish current compile success/warnings/errors from stale or incomplete
evidence for a static project graph.

**Independent Test**: The fixture success, warning, error, stale, malformed, and oversized paths produce
the documented state/outcome and preserve all inputs.

- [x] T008 [P] [US1] Add outcome/count-mismatch, stale-source, and missing-summary regressions in `tests/test_compiler_evidence.py`
- [x] T009 [US1] Implement conservative evidence-state and observed-outcome derivation in `src/mql5_codegraph/compiler_evidence.py`
- [x] T010 [US1] Add project-contained entry/log validation and source-time comparison in `src/mql5_codegraph/compiler_evidence.py`

**Checkpoint**: P1 returns explicit compiler state without claiming that static analysis compiled successfully.

---

## Phase 4: User Story 2 - Connect Compiler Diagnostics to Code Evidence (Priority: P2)

**Goal**: A compiler finding identifies a graph declaration only when exact project-contained location
evidence supports it.

**Independent Test**: Fixture diagnostics exercise exact, no-declaration, outside-project, unlocated, and
ambiguous location states with deterministic ordering.

- [x] T011 [P] [US2] Add location-correlation regressions and negative message-only cases in `tests/test_compiler_evidence.py`
- [x] T012 [US2] Implement exact location-to-symbol correlation and explicit non-exact states in `src/mql5_codegraph/compiler_evidence.py`
- [x] T013 [US2] Document compiler-origin location evidence and unsupported grammar in `docs/architecture.md` and `README.md`

**Checkpoint**: P2 makes compiler diagnostics useful for agents without converting them into static graph
edges or guessed symbol references.

---

## Phase 5: User Story 3 - Use the Same Evidence through Agent-Facing Interfaces (Priority: P3)

**Goal**: CLI and the active read-only MCP session expose equivalent compiler evidence.

**Independent Test**: The same fixture graph/log produces semantically equivalent CLI and MCP results;
MCP-without-snapshot and adapter errors are stable.

- [x] T014 [P] [US3] Add CLI JSON/error/no-mutation regressions in `tests/test_cli.py`
- [x] T015 [P] [US3] Add MCP snapshot, error-envelope, and protocol-inventory regressions in `tests/mcp_adapter/test_service.py` and `tests/mcp_adapter/test_protocol.py`
- [x] T016 [US3] Add the `compiler-evidence` command and stable JSON envelope in `src/mql5_codegraph/cli.py`
- [x] T017 [US3] Add active-snapshot correlation projection and safe adapter error translation in `src/mql5_codegraph/mcp/service.py`
- [x] T018 [US3] Add the read-only `correlate_compiler_log` MCP tool in `src/mql5_codegraph/mcp/server.py`
- [x] T019 [US3] Update the MCP tool contract in `specs/004-mql5-agent-plugin/contracts/mcp-tools-v0.1.md`

**Checkpoint**: P3 gives agents bounded compiler evidence only after a complete static snapshot exists.

---

## Phase 6: Polish and Release Evidence

**Purpose**: Complete governance, documentation, verification, and generated graph upkeep.

- [x] T020 [P] Update `CHANGELOG.md`, `README.md`, and `docs/limitations.md` with scope, operator workflow, and no-runtime guarantee
- [x] T021 Add session evidence in `docs/project-journal/2026-07-29-002-compiler-evidence-correlation.md` and `docs/project-journal/README.md`
- [x] T022 Run `specs/006-compiler-correlation/quickstart.md` and record exact results in the journal
- [x] T023 Run `python -m unittest discover -s tests` and `python -m compileall -q src tests tools`
- [x] T024 Run an incremental directed Graphify update and graph-health diagnostic; keep `graphify-out/` uncommitted
- [x] T025 Inspect final diff, update completed tasks, and verify source/contract/ADR consistency

## Dependencies & Execution Order

- Phase 1 may start immediately.
- Phase 2 depends on the approved boundary and blocks every user story.
- US1 depends on Phase 2.
- US2 depends on the parsed immutable diagnostic model from US1.
- US3 depends on the complete core report from US1 and can follow US2; it must not reimplement parsing or freshness.
- Phase 6 depends on all desired user stories.

## Parallel Opportunities

- T002 and T003 modify independent files.
- T004 can be drafted alongside T005 before T006.
- T014 and T015 can be drafted in parallel after the core result shape is fixed.
- T020 documentation can proceed once the final output contract is stable.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and the immutable core in Phase 2.
2. Complete US1 and prove that current/stale/incomplete evidence is explicit and read-only.
3. Validate P1 before location mapping or adapters.

### Incremental Delivery

1. Add exact location correlation after P1, preserving unmatched compiler diagnostics.
2. Project the same core report through CLI and MCP only after it is independently verified.
3. Finish release evidence and Graphify maintenance; defer dashboard and MetaEditor process control.
