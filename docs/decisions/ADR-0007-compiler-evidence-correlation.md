# ADR-0007: Compiler evidence correlation without compiler control

- Status: Accepted
- Date: 2026-07-29
- Owners: Project maintainers

## Context

The static MQL5 graph can preserve structural source evidence but cannot claim MetaEditor compiler
parity. Agents need a way to distinguish observed compiler results from static diagnostics and to avoid
using stale logs after a source or graph change. The verified local MT5 terminal installation has no
discoverable MetaEditor executable, and command-line compilation writes generated artifacts beside source.

## Decision

- Accept only an operator-supplied, bounded local MetaEditor log as compiler evidence; V1 does not launch
  MetaEditor, compile source, or write `.ex5`/log artifacts.
- Parse one documented English log grammar, including `Result: <errors> errors, <warnings> warnings` and
  file/line/column error or warning records. Unsupported, missing, and count-mismatched summaries remain
  incomplete evidence rather than a success claim.
- Recompute the selected root's source identity and compare it with the static graph fingerprint; require
  the log to be no older than the selected source files before reporting current evidence.
- Keep compiler evidence as an immutable request result. It must not change the canonical `CodeGraph`,
  static diagnostics, MCP snapshot, source tree, or log.
- Map a compiler diagnostic to a symbol only from an exact project-contained source location. No message
  text or fuzzy identifier matching can create a compiler-to-symbol association.

## Consequences

- Positive: agents receive explicit current/stale/incomplete compiler evidence and can investigate exact
  locations without treating external observations as static graph facts.
- Positive: the existing local read-only/no-network boundary is preserved.
- Cost: operators must explicitly compile trusted projects and provide a log; localized or vendor-modified
  logs need fixtures and an explicit grammar extension.
- Limit: compiler success does not prove strategy behavior, broker acceptance, runtime dispatch, or the
  absence of logical defects.

## Guardrails

- CLI and MCP adapters delegate parsing, freshness, and mapping to the backend-neutral core.
- Bounded logs and diagnostics must not reveal raw surrounding log text in errors.
- Any MetaEditor process-control capability requires a new security review, explicit operator authority,
  temporary-output design, and real executable validation.
