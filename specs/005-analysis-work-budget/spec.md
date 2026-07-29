# Feature Specification: Analyzer Work Budget

**Feature Branch**: `codex/mql5-agent-plugin`

**Created**: 2026-07-29

**Status**: Implemented

**Input**: Add a deterministic, analyzer-wide work budget so trusted local MQL5 projects can be
analyzed safely without unbounded parser or resolver work. Preserve the read-only local workflow,
existing graph evidence semantics, and the last valid MCP snapshot. MetaEditor integration and
persistent indexing are explicitly deferred.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop excessive analysis safely (Priority: P1)

As an MQL5 project operator, I can set or rely on a safe analysis work limit so that an unusually
large or adversarial trusted project stops with an actionable result instead of consuming unbounded
resources.

**Why this priority**: A bounded analysis operation is required before this local analyzer can safely
be used repeatedly by agents on projects whose complexity is not known in advance.

**Independent Test**: Analyze fixtures that intentionally exercise each known amplification path and
verify that they stop at the configured limit, report the stopping phase and consumed work, and leave
the input tree unchanged.

**Acceptance Scenarios**:

1. **Given** a project whose analysis exceeds its configured work limit, **When** the operator starts
   analysis, **Then** it ends with a stable budget-exhausted result that identifies the phase and does
   not publish a partial graph.
2. **Given** a project whose analysis remains within its limit, **When** the operator analyzes it,
   **Then** it produces the same deterministic graph and diagnostics as the existing supported flow.
3. **Given** an invalid work-limit value, **When** the operator requests analysis, **Then** the
   request is rejected before source analysis begins with an actionable validation error.

---

### User Story 2 - Preserve a usable agent snapshot (Priority: P2)

As an agent using the MCP adapter, I retain the last successful project snapshot when a re-index
operation runs out of budget.

**Why this priority**: A failed refresh must not make previously verified project intelligence
unavailable or tempt an agent to treat partial findings as facts.

**Independent Test**: Index a reference project, attempt a budget-exhausted re-index, then verify
that all project status identity and query results remain those of the first snapshot.

**Acceptance Scenarios**:

1. **Given** an active snapshot, **When** the same project exceeds the requested work limit during
   re-indexing, **Then** the MCP response identifies budget exhaustion and the active snapshot remains
   unchanged.
2. **Given** no active snapshot, **When** initial indexing exceeds its limit, **Then** the MCP server
   reports the stable failure without exposing a partial snapshot.

---

### User Story 3 - Apply the same protection from every local entry point (Priority: P3)

As a local operator, I receive equivalent work-limit behavior whether analysis starts from the
library, CLI, dashboard, or MCP adapter.

**Why this priority**: A limit that can be bypassed through another supported entry point does not
provide a reliable safety boundary for agent workflows.

**Independent Test**: Exercise a bounded analysis through each supported entry point and compare its
success/failure class, configured limit, and deterministic metadata.

**Acceptance Scenarios**:

1. **Given** the same project and work limit, **When** analysis starts through any supported local
   entry point, **Then** it observes the same analysis budget and does not write to the project.
2. **Given** the default limit, **When** a current supported fixture is analyzed, **Then** no caller
   must change its existing invocation to receive a successful result.

### Edge Cases

- The budget is exhausted while discovering files, parsing malformed source, resolving includes, or
  resolving ambiguous call edges.
- A limit is exhausted exactly at a phase boundary.
- A re-index of an unchanged project is requested with a stricter limit than the active snapshot.
- A caller supplies a non-integer, zero, negative, or excessively large limit.
- A project contains no MQL5 source files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST apply one deterministic work budget across source discovery, parsing,
  graph resolution, and runtime enrichment for every supported analysis entry point.
- **FR-002**: The system MUST make the default limit safe for ordinary supported projects while
  allowing an operator to request a stricter valid limit for one analysis operation.
- **FR-003**: When work is exhausted, the system MUST stop further analysis, MUST NOT publish or save
  a partial graph, and MUST preserve the analyzed source tree unchanged.
- **FR-004**: Budget-exhausted results MUST distinguish exhaustion from malformed input and other
  analysis failures, and MUST include a stable code, the completed/active phase, consumed work, and
  configured limit without exposing source contents.
- **FR-005**: MCP re-indexing that exhausts its budget MUST retain the prior valid snapshot unchanged;
  an initial failed index MUST leave the session unindexed.
- **FR-006**: Existing successful analysis output, graph identity, evidence origin, confidence,
  ordering, and diagnostics MUST remain deterministic when analysis completes within the budget.
- **FR-007**: Public local interfaces MUST validate a requested work limit before source analysis
  starts and provide compatible machine-readable errors.
- **FR-008**: The implementation MUST cover the accepted parser and resolver amplification paths with
  bounded regression tests.
- **FR-009**: This feature MUST remain local, read-only, single-user, and must not add persistent
  indexes, remote transport, raw-source retrieval, or MetaEditor control.

### Key Entities

- **Analysis Work Budget**: The configured maximum amount of deterministic analysis work and the
  resulting consumed-work state for one operation.
- **Budget-Exhausted Result**: A stable failure outcome containing the limit, consumption, phase, and
  non-public diagnostic context needed for a caller to retry safely.
- **Published Snapshot**: The complete immutable graph and intelligence state visible to MCP callers
  only after a successful analysis operation.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All fixtures designed for the four documented amplification paths stop before exceeding
  their configured maximum work by more than one accounting unit.
- **SC-002**: One hundred percent of budget-exhausted test runs leave input-file hashes unchanged and
  expose no partial graph through any supported entry point.
- **SC-003**: One hundred percent of re-index exhaustion tests preserve the prior snapshot revision,
  source fingerprint, and query results.
- **SC-004**: The existing complete test suite and a normal reference-project analysis continue to
  pass with the default budget.
- **SC-005**: A user can determine whether to retry with a different limit solely from the structured
  failure result, without inspecting application logs or source files.

## Assumptions

- Work is a deterministic analyzer accounting unit, not a wall-clock promise; operators retain control
  of the local machine and analysis remains limited to trusted local projects in this feature.
- The current default behavior remains compatible for ordinary supported fixtures and existing callers.
- The feature must protect the library, CLI, dashboard, and MCP adapter because each can initiate
  analysis today.
- Compiler diagnostics, MetaEditor automation, persistent snapshots, and multi-project server state
  are separate future features.
