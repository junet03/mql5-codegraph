# Experimental MCP Tool Contract v0.1

This surface is private and experimental. Tool names and argument shapes may change before a stable
MCP contract is declared.

## Tool catalog

| Tool | Required arguments | Purpose |
| --- | --- | --- |
| `project_status` | none | Return active snapshot state and identity without indexing |
| `index_project` | `root` | Build and publish an in-memory snapshot of a trusted local project |
| `query_symbols` | `target` | Resolve exact, qualified, normalized, or ambiguous symbol matches |
| `get_context` | `target` | Return bounded incoming/outgoing/both neighborhood evidence |
| `get_impact` | `target` | Return bounded upstream impact evidence |
| `find_paths` | `source`, `target` | Return bounded evidence-backed directed paths |
| `get_context_package` | `target` | Return a bounded deterministic AI context package |
| `get_diagnostics` | none | Return bounded graph diagnostics |

## Shared optional arguments

- `relationship_types`: array of graph relationship strings.
- `node_kinds`: array of node kinds, only for context packages.
- `direction`: `incoming`, `outgoing`, or `both`.
- `max_depth`: 0 to 5.
- `max_items`: 1 to 2000.
- `max_paths`: 1 to 20.
- `max_expansions`: 1 to 100000.
- `context_units`: 1 to 10000.
- `expected_source_fingerprint`: optional stale-snapshot guard.

`index_project` additionally accepts `include_roots` and `excluded` arrays.

## Result envelope

Successful intelligence tools return the exact `IntelligenceResult.to_dict()` object. Status and
index tools return adapter-owned deterministic objects. MCP structured output is authoritative; a
JSON text block is retained by the SDK for older clients.

## Errors

Adapter lifecycle/input failures use stable `AdapterError` codes. Intelligence validation and
execution failures preserve `IntelligenceError.to_dict()` inside the MCP tool error message.

## Annotations

All v0.1 tools advertise:

- `readOnlyHint = true`
- `destructiveHint = false`
- `idempotentHint = true`
- `openWorldHint = false`

`index_project` is read-only with respect to external state: it reads local files and replaces only
the server process's in-memory snapshot.
