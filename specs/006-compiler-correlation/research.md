# Research: Compiler Evidence Correlation

## Decision: ingest MetaEditor logs; do not control MetaEditor in V1

- **Rationale**: The installed MT5 terminal has no discoverable `metaeditor.exe` or `metaeditor64.exe`.
  MetaEditor command-line compilation can create `.ex5` and log artifacts beside source, which conflicts
  with the project's read-only analyzer boundary. An operator-provided log is useful external evidence
  without granting an agent process-control or project-write authority.
- **Alternatives considered**:
  - Launch MetaEditor directly: rejected for V1 because it writes compiler artifacts, is not installed in
    the verified local terminal, and needs a separate explicit authorization/security design.
  - Treat static parser diagnostics as compiler evidence: rejected because structural analysis has no
    compiler parity claim.

## Decision: support a narrow English log grammar and make unsupported evidence incomplete

- **Rationale**: MetaEditor documentation identifies `0 errors` as successful compilation and allows
  warnings. A documented log sample shows `Result: 0 errors, 0 warnings, ...`; compiler findings carry
  file, line, column, severity, and message. The parser will accept only a case-insensitive English
  `Result: <errors> errors, <warnings> warnings` summary plus `path(line,column) : severity [code:] message`
  records and explicitly unlocated `severity [code:] message` records. It will not infer a symbol from
  message text or localized summaries.
- **Alternatives considered**:
  - Parse every log locale heuristically: rejected because it would convert ambiguous text into false
    current/success claims.
  - Retain raw logs for later extraction: rejected by no-persistence and raw-source exposure boundaries.

## Decision: verify both graph identity and timestamp freshness conservatively

- **Rationale**: A log newer than files alone does not prove that the active static graph represents
  current sources. The correlation core will recompute the selected root's deterministic source
  fingerprint, compare it with the graph identity, then require the log modification time to be no older
  than every discovered source. Missing, unreadable, changed, or timestamp-anomalous evidence becomes
  `stale` or `incomplete`.
- **Alternatives considered**:
  - Assume active MCP snapshots are current: rejected because users can edit source after indexing.
  - Use only a log timestamp: rejected because it cannot detect a stale graph snapshot.

## Decision: correlate only by contained exact location

- **Rationale**: A compiler file/line can map deterministically to graph declarations with the exact
  location. Other findings are still useful but are labeled `no_declaration`, `outside_project`, or
  `ambiguous`; no symbol is guessed from identifier-looking message text.
- **Alternatives considered**:
  - Fuzzy-message symbol matching: rejected because compiler prose can name unrelated symbols and would
    violate the evidence-origin rule.
  - Add compiler diagnostics to `CodeGraph.diagnostics`: rejected because it would make a static graph
    depend on transient external evidence and break deterministic source-only serialization.

## Evidence consulted

- MQL5 reference documents compiler errors/warnings and says errors prevent compilation.
- MQL5's development-environment guide identifies `0 errors` as successful compilation and notes that
  warnings do not prevent an `.ex5` output.
- MQL5 command-line guidance states `/compile` with `/log` writes a log alongside source; process control
  is intentionally deferred in this feature.
