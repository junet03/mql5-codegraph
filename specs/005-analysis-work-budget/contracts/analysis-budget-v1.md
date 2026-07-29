# Analysis Work Budget Contract v1

## Scope

The work budget applies only while building a canonical graph from local MQL5 source. It is not a
network, wall-clock, persistence, or Intelligence Kernel traversal limit.

## Configuration

Analysis-starting callers accept an optional `max_work` integer. When omitted, the analyzer uses
1,000,000 work units. Values from 1 through 10,000,000 are valid; all other values fail validation
before source discovery begins.

| Entry point | Configuration | Success behavior |
| --- | --- | --- |
| Library | Optional `max_work`/budget argument | Returns a complete `CodeGraph` only |
| CLI `analyze` | `--max-work INTEGER` | Writes the requested graph only after complete analysis |
| Dashboard state | Optional request budget | Publishes a new job/graph only after complete analysis |
| MCP `index_project` | Optional `max_work` | Replaces the in-memory snapshot only after complete analysis |

## Failure payload

Budget exhaustion has the following stable fields, adapted to each entry point's existing error
envelope:

```json
{
  "code": "analysis_budget_exceeded",
  "message": "Analysis work budget exhausted",
  "details": {
    "phase": "resolution",
    "work_used": 100,
    "work_limit": 100
  }
}
```

The message text is human-readable; callers must use `code` and `details` for automation.

## Publication guarantee

- The core analyzer returns no graph on exhaustion.
- CLI does not create or overwrite the requested graph output on exhaustion.
- Dashboard and MCP keep their last complete graph/snapshot unchanged.
- A successful result continues to use existing graph/evidence contracts unchanged.

## Compatibility

Existing callers that omit `max_work` retain their current successful invocation shape. Existing
Intelligence Kernel query bounds are unaffected.
