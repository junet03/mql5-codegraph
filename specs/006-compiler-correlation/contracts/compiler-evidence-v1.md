# Compiler Evidence Contract v1

## Scope

Compiler evidence is an ephemeral report for an existing canonical graph and an operator-supplied local
MetaEditor log. It does not compile MQL5, write artifacts, persist diagnostics, alter graph serialization,
or replace an MCP snapshot.

## CLI

```text
mql5-codegraph compiler-evidence GRAPH --entry RELATIVE_FILE --log RELATIVE_OR_ABSOLUTE_LOG [--exclude NAME] [--json]
```

`GRAPH` must carry an existing project root and source fingerprint. `--entry` and `--log` must resolve
inside that root; `--exclude` repeats the source-discovery exclusions used when the graph was made.

## Supported log grammar and bounds

V1 accepts exactly one case-insensitive English summary in the form
`Result: <errors> errors, <warnings> warnings`. It recognizes at most 1,000 diagnostic records in either
`path(line,column) : error|warning [code]: message` form or unlocated
`error|warning [code]: message` form. The log may be at most 2 MiB. Unrecognized surrounding lines are
not retained. UTF-8 (with or without a BOM) and BOM-marked UTF-16 LE/BE logs are supported; UTF-16
without a BOM is not guessed. A missing, repeated, localized, or count-mismatched summary makes the
otherwise readable report `incomplete`.

## MCP

```text
correlate_compiler_log(log_path, entry_file)
```

The tool requires an active complete project snapshot. It returns the same report content as the CLI for
the same snapshot, root state, entry, active-snapshot exclusions, and log bytes.

## Success result

```json
{
  "contract_version": "1.0.0",
  "graph_identity": {
    "schema_version": "1.0.0",
    "source_fingerprint": "<sha256>"
  },
  "compiler_evidence": {
    "evidence_state": "current",
    "outcome": "warnings",
    "complete": true,
    "entry_file": "Experts/Example.mq5",
    "log_fingerprint": "<sha256>",
    "observed_at": "2026-07-29T00:00:00Z",
    "diagnostics": [
      {
        "severity": "warning",
        "code": "123",
        "message": "example warning",
        "location": {"file": "Experts/Example.mq5", "line": 10, "column": 5},
        "correlation": {
          "state": "exact",
          "origin": "compiler_location",
          "symbol_id": "symbol:<id>",
          "qualified_name": "OnTick"
        }
      }
    ]
  }
}
```

Callers must use `evidence_state`, `outcome`, `complete`, and correlation `state` rather than inferring
compiler validity from an empty diagnostic array.

## Failure behavior

All failure envelopes retain the adapter's existing JSON shape. Stable codes include:

| Code | Meaning |
| --- | --- |
| `compiler_log_invalid` | Log is empty or cannot provide recoverable text for bounded parsing |
| `compiler_log_outside_root` | Requested log or entry escapes the selected trusted root |
| `compiler_log_too_large` | Log exceeds the documented 2 MiB bound |
| `compiler_log_unreadable` | Log could not be read as recoverable local text |
| `project_not_indexed` | MCP request has no active complete snapshot |
| `compiler_correlation_failed` | Safe correlation boundary failed without exposing raw log contents |

## Compatibility

Existing graph schema, analyzer diagnostics, intelligence contracts, MCP tools, and CLI commands retain
their current behavior. Compiler evidence is a new optional command/tool and has no effect until an
operator supplies a log. A non-empty log with a missing, unsupported, or count-mismatched summary is a
successful correlation response with `evidence_state: "incomplete"`, not an error.
