# Implementation Plan: Analyzer Work Budget

**Branch**: `codex/mql5-agent-plugin` | **Date**: 2026-07-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-analysis-work-budget/spec.md`

## Summary

Introduce one deterministic `AnalysisBudget` owned by the canonical analysis pipeline. Source discovery,
lexing/parsing, graph resolution, and runtime enrichment consume work units through this shared budget.
On exhaustion, a typed failure records the active phase, used work, and limit; no graph is returned or
published. The library, CLI, dashboard, and MCP adapter use the same pipeline contract. MCP keeps the
last valid immutable snapshot when a refresh fails.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Python standard library; optional `mcp>=1.28.1,<2` for the local stdio adapter

**Storage**: In-memory graph snapshots and optional existing CLI exports; no new files, caches, or persistence

**Testing**: `unittest`, MCP official-client adapter tests, CLI unit tests, dashboard state tests, full regression

**Target Platform**: Windows-first local CLI/Codex desktop; portable local Python process

**Project Type**: Python static-analysis library with CLI, loopback dashboard, and local MCP adapter

**Performance Goals**: Supported fixtures finish within the default deterministic work limit; every
budget-exhaustion fixture stops before consuming more than one unit above its limit

**Constraints**: Local trusted roots only; no source writes/network access; no partial graph publication;
preserve evidence and deterministic successful output; a work budget is not a wall-clock guarantee

**Scale/Scope**: One budget per analysis request across discovery, parser, resolver, and runtime enrichment;
no MetaEditor integration, persistence, remote/multi-user ingestion, or public MCP stabilization

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

- **MQL5 semantic fidelity — PASS**: exhausted analysis reports a typed limitation instead of silently
  returning partial or inferred relationships.
- **Evidence-backed graph — PASS**: only a complete graph can be published; successful evidence and
  relationship origin are unchanged.
- **Deterministic CLI contracts — PASS**: work units, validation, and failure payloads are stable and
  machine-readable; successful re-indexes remain deterministic.
- **Test corpus before claims — PASS**: focused fixtures cover the accepted parser/resolver amplification
  paths and all adapter failure boundaries.
- **Small composable core — PASS**: the core budget is independent of CLI, dashboard, MCP, storage, and UI.
- **Read-only and local boundary — PASS**: no analysis path writes the selected MQL5 root or introduces
  persistence/network access.

## Project Structure

### Documentation

```text
specs/005-analysis-work-budget/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── analysis-budget-v1.md
└── tasks.md

docs/
├── decisions/ADR-0006-analysis-work-budget.md
├── limitations.md
└── project-journal/
```

### Source Code

```text
src/mql5_codegraph/
├── analysis_budget.py             # Canonical budget accounting and typed exhaustion
├── indexer.py                     # One analysis budget shared across phases
├── lexer.py                       # Lexer accounting
├── parser.py                      # Parser and binding/call accounting
├── resolver.py                    # Include and call-resolution accounting
├── runtime.py                     # Runtime-enrichment accounting
├── cli.py                         # --max-work validation and stable failure output
├── web/api.py                      # Dashboard request validation
├── web/state.py                   # Dashboard job failure/publish boundary
└── mcp/
    ├── service.py                 # Transactional snapshot behavior
    └── server.py                  # Optional max_work tool argument

tests/
├── test_analysis_budget.py
├── test_indexer.py
├── test_cli.py
├── test_web_state.py
└── mcp_adapter/test_service.py
```

**Structure Decision**: Budget semantics live in a core module and flow downward into the existing
analyzer. Adapters only validate/request the configured limit and translate the typed outcome; they
never implement their own accounting policy.

## Complexity Tracking

No constitutional waiver is required. The implementation adds a small core module and propagates one
explicit dependency through analysis functions; this is necessary to enforce a single budget across
all supported entry points.
