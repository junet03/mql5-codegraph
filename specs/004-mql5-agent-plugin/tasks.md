# Tasks: MQL5 Agent Plugin and MCP Alpha

**Input**: Design documents from `specs/004-mql5-agent-plugin/`

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Required by the approved specification.

## Phase 1: Contract and scaffolding

- [x] T001 Define the approved feature, design, tool contract, data model, and verification plan in `specs/004-mql5-agent-plugin/`
- [x] T002 Add the optional MCP SDK dependency and stdio entry point in `pyproject.toml`
- [x] T003 Scaffold `plugins/mql5-codegraph-intelligence/` and `.agents/plugins/marketplace.json` with the plugin-creator workflow

## Phase 2: Foundational service

- [x] T004 [P] Add failing snapshot lifecycle, invalid-root, no-project, atomic replacement, and source-immutability tests in `tests/mcp_adapter/test_service.py`
- [x] T005 Implement stable adapter errors and transactional `ProjectSession` indexing in `src/mql5_codegraph/mcp/service.py`
- [x] T006 Implement one-to-one Intelligence Kernel request projection in `src/mql5_codegraph/mcp/service.py`

## Phase 3: MCP protocol adapter

- [x] T007 [P] Add failing official-client stdio handshake, exact tool-list, structured-result, and tool-error tests in `tests/mcp_adapter/test_protocol.py`
- [x] T008 Register the eight experimental tools with non-destructive annotations in `src/mql5_codegraph/mcp/server.py`
- [x] T009 Add package exports and the `mql5-codegraph-mcp` console entry point

## Phase 4: Plugin skills

- [x] T010 [P] Write project onboarding and freshness workflow in `plugins/mql5-codegraph-intelligence/skills/mql5-project-onboarding/SKILL.md`
- [x] T011 [P] Write evidence-first architecture navigation in `plugins/mql5-codegraph-intelligence/skills/mql5-architecture/SKILL.md`
- [x] T012 [P] Write change-impact and path analysis in `plugins/mql5-codegraph-intelligence/skills/mql5-change-impact/SKILL.md`
- [x] T013 [P] Write local release/security gate guidance in `plugins/mql5-codegraph-intelligence/skills/mql5-release-gate/SKILL.md`
- [x] T014 Configure the bundled stdio server and final plugin metadata in `.mcp.json` and `.codex-plugin/plugin.json`

## Phase 5: Verification and release

- [x] T015 Validate every skill and the complete plugin with official local validators
- [x] T016 Run MCP-focused tests, the full Python suite, compileall, frontend lint/build, package build, and dependency audits
- [x] T017 Run a real plugin/MCP smoke against the reference MQL5 fixture and record evidence in `quickstart.md`
- [x] T018 Add or update the architecture ADR, README/architecture documentation, journal entry, and journal indexes
- [x] T019 Run incremental directed Graphify update and surface graph health
- [x] T020 Inspect staged scope, run `git diff --cached --check`, commit with Conventional Commits, and push the private feature branch

## Completion Rule

The feature is complete only when the official client can use the bundled server, MCP results conform
to the direct kernel, all plugin paths validate, no source file is mutated by indexing, existing gates
pass, generated output remains uncommitted, and exact evidence is recorded.
