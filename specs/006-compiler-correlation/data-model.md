# Data Model: Compiler Evidence Correlation

## CompilerEvidenceReport

One immutable correlation result for one static graph, current source observation, and one local compiler
log. It is never stored in `CodeGraph` or an MCP snapshot.

| Field | Meaning | Validation |
| --- | --- | --- |
| `source_fingerprint` | Identity from the graph being assessed | Non-empty graph metadata value |
| `current_source_fingerprint` | Fresh identity observed from selected sources | Equal only when graph is current |
| `log_fingerprint` | SHA-256 identity of bounded log bytes | Exactly 64 lowercase hexadecimal characters |
| `observed_at` | UTC modification timestamp of the log | ISO-8601 UTC string |
| `evidence_state` | Current usability | `current`, `stale`, or `incomplete` |
| `outcome` | Observed compiler result | `success`, `warnings`, `errors`, or `unknown` |
| `complete` | Parser found one valid supported summary | Boolean |
| `entry_file` | Project-relative requested compilation entry | Existing `.mq5` file inside root |
| `diagnostics` | Stable compiler findings | Sorted by normalized location, severity, code, message |

### State derivation

```text
valid bounded log + supported summary
  + graph source identity matches current root
  + log not older than selected source files
  -> current

valid bounded log + supported summary + any stale identity/timestamp condition
  -> stale

valid bounded log + missing/unsupported summary or count mismatch
  -> incomplete
```

Invalid path, unreadable bytes, a log above the size bound, and invalid entry selection are stable request
errors rather than reports.

## CompilerDiagnostic

| Field | Meaning |
| --- | --- |
| `severity` | Observed `error` or `warning` |
| `code` | Optional compiler error number, preserved as text |
| `message` | Parsed compiler message without raw surrounding log context |
| `location` | Optional project-normalized file, line, and column |
| `correlation` | Exact location result described below |

## LocationCorrelation

| State | Meaning |
| --- | --- |
| `exact` | One graph declaration has the diagnostic's project-contained file and line |
| `no_declaration` | Location is contained but no graph declaration starts at that line |
| `ambiguous` | More than one graph declaration shares the exact location |
| `outside_project` | Compiler location does not resolve under the selected root |
| `unlocated` | Parser received no usable file-and-line location |

Only `exact` contains `symbol_id`, `qualified_name`, and an origin of `compiler_location`.
