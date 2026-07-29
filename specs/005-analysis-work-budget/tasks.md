# Tasks: Analyzer Work Budget

**Input**: Design documents from `specs/005-analysis-work-budget/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, and
`contracts/analysis-budget-v1.md`

**Tests**: Tests are required by FR-008 and the project constitution. Add focused regressions before
each implementation slice, then run the full Python suite and proportional frontend gates.

## Phase 1: Setup

**Purpose**: Establish the reviewed feature contract and its release documentation path.

- [x] T001 Record the analyzer work-budget decision in `docs/decisions/ADR-0006-analysis-work-budget.md`
- [x] T002 Add an initial work-budget limitation/update note in `docs/limitations.md`

---

## Phase 2: Foundational Budget Contract

**Purpose**: Provide the one core budget and typed failure used by every entry point.

- [x] T003 Write validation, accounting, deterministic phase, and exhaustion tests in `tests/test_analysis_budget.py`
- [x] T004 Implement `AnalysisBudget` and `AnalysisBudgetExceeded` in `src/mql5_codegraph/analysis_budget.py`
- [x] T005 Thread one request-scoped budget through `src/mql5_codegraph/indexer.py` source discovery and analysis orchestration

**Checkpoint**: The core can reject invalid limits and stop discovery without modifying source or returning a graph.

---

## Phase 3: User Story 1 - Stop Excessive Analysis Safely (Priority: P1) 🎯 MVP

**Goal**: Bound every parser/resolver/runtime phase and preserve normal deterministic analysis under
the default limit.

**Independent Test**: Fixtures exercising range membership, nested arguments, binding-list scans, and
ambiguous call fan-out exhaust predictably; normal fixture output remains deterministic.

- [x] T006 [P] [US1] Add parser amplification and phase-exhaustion regressions in `tests/test_parser.py`
- [x] T007 [P] [US1] Add resolver fan-out and phase-exhaustion regressions in `tests/test_indexer.py`
- [x] T008 [US1] Add budget accounting at lexer/parser iteration and nested parsing paths in `src/mql5_codegraph/lexer.py` and `src/mql5_codegraph/parser.py`
- [x] T009 [US1] Add budget accounting at include/call resolution paths in `src/mql5_codegraph/resolver.py`
- [x] T010 [US1] Add budget accounting to runtime graph enrichment in `src/mql5_codegraph/runtime.py`
- [x] T011 [US1] Verify default-budget graph determinism and no source mutation in `tests/test_indexer.py`

**Checkpoint**: A direct library call is bounded across all analysis phases and returns only complete graphs.

---

## Phase 4: User Story 2 - Preserve a Usable Agent Snapshot (Priority: P2)

**Goal**: Surface one stable MCP budget error while preserving the last complete snapshot.

**Independent Test**: Index the reference fixture, force a budget-exhausted refresh, and prove the
revision, fingerprint, and query result are unchanged.

- [x] T012 [P] [US2] Add initial-index and transactional re-index exhaustion tests in `tests/mcp_adapter/test_service.py`
- [x] T013 [US2] Map `AnalysisBudgetExceeded` to stable MCP adapter errors and retain snapshot publication semantics in `src/mql5_codegraph/mcp/service.py`
- [x] T014 [US2] Add optional `max_work` to the read-only `index_project` projection in `src/mql5_codegraph/mcp/server.py`
- [x] T015 [US2] Update the MCP limit/error documentation in `specs/004-mql5-agent-plugin/contracts/mcp-tools-v0.1.md`

**Checkpoint**: Agents receive a structured actionable failure and never query a partial replacement snapshot.

---

## Phase 5: User Story 3 - Apply Protection from Every Local Entry Point (Priority: P3)

**Goal**: Make the same valid budget available through CLI and dashboard analysis starts.

**Independent Test**: CLI does not write its requested output on exhaustion and dashboard retains its
prior graph when an analysis job exhausts.

- [x] T016 [P] [US3] Add `--max-work` validation and no-output-on-exhaustion tests in `tests/test_cli.py`
- [x] T017 [P] [US3] Add dashboard budget failure and prior-graph retention tests in `tests/test_web_state.py`
- [x] T018 [US3] Add `--max-work` and structured analysis failure handling to `src/mql5_codegraph/cli.py`
- [x] T019 [US3] Thread the optional budget through jobs and summarize typed exhaustion in `src/mql5_codegraph/web/state.py`
- [x] T020 [US3] Thread dashboard `max_work` validation and startup configuration through `src/mql5_codegraph/web/api.py`, `src/mql5_codegraph/web/server.py`, and `src/mql5_codegraph/cli.py`

**Checkpoint**: Every supported local analysis entry point enforces the same canonical budget.

---

## Phase 6: Polish and Release Evidence

**Purpose**: Complete governance, user documentation, verification, and generated graph upkeep.

- [x] T021 [P] Update user-facing work-budget guidance in `README.md` and `docs/limitations.md`
- [x] T022 Add the implementation/session evidence in `docs/project-journal/2026-07-29-001-analysis-work-budget.md` and `docs/project-journal/README.md`
- [x] T023 Run the quickstart commands in `specs/005-analysis-work-budget/quickstart.md` and record exact results in the journal
- [x] T024 Run `python -m unittest discover -s tests` and `python -m compileall -q src tests tools`
- [x] T025 Run `npm run lint` and `npm run build` in `web/`
- [x] T026 Run an incremental directed Graphify update and graph-health diagnostic; keep `graphify-out/` uncommitted
- [x] T027 Inspect final diff, update completed tasks, and verify source/contract/ADR consistency

## Dependencies & Execution Order

- Phase 1 can begin immediately.
- Phase 2 depends on the reviewed feature design and blocks all user stories.
- US1 depends on the core budget in Phase 2.
- US2 depends on US1 because MCP indexes the canonical pipeline.
- US3 depends on US1 and may proceed in parallel with US2 after the canonical analyzer contract is stable.
- Phase 6 depends on all desired user stories.

## Parallel Opportunities

- T001 and T002 touch independent documentation files.
- T006 and T007 can be written in parallel after T005.
- T012 and the initial adapter contract documentation can proceed after the core typed error exists.
- T016 and T017 can proceed in parallel after the canonical behavior is available.
- T021 and the final verification preparation can proceed in parallel after implementation stabilizes.

## Implementation Strategy

### MVP First

1. Complete the core budget and source-discovery contract.
2. Complete US1 so direct analysis is bounded without partial graphs.
3. Validate the P1 fixtures and default deterministic output.

### Incremental Delivery

1. Add MCP transactional propagation (US2) after the core is proven.
2. Add CLI/dashboard configuration (US3) only as thin projections of the same budget.
3. Finish documentation, release gates, journal evidence, and Graphify health maintenance.
