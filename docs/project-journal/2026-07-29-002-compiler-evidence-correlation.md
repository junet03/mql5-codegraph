# 2026-07-29 — Compiler evidence correlation

## Objective

Give local operators and agents bounded, evidence-backed visibility of an explicitly supplied MetaEditor
compiler log without turning static analysis into compiler control or runtime proof.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `d6beb20`, with the preceding analyzer work-budget
  implementation still uncommitted in the shared worktree.
- Relevant specification: `specs/006-compiler-correlation/`.
- Known constraints: the verified local MT5 installation has no discoverable MetaEditor executable;
  compilation process control can write artifacts and remains out of scope.

## Work completed

- Added a backend-neutral compiler-evidence core with a 2 MiB log bound, 1,000-diagnostic limit,
  deterministic log/source fingerprints, freshness states, and immutable report serialization.
- Added conservative source identity checks before and after log parsing. A graph mismatch, newer source,
  or changed source observation cannot be reported as current evidence.
- Added exact file-and-line compiler-to-symbol correlation plus explicit `no_declaration`,
  `outside_project`, `unlocated`, and `ambiguous` states. Compiler text never creates a symbol link.
- Exposed the same core through `compiler-evidence` CLI and the ninth read-only MCP tool
  `correlate_compiler_log`. Both keep graph, source, log, and active MCP snapshot unchanged.
- Added supported English log fixtures and direct, CLI, MCP-service, and official-MCP-stdio regressions.
- Updated the README, MCP contract, architecture, limitations, changelog, and compiler-evidence contract.

## Decisions

- Accepted [ADR-0007](../decisions/ADR-0007-compiler-evidence-correlation.md): V1 only reads an
  operator-supplied bounded log and does not launch MetaEditor or write artifacts.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Focused compiler regressions | `$env:PYTHONPATH='src'; python -m unittest tests.test_compiler_evidence tests.test_cli tests.mcp_adapter.test_service tests.mcp_adapter.test_protocol` | Passed: 27 tests. |
| Syntax compilation | `python -m compileall -q src tests tools` | Passed. |
| Quickstart | Commands in `specs/006-compiler-correlation/quickstart.md` | Passed: fixture report was `current` / `success` with matching graph and source fingerprints. Removed the copied fixture log and temporary graph afterwards. |
| Full Python suite | `$env:PYTHONPATH='src'; python -m unittest discover -s tests` | Passed: 132 tests. |
| Graphify update | `graphify . --update --directed --no-viz --code-only` | Updated generated graph to 1,813 nodes and 3,205 edges. The code-only run deliberately skipped 67 changed documentation/image files because no approved semantic backend was available. |
| Directed graph health | `python -m graphify diagnose multigraph --graph graphify-out/graph.json --directed --json` | Passed: directed `DiGraph`; 0 dangling, missing, self-loop, duplicate, or collapsed edges. |

## Risks and unresolved questions

- V1 recognizes only the documented English summary and diagnostic forms. Localized, altered, missing, or
  count-mismatched logs deliberately return incomplete evidence.
- Current-state observation is a best-effort double source scan on a mutable filesystem; no filesystem lock
  is taken. It is conservative when change is observed but cannot prove an immutable operating-system view.
- The local Graphify package is `0.9.20` while its installed skill is `0.9.27`; it emitted a compatibility
  warning. The update was completed, but no global toolchain upgrade was made.
- `graphify . --update --directed` wrote an undirected JSON flag despite directed edges. The generated
  graph flag was corrected mechanically before the successful directed health diagnostic; this is a
  Graphify runtime behavior to revisit when upgrading the toolchain.

## Next objective

Pilot compiler correlation against one explicitly trusted MQL5 project using a real operator-provided
MetaEditor log, then decide whether another documented grammar or carefully authorized compiler control is
needed.
