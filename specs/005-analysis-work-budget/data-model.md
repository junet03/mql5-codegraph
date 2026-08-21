# Data Model: Analyzer Work Budget

## AnalysisBudget

Represents one mutable, request-scoped accounting authority owned by the analyzer.

| Field | Meaning | Validation |
| --- | --- | --- |
| `work_limit` | Maximum permitted deterministic work units | Integer from 1 through 10,000,000; defaults to 1,000,000 |
| `work_used` | Units consumed before the current action | Starts at zero; never decreases |
| `phase` | Named active analysis phase | One of source discovery, lexing, parsing, resolution, or runtime enrichment |

### Transitions

```text
created -> consuming -> completed
                    -> exhausted
```

`completed` produces one complete graph. `exhausted` produces no graph and cannot transition back to
`consuming`; a caller must begin a new analysis request.

## AnalysisBudgetExceeded

Represents the typed, recoverable failure emitted when the next accounted unit would exceed the limit.

| Field | Meaning |
| --- | --- |
| `code` | Stable identifier: `analysis_budget_exceeded` |
| `phase` | The phase whose next work unit could not start |
| `work_used` | Work consumed before rejection |
| `work_limit` | Configured maximum for the request |
| `budget_kind` | Stable discriminator: `analyzer_work_units` |
| `not_model_token_limit` | Explicitly distinguishes analyzer work from model/account quotas |
| `recommended_actions` | Ordered machine-readable retry policy: narrow root, narrow include roots, then increase work |
| `maximum_max_work` | Maximum accepted explicit work limit |

This entity contains no source contents, paths beyond the caller's existing root context, graph nodes,
or partial evidence.

## PublishedSnapshot

The existing complete MCP/dashboard graph state. It has an optional relationship to an
`AnalysisBudget`: only a completed budget can create a replacement snapshot. An exhausted budget has
no replacement relationship, so the previous snapshot remains visible.
