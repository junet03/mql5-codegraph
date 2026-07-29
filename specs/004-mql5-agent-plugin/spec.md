# Feature Specification: MQL5 Agent Plugin and MCP Alpha

**Feature Branch**: `codex/mql5-agent-plugin`

**Created**: 2026-07-23

**Status**: Implemented

**Input**: Package MQL5 CodeGraph as a private Codex plugin so internal agents can use repeatable
skills and a read-only MCP adapter to understand local MQL5 projects through the existing
Intelligence Kernel.

## User Scenarios & Testing

### User Story 1 - Index a local MQL5 project safely (Priority: P1)

As an internal MQL5 developer, I can explicitly select a trusted local project and create an
in-memory intelligence snapshot without changing its source files or publishing its contents.

**Why this priority**: Every later agent query depends on a current, correctly scoped snapshot.

**Independent Test**: Start the MCP server, index the reference fixture, verify the reported root,
fingerprint, file/node/edge counts, and confirm that no fixture file was created or modified.

**Acceptance Scenarios**:

1. **Given** a valid local MQL5 directory, **When** `index_project` is called, **Then** the server
   publishes one active in-memory graph and returns its identity and counts.
2. **Given** an invalid or missing directory, **When** indexing is requested, **Then** the server
   returns a stable sanitized error and keeps the previous snapshot unchanged.
3. **Given** no active snapshot, **When** `project_status` is called, **Then** it reports
   `not_indexed` without scanning the filesystem.

---

### User Story 2 - Query evidence-backed project intelligence (Priority: P2)

As an internal agent, I can query symbols, callers/callees context, upstream impact, directed paths,
diagnostics, and bounded context packages using the same semantics as CLI and Web.

**Why this priority**: The plugin is valuable only when agents receive authoritative evidence,
limits, ambiguity, and completion state instead of improvised repository summaries.

**Independent Test**: Run equivalent requests through MCP and directly through
`IntelligenceKernel`, then compare the structured contract results byte-for-byte after removing
the MCP envelope.

**Acceptance Scenarios**:

1. **Given** an active snapshot, **When** an MCP intelligence tool is called, **Then** its result is
   delegated to Intelligence Kernel contract v1 and preserves graph identity and bounds.
2. **Given** an ambiguous or missing symbol, **When** a tool is called, **Then** candidates or
   `no_match` remain explicit.
3. **Given** a bounded traversal or path search, **When** the limit is reached, **Then** the tool
   reports truncation and its completion reason.
4. **Given** no active snapshot, **When** an intelligence tool is called, **Then** it returns a
   stable `project_not_indexed` error.

---

### User Story 3 - Reuse the workflow through a private Codex plugin (Priority: P3)

As the owner of multiple MQL5 projects, I can install one private plugin whose skills teach agents
when to index, which MCP tools to call, and how to preserve evidence and uncertainty.

**Why this priority**: Reusable instructions and tool configuration are what make the capability
consistent across agent sessions and repositories.

**Independent Test**: Validate the plugin manifest and skills, install it from the repo-local
marketplace, start a fresh Codex task, and verify the bundled MCP server advertises the expected
read-only tools.

**Acceptance Scenarios**:

1. **Given** the private repository marketplace, **When** the plugin is installed, **Then** Codex
   discovers its skills and bundled MCP configuration.
2. **Given** an architecture or impact question, **When** a matching skill is selected, **Then** the
   skill directs the agent to use MCP evidence before broad file scanning.
3. **Given** a stale or different project root, **When** a skill begins, **Then** it checks status
   and requests a fresh explicit index rather than assuming the existing snapshot is current.

### Edge Cases

- A project contains no `.mq5` or `.mqh` files.
- Include roots are missing, duplicated, or outside the selected project.
- An MCP call arrives before initialization or before any project is indexed.
- Tool arguments contain unknown fields, invalid bounds, non-string list entries, or too many path targets.
- A project is re-indexed after source changes while an earlier snapshot is still active.
- The SDK dependency is absent or a future incompatible major version is installed.
- Analysis is slow on a large repository; v0.1 has no analyzer-wide wall-clock budget.
- The MCP host closes stdin, externally ends the child, or retains a dead transport without respawning.
- A consumer task starts in the MQL5 CodeGraph source, marketplace, plugin cache, or package directory
  instead of the intended MQL5 project.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST expose an experimental local MCP stdio adapter without changing the
  Intelligence Kernel contract.
- **FR-002**: MCP intelligence tools MUST delegate semantic operations to `IntelligenceKernel`.
- **FR-003**: `index_project` MUST read only the explicitly supplied local project and include roots,
  build an in-memory snapshot, and MUST NOT modify analyzed source files.
- **FR-004**: A failed index MUST NOT replace the last valid active snapshot.
- **FR-005**: `project_status` MUST report whether a snapshot is active plus its root, graph identity,
  revision, and deterministic counts without triggering analysis.
- **FR-006**: The adapter MUST expose bounded tools for query, context, impact, path,
  context-package, and diagnostics operations.
- **FR-007**: Tool results MUST preserve contract version, graph identity, evidence, ambiguity,
  ordering, completion, truncation, and omission metadata returned by the kernel.
- **FR-008**: Adapter errors MUST use stable machine-readable codes and sanitized actionable messages.
- **FR-009**: All v0.1 tools MUST be local-only, non-destructive, and must not perform network access.
- **FR-010**: The Python MCP SDK MUST be an optional, upper-bounded dependency so the core
  library remains usable without plugin support.
- **FR-011**: The plugin MUST contain a valid manifest, bundled `.mcp.json`, reusable skills, and a
  repo-local marketplace entry suitable for private distribution.
- **FR-012**: Skills MUST tell agents to check snapshot status and evidence freshness before claims.
- **FR-013**: Automated tests MUST cover service behavior, official MCP-client initialization,
  exact tool discovery, structured results, error behavior, and kernel conformance.
- **FR-014**: The adapter MUST document that hosted/untrusted ingestion, source mutation,
  MetaEditor control, persistent indexes, and a stable public MCP contract are out of scope.
- **FR-015**: Every bundled workflow skill MUST load a common consumer safety policy that treats the
  MQL5 CodeGraph source, marketplace, plugin source/cache, and runtime installation as immutable unless
  the user explicitly requests MQL5 CodeGraph maintenance.
- **FR-016**: Consumer installation guidance MUST use a non-editable package build and MUST reserve
  editable installs for explicit maintainer sessions.
- **FR-017**: The stdio entry point MUST emit bounded lifecycle evidence to stderr for startup, clean EOF,
  and unhandled failure without writing non-protocol content to stdout or exposing project data.

### Key Entities

- **Project Snapshot**: The active resolved root, include roots, exclusions, immutable graph,
  Intelligence Kernel, monotonically increasing session revision, identity, and counts.
- **MCP Tool Request**: A validated tool name and JSON arguments projected into either session
  management or an Intelligence Kernel v1 request.
- **MCP Tool Result**: Structured JSON data or a stable adapter error surfaced through the official
  MCP SDK.
- **Agent Skill**: Reusable workflow instructions that select tools, enforce evidence checks, and
  describe completion criteria.

## Success Criteria

### Measurable Outcomes

- **SC-001**: The official MCP Python client initializes the stdio server and lists the exact
  expected tool set in an automated test.
- **SC-002**: One hundred percent of reference MCP intelligence results match direct kernel results.
- **SC-003**: Indexing the reference fixture leaves its tracked file hashes unchanged.
- **SC-004**: Invalid indexing and pre-index query tests return stable codes and never crash the server.
- **SC-005**: Plugin and skill validators complete successfully with no placeholders or missing paths.
- **SC-006**: All existing Python, CLI, Web, frontend, package, and dependency gates continue to pass.
- **SC-007**: Automated tests fail if the plugin loses its read-only capability declaration, common
  consumer policy, skill policy references, or bytecode-write suppression.
- **SC-008**: An official-client regression keeps an indexed snapshot across a configurable idle interval,
  observes clean EOF telemetry on shutdown, and a unit regression observes unhandled-failure telemetry.

## Assumptions

- v0.1 is private, local, single-user, and experimental.
- Users explicitly trust each project root they ask the MCP server to index.
- The optional MCP extra is installed before the bundled server starts.
- The existing parser/resolver scaling risks remain accepted only for trusted local repositories.
- Source and tests remain more authoritative than an in-memory graph snapshot.
