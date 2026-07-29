# Feature Specification: Compiler Evidence Correlation

**Feature Branch**: `codex/mql5-agent-plugin`

**Created**: 2026-07-29

**Status**: Implemented

**Input**: Let agents distinguish static MQL5 findings from observed MetaEditor compiler evidence by
correlating an operator-provided local compile log with the current project graph. Preserve the trusted,
read-only, single-user workflow: this feature must not launch MetaEditor, write compiler artifacts, retain
raw logs, or claim that static analysis has compiler parity.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See whether compiler evidence is current (Priority: P1)

As an MQL5 project operator, I can supply the compile log produced by MetaEditor and obtain a clear,
bounded result telling me whether the log is usable evidence for the currently indexed source.

**Why this priority**: Agents must not silently infer that a structurally valid graph has been compiled,
or use an old compiler result after the source has changed.

**Independent Test**: Correlate a known-success and a known-failure log against a fixture graph, then
change a source file and prove the same log is reported as stale without changing the graph.

**Acceptance Scenarios**:

1. **Given** a current graph and a complete successful compiler log, **When** the operator requests
   correlation, **Then** the result reports current successful compiler evidence with its evidence
   identity and no static graph mutation.
2. **Given** a current graph and a compiler log with errors or warnings, **When** correlation runs,
   **Then** the result reports the observed outcome and each usable diagnostic separately from static
   diagnostics.
3. **Given** a compiler log older than the relevant source, **When** correlation runs, **Then** the
   result is explicitly stale and agents are told not to treat it as current compiler evidence.

---

### User Story 2 - Connect compiler diagnostics to code evidence (Priority: P2)

As an agent investigating a reported compiler problem, I can see the affected project file, source line,
and the graph symbol at that location when an exact evidence-backed correlation is available.

**Why this priority**: This converts an opaque compiler message into bounded, traceable context without
inventing a relationship from a message string.

**Independent Test**: Use fixture logs with file-and-line diagnostics that resolve to declarations,
non-declaration lines, and files outside the selected project; verify each result's correlation state.

**Acceptance Scenarios**:

1. **Given** a diagnostic with a project-relative file and an exact declared line, **When** correlation
   runs, **Then** it identifies that symbol and marks the link as location-based compiler evidence.
2. **Given** a diagnostic line with no declaration or a path outside the project, **When** correlation
   runs, **Then** the diagnostic is retained but its correlation is explicitly absent or ambiguous.

---

### User Story 3 - Use the same evidence through agent-facing interfaces (Priority: P3)

As a local operator or agent, I can request the same compiler-correlation result through the scriptable
CLI and active local MCP project session, including stable errors for missing, malformed, or unsuitable
logs.

**Why this priority**: An agent should receive the same bounded evidence envelope as the operator, not a
prompt-only summary that can drift from the project state.

**Independent Test**: Run each interface against the same fixture log and compare evidence identity,
outcome, freshness, diagnostics, and no-mutation behavior.

**Acceptance Scenarios**:

1. **Given** the same project graph and compiler log, **When** CLI and MCP correlation are requested,
   **Then** both report equivalent evidence content and stable error classes.
2. **Given** no active MCP graph, **When** compiler correlation is requested, **Then** the request fails
   without reading a project source tree or creating a partial session state.

### Edge Cases

- The log is empty, malformed, unreadable, too large, or contains no recognizable compiler summary.
- The log refers to a deleted, renamed, case-variant, absolute, or outside-project source path.
- The compiler emits a warning-only summary, an error-only summary, repeated diagnostics, or a locale
  variation that is not yet supported.
- A source file changes while a caller reads or correlates its log.
- A log does not identify the compiled entry point or contains an error location inside an included file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST ingest an explicitly supplied local compiler log only after validating its
  path, size, text encoding recovery, and containment policy for the selected trusted project workflow.
- **FR-002**: The system MUST report supplied compiler evidence as one of `current`, `stale`, or
  `incomplete`; it MUST distinguish observed success, warning, error, and unknown outcomes without
  treating any of them as a static-analysis diagnostic.
- **FR-003**: The system MUST identify compiler evidence by a deterministic log fingerprint, observed
  modification time, normalized entry-point/path data when available, and the source fingerprint of the
  graph used for correlation.
- **FR-004**: The system MUST determine freshness conservatively: evidence is current only when the log
  is complete and no relevant selected-project source is newer than the observed log; uncertainty MUST
  produce `stale` or `incomplete`, never a current claim.
- **FR-005**: The system MUST preserve each compiler diagnostic's original severity, message, location
  when present, and correlation state. A compiler-to-symbol link MUST be made only from project-contained
  location evidence and must identify its evidence origin distinctly from extracted or resolved edges.
- **FR-006**: The system MUST leave the canonical static graph, active MCP snapshot, selected source tree,
  and supplied compiler log unchanged after a correlation operation.
- **FR-007**: CLI and MCP MUST expose machine-readable, deterministic correlation results and stable
  validation errors; MCP MUST require an existing complete project snapshot.
- **FR-008**: The system MUST bound compiler-log reading and diagnostic parsing, and must reject logs
  outside its supported local size and format limits without exposing raw log contents in errors.
- **FR-009**: The feature MUST remain local and operator-driven. It MUST NOT launch MetaEditor, compile
  code, write `.ex5`/log artifacts, persist logs, retrieve raw source through MCP, or claim that a
  compiler result proves runtime behavior.
- **FR-010**: The supported MetaEditor log grammar and unsupported locales/variants MUST be documented,
  with fixture coverage for successful, warning, error, stale, malformed, and uncorrelated outcomes.

### Key Entities

- **Compiler Evidence Report**: An immutable result for one compiler log and one graph identity,
  containing source freshness, observed outcome, completeness, and bounded diagnostics.
- **Compiler Diagnostic**: A compiler-emitted finding with preserved severity, message, optional file and
  line, and a correlation state separate from static graph diagnostics.
- **Location Correlation**: Evidence that a compiler diagnostic location maps to a graph declaration,
  no declaration, or an ambiguous set; it never derives a symbol from message text alone.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All supported fixture logs yield deterministic evidence reports whose fingerprints,
  outcome, freshness, diagnostic ordering, and correlation states are identical across repeated runs.
- **SC-002**: 100% of stale, malformed, outside-project, and incomplete fixture logs are reported as
  non-current evidence and leave graph/source/log hashes unchanged.
- **SC-003**: 100% of fixture diagnostics with a declaration-exact project location resolve to the
  expected symbol, while no fixture diagnostic without location evidence gains a symbol correlation.
- **SC-004**: CLI and MCP return equivalent semantic evidence for the same complete fixture graph and
  log, and no MCP request without an active snapshot succeeds.
- **SC-005**: An agent can determine from one correlation response whether compiler evidence is current,
  what it observed, and which findings lack a trustworthy graph link, without reading raw log text.

## Assumptions

- Operators compile a selected trusted local project with their installed MetaEditor and explicitly pass
  the resulting log to this feature; MetaEditor may be absent from the MQL5 CodeGraph machine.
- V1 supports a documented English MetaEditor log grammar. Other localized or vendor-modified formats
  are preserved as incomplete evidence until explicitly added with fixtures.
- A compiler log is valuable external evidence but does not replace static graph assertions, broker
  execution evidence, or Strategy Tester results.
- The active source fingerprint and current source modification times are the authority for freshness;
  wall-clock and filesystem timestamp anomalies are treated conservatively.
