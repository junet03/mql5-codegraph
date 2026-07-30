# Feature Specification: Local Web Dashboard

**Feature Branch**: `main`

**Created**: 2026-07-22

**Status**: Approved for implementation

**Input**: Turn MQL5 CodeGraph into a carefully completed product with a serious local web application.

## User Scenarios & Testing

### User Story 1 - Analyze and understand a repository visually (Priority: P1)

As an MQL5 developer, I can select a local repository, start analysis, and inspect its architecture
as an interactive graph without learning graph query syntax.

**Why this priority**: Visual comprehension is the primary product value beyond the existing CLI.

**Independent Test**: Start the dashboard with the reference fixture, analyze it, and inspect graph nodes,
relationships, summary metrics, and an event-handler detail panel in one browser session.

**Acceptance Scenarios**:

1. **Given** no graph is loaded, **When** a valid repository path is submitted, **Then** analysis
   progress is visible and the completed graph replaces the empty state.
2. **Given** a loaded graph, **When** a node is selected, **Then** its kind, qualified name, source
   location, attributes, callers, callees, and runtime relationships are displayed.
3. **Given** a large graph, **When** filters change, **Then** the visible graph is bounded while the
   canonical graph remains intact on the server.

---

### User Story 2 - Search, trace context, and assess impact (Priority: P2)

As a maintainer, I can search symbols and trace context or upstream impact from the same screen.

**Why this priority**: It turns the visual map into a practical debugging and change-safety tool.

**Independent Test**: Search `CalculateLots`, open it, and request impact to see `OnTick` and path evidence.

**Acceptance Scenarios**:

1. **Given** a graph, **When** a search term is entered, **Then** matching symbols appear with kind
   and source location and can be focused in the graph.
2. **Given** a selected symbol, **When** context or impact is requested, **Then** bounded results and
   relationship paths are shown without re-indexing.

---

### User Story 3 - Investigate diagnostics and source evidence (Priority: P3)

As a parser maintainer or EA developer, I can filter diagnostics and open the exact local source
evidence associated with a finding.

**Why this priority**: Honest limitations and inspectable evidence are essential for trusting AI code analysis.

**Independent Test**: Open the malformed fixture diagnostic and verify the source viewer highlights
the reported line while preventing access outside the active repository.

**Acceptance Scenarios**:

1. **Given** diagnostics exist, **When** severity or code filters change, **Then** matching diagnostics
   are listed with counts and locations.
2. **Given** a diagnostic location, **When** it is opened, **Then** the relevant local source is shown
   with line numbers and the target line highlighted.
3. **Given** a crafted path outside the active root, **When** source is requested, **Then** access is rejected.

### Edge Cases

- The selected directory does not exist, is unreadable, or contains no MQL5 files.
- Analysis is requested twice while a previous job is running.
- The browser disconnects while analysis continues.
- A graph contains thousands of nodes or a selected node disappears after re-indexing.
- The production frontend bundle is missing or stale.
- A source file is deleted, changed, too large, or encoded imperfectly after indexing.
- Requests arrive with malformed JSON, excessive payloads, invalid depths, or traversal paths.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST provide a `serve` command that starts a local dashboard on loopback by default.
- **FR-002**: Users MUST authorize a local repository and optional include roots at process startup for
  background analysis and re-indexing.
- **FR-003**: The dashboard MUST show analysis state, summary metrics, graph health, and diagnostic counts.
- **FR-004**: The dashboard MUST render a directed interactive graph with node-kind and relationship filters.
- **FR-005**: Users MUST be able to search, focus, select, pan, zoom, fit, and reset the graph by keyboard or pointer.
- **FR-006**: Selected-node details MUST expose source evidence, attributes, incoming edges, and outgoing edges.
- **FR-007**: Users MUST be able to request bounded context and upstream impact for a selected symbol.
- **FR-008**: Users MUST be able to filter diagnostics by severity/code and navigate to source evidence.
- **FR-009**: Source access MUST be restricted to indexed `.mq5` and `.mqh` files under the
  startup-authorized analysis root.
- **FR-010**: The server MUST reject oversized or malformed request bodies with structured errors.
- **FR-011**: The server MUST keep the full canonical graph while returning bounded visualization payloads.
- **FR-012**: The frontend MUST provide responsive empty, loading, success, and error states.
- **FR-013**: The product MUST operate locally without cloud accounts, hosted storage, or source upload.
- **FR-014**: API, server, build, and core regression tests MUST pass before completion.

### Key Entities

- **DashboardState**: Active graph, root, graph version, current job, and last error.
- **AnalysisJob**: Identifier, state, timing, requested paths, result summary, and error.
- **VisualizationGraph**: Bounded node and edge projection plus truncation metadata and filter echo.
- **SourceEvidence**: Safe repository-relative file content, line metadata, and highlighted location.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A first-time user can analyze the reference repository and focus `OnTick` in under two minutes.
- **SC-002**: API health, analyze, graph, query, context, impact, diagnostics, and source contracts pass automated tests.
- **SC-003**: The dashboard remains interactive with a canonical graph of at least 10,000 nodes by bounding rendered nodes.
- **SC-004**: All source traversal tests outside the active root are rejected.
- **SC-005**: The production frontend build completes without TypeScript or bundler errors.
- **SC-006**: The dashboard is visually verified at desktop and narrow viewport sizes with no blocking layout defects.

## Assumptions

- The dashboard is a trusted single-user local tool and binds to `127.0.0.1` unless explicitly overridden.
- The Python process has permission to read repositories selected by the user.
- A local browser is available; automatic opening can be disabled.
- Authentication and cloud hosting are outside this feature because source code never leaves the machine.
