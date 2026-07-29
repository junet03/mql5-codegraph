# Implementation Plan: Compiler Evidence Correlation

**Branch**: `codex/mql5-agent-plugin` | **Date**: 2026-07-29 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-compiler-correlation/spec.md`

## Summary

Add a backend-neutral compiler-evidence core that reads one operator-supplied MetaEditor log, verifies
the indexed project is still current, parses a constrained English log grammar, and correlates
location-backed findings to existing graph nodes. The report is ephemeral: it never alters `CodeGraph`,
source, the log, or the active MCP snapshot. CLI and MCP are thin projections over the same core.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Python standard library; optional `mcp>=1.28.1,<2` for the local stdio adapter

**Storage**: Request-local immutable reports only; no log, diagnostic, or compiler-state persistence

**Testing**: `unittest`, fixture logs, CLI unit tests, MCP service/protocol tests, full regression

**Target Platform**: Windows-first local CLI/Codex desktop; portable local Python process

**Project Type**: Python static-analysis library with CLI, loopback dashboard, and local MCP adapter

**Performance Goals**: Reject a log above 2 MiB before parsing; return deterministic correlation for
fixture logs without reading raw source through MCP or traversing an unbounded diagnostic list

**Constraints**: Trusted local project root only; log must be contained by that root; no MetaEditor
launching, compiler artifact writes, network access, graph mutation, snapshot mutation, or persistence;
preserve location/origin/completeness/freshness evidence explicitly

**Scale/Scope**: One English MetaEditor log grammar; at most 1,000 parsed diagnostics per report;
CLI and MCP only; dashboard visualization and MetaEditor process control are deferred

## Constitution Check

*GATE: Passed before Phase 0 research. Re-checked after Phase 1 design.*

- **MQL5 semantic fidelity — PASS**: compiler messages are observed external evidence and unsupported
  grammar is reported as incomplete rather than guessed.
- **Evidence-backed graph — PASS**: location is the only compiler-to-symbol mapping basis; compiler
  diagnostics remain separate from static diagnostics and graph edges.
- **Deterministic CLI contracts — PASS**: report ordering, fingerprints, error codes, and JSON shape are
  deterministic for the same graph, source state, and log bytes.
- **Test corpus before claims — PASS**: supported grammar and each freshness/correlation boundary require
  focused fixture logs before documentation claims support.
- **Small composable core — PASS**: compiler evidence lives in its own core module; CLI/MCP only request
  and serialize it.
- **Read-only and local boundary — PASS**: the feature reads a bounded local log and source metadata/
  identity only; it does not start MetaEditor, write `.ex5`/logs, or mutate the selected project.

## Project Structure

### Documentation

```text
specs/006-compiler-correlation/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── compiler-evidence-v1.md
└── tasks.md

docs/
├── decisions/ADR-0007-compiler-evidence-correlation.md
├── architecture.md
├── limitations.md
└── project-journal/
```

### Source Code

```text
src/mql5_codegraph/
├── compiler_evidence.py            # Parse, bound, validate, and correlate one compiler log
├── indexer.py                      # Reusable deterministic source-identity helper
├── cli.py                          # Stable compiler-evidence command
└── mcp/
    ├── service.py                  # Active-snapshot compiler-evidence projection
    └── server.py                   # Read-only MCP tool

tests/
├── fixtures/compiler_logs/          # Supported log variants only
├── test_compiler_evidence.py
├── test_cli.py
└── mcp_adapter/
    ├── test_service.py
    └── test_protocol.py
```

**Structure Decision**: Compiler evidence is an immutable result independent of `CodeGraph` and
`IntelligenceKernel`. A reusable source-identity helper confirms the graph fingerprint before adapter
code invokes the core; adapters do not parse logs, calculate freshness, or map diagnostics themselves.

## Complexity Tracking

No constitutional waiver is required. A separate core result prevents compiler-specific state from
polluting canonical static graph serialization or adapter-specific logic.
