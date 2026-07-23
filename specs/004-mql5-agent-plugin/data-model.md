# Data Model: MQL5 Agent Plugin and MCP Alpha

## ProjectSnapshot

| Field | Type | Rules |
| --- | --- | --- |
| `root` | absolute path | Existing local directory explicitly supplied by the caller |
| `include_roots` | tuple of absolute paths | Deterministically sorted and de-duplicated |
| `excluded` | tuple of strings | Deterministically sorted and de-duplicated |
| `revision` | positive integer | Increments only after successful publication |
| `graph` | `CodeGraph` | In-memory canonical snapshot |
| `kernel` | `IntelligenceKernel` | Built from the same graph instance |

Derived status fields are file, node, edge, diagnostic counts and `kernel.graph_identity`.

## AdapterError

| Field | Type | Meaning |
| --- | --- | --- |
| `code` | stable string | Machine-readable adapter category |
| `message` | string | Sanitized actionable explanation |
| `details` | object | Optional non-secret structured context |

Initial codes: `project_not_indexed`, `invalid_project_root`, `invalid_tool_arguments`,
`analysis_failed`, and `intelligence_error`.

## State transitions

```text
not_indexed --index success--> indexed(revision=1)
indexed(N) --index success--> indexed(N+1)
not_indexed --index failure--> not_indexed
indexed(N) --index failure--> indexed(N)
```

Intelligence tools never change the state. `project_status` only observes it.
