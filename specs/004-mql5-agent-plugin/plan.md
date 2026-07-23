# Implementation Plan: MQL5 Agent Plugin and MCP Alpha

**Branch**: `codex/mql5-agent-plugin` | **Date**: 2026-07-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-mql5-agent-plugin/spec.md`

## Summary

Add a thin experimental MCP stdio adapter above `IntelligenceKernel`, maintain one in-memory project
snapshot per server process, and package the adapter with evidence-first Codex skills in a private
repo-local plugin marketplace. The adapter uses the official MCP Python SDK as an optional dependency
and does not persist graphs, mutate MQL5 source, or introduce analysis logic.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Existing standard-library core; optional `mcp>=1.28.1,<2`

**Storage**: In-memory active project snapshot only; no new persistent runtime state

**Testing**: `unittest`, official MCP client over stdio, plugin/skill validators, existing release gates

**Target Platform**: Windows-first local Codex desktop/CLI; portable stdio server

**Project Type**: Python library/CLI plus private Codex plugin

**Performance Goals**: Adapter overhead remains negligible relative to analysis; bounded kernel operations
retain Feature 003 thresholds

**Constraints**: Local trusted repositories only, no source writes, no network access, deterministic
structured output, optional dependency isolation, experimental MCP surface

**Scale/Scope**: One active project snapshot per MCP process; eight read-only tools and four initial skills

## Constitution Check

*GATE: Passed before implementation and must be re-checked after validation.*

- **Backend neutrality — PASS**: MCP imports only the public indexer, graph, and Intelligence Kernel surfaces.
- **Evidence fidelity — PASS**: Tool output is the serialized kernel contract; the adapter adds no inferred facts.
- **Read-only boundary — PASS**: Indexing reads trusted local files into memory and never saves or edits them.
- **Determinism — PASS**: Kernel ordering and contract serialization remain authoritative.
- **Security boundary — PASS WITH KNOWN LIMIT**: Local trusted repositories only; analyzer-wide work budgets
  remain a prerequisite for hosted untrusted ingestion.
- **Dependency discipline — PASS**: The official SDK is optional and capped below its imminent breaking major.
- **Adapter thinness — PASS**: Session management and protocol projection are separate from analysis semantics.

## Project Structure

### Documentation

```text
specs/004-mql5-agent-plugin/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── mcp-tools-v0.1.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code

```text
src/mql5_codegraph/mcp/
├── __init__.py
├── service.py                  # Pure snapshot state and kernel projection
└── server.py                   # Official SDK registration and stdio entry point

tests/mcp_adapter/
├── __init__.py
├── test_service.py
└── test_protocol.py

plugins/mql5-codegraph-intelligence/
├── .codex-plugin/plugin.json
├── .mcp.json
└── skills/
    ├── mql5-project-onboarding/SKILL.md
    ├── mql5-architecture/SKILL.md
    ├── mql5-change-impact/SKILL.md
    └── mql5-release-gate/SKILL.md

.agents/plugins/marketplace.json
```

**Structure Decision**: MCP protocol code lives beside other adapters in the Python package while
plugin distribution files remain under `plugins/`. The Intelligence Kernel remains unaware of MCP,
Codex, skills, marketplaces, and session roots.

## Delivery Sequence

1. Freeze the experimental tool catalog and error contract.
2. Add service tests that fail before the adapter exists.
3. Implement transactional in-memory indexing and kernel request projection.
4. Register tools through the official SDK and prove a real stdio client handshake.
5. Scaffold and validate the repo-local plugin and marketplace.
6. Add evidence-first skills, documentation, audits, Graphify refresh, and release evidence.

## Complexity Tracking

No constitution violation requires a waiver. The optional SDK adds transitive packages only when the
MCP extra is installed; the base package dependency set remains unchanged.
