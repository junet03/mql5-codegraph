# Experimental MCP Tool Contract v0.1

This surface is private and experimental. Tool names and argument shapes may change before a stable
MCP contract is declared.

## Tool catalog

| Tool | Required arguments | Purpose |
| --- | --- | --- |
| `project_status` | none | Return active snapshot state and identity without indexing |
| `index_project` | `root` | Build and publish an in-memory snapshot of a trusted local project |
| `correlate_compiler_log` | `log_path`, `entry_file` | Correlate a supplied bounded MetaEditor log with the active snapshot |
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

`index_project` additionally accepts `include_roots` and `excluded` arrays plus optional `max_work`.
When omitted, source analysis uses 1,000,000 deterministic work units; values from 1 through 10,000,000
are valid. Exhaustion returns `analysis_budget_exceeded` with `phase`, `work_used`, and `work_limit` and
does not replace an active snapshot. Its structured details identify `analyzer_work_units`, explicitly
exclude model-token/account quota exhaustion, and order retry actions so callers narrow `root` and
`include_roots` before increasing `max_work`.

`correlate_compiler_log` uses the active snapshot's root and exclusions. Both paths must resolve inside
that trusted root; it never launches MetaEditor, writes compiler artifacts, or changes the snapshot. Its
separate compiler-evidence envelope is specified in
[`specs/006-compiler-correlation/contracts/compiler-evidence-v1.md`](../../006-compiler-correlation/contracts/compiler-evidence-v1.md).

## Result envelope

Successful intelligence tools return the exact `IntelligenceResult.to_dict()` object. Status and
index tools return adapter-owned deterministic objects. Compiler correlation returns its versioned
compiler-evidence envelope. MCP structured output is authoritative; a
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
the server process's in-memory snapshot. `correlate_compiler_log` reads a bounded supplied log and current
source identity without mutating the filesystem, graph, or snapshot.

## Transport lifecycle

The entry point writes one-line JSON lifecycle records to stderr with prefix
`mql5-codegraph-mcp.lifecycle `. Records contain only schema version, timestamp, event, PID/parent PID,
server/transport name, Python/package/SDK versions, and a bounded reason/exception type. They never contain
project roots, tool arguments, graph data, source, compiler logs, credentials, or environment values.

- `starting`: emitted before the FastMCP stdio run loop.
- `stopped` / `stdio_eof`: emitted when the run loop returns after host input closes.
- `crashed` / `unhandled_exception`: emitted before an unhandled server exception is re-raised.

Lifecycle records are diagnostic evidence, not MCP tool results. The server cannot repair a client that
already holds a dead transport. The host must spawn and initialize a new process; callers must then treat
the old in-memory snapshot as lost and re-index explicitly.
