# MQL5 CodeGraph

MQL5 CodeGraph is an offline static-analysis library and CLI that builds an evidence-backed graph
from MetaTrader 5 `.mq5` and `.mqh` source. It treats terminal callbacks as runtime relationships,
keeps inferred edges separate from source calls, and stores a deterministic backend-neutral JSON index.

## MVP capabilities

- Tolerant tokenizer that ignores comments and string contents during structural analysis.
- Extraction of includes, classes, structs, enums, functions, methods, event handlers, and calls.
- Project and custom include-root resolution.
- MetaTrader runtime dispatch edges for standard event handlers.
- Deterministic JSON, query/context/impact commands, and GraphML export.
- A versioned Intelligence Kernel shared by direct Python, normalized CLI, and normalized HTTP callers.
- Evidence-ranked directed paths and deterministic bounded structural context packages.
- Partial results with diagnostics for incomplete or unresolved code.

## Intelligence Kernel

`CodeGraph` is the backend-neutral canonical snapshot. `IntelligenceKernel` builds one immutable index
per snapshot and is the only authoritative interpreter for query, context, impact, diagnostics, directed
path, and context-package operations. CLI and Web remain thin projectors; GraphML and other
representation-only exporters may consume the canonical graph directly.

Normalized calls use contract `1.0.0`:

```powershell
mql5-codegraph intelligence query build/basic-ea.json CalculateLots --json
mql5-codegraph intelligence path build/basic-ea.json OnTick CalculateLots --json
mql5-codegraph intelligence context-package build/basic-ea.json CalculateLots --context-units 40 --json
```

The normalized HTTP equivalents are under `/api/v1/intelligence/*`. Existing unversioned CLI commands
and dashboard routes retain their frozen legacy shapes and defaults.

Relationship results preserve direction, type, origin, confidence, source location, and explicit evidence
state. Stored locations are references, not proof that a file is still present or unchanged.

## Private Codex plugin (experimental)

The repository includes `mql5-codegraph-intelligence`, a private local Codex plugin with four MQL5
workflow skills and eight read-only MCP tools. It projects the same Intelligence Kernel contract and does
not edit source, persist an index, or use the network.

```powershell
python -m pip install -e ".[mcp]"
codex plugin marketplace add D:\mql5-codegraph
codex plugin add mql5-codegraph-intelligence@mql5-codegraph-internal
```

Start a fresh Codex task after installation. The agent should call `project_status`, index an explicitly
trusted local root when needed, and re-index after source changes. The plugin is an internal alpha, not a
stable public MCP contract, and is not approved for hosted or untrusted-repository ingestion.

## Local dashboard

Build the dashboard once, then launch it against any local MQL5 repository:

```powershell
cd web
npm ci
npm run build
cd ..
mql5-codegraph serve --root C:\work\Example-MQL5
```

The dashboard provides interactive graph navigation, symbol search, context and impact traversal,
diagnostic filtering, and safe source evidence. It is a loopback-only, unauthenticated local tool: non-loopback
binds are rejected, request authorities are validated, idle reads time out after two seconds, and every
request read has a ten-second absolute deadline. It does not upload source.

## Development

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
mql5-codegraph analyze tests/fixtures/basic_ea --output build/basic-ea.json
mql5-codegraph status build/basic-ea.json --json
```

See [architecture](docs/architecture.md), [known limitations](docs/limitations.md), and the
[dashboard guide](docs/web-dashboard.md). Multi-session work is recorded in the
[project journal](docs/project-journal/README.md), with durable choices tracked as
[architecture decisions](docs/decisions/README.md).
