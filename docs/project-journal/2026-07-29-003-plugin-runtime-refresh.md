# 2026-07-29 — Plugin runtime refresh

## Objective

Build, install, and verify the private MCP runtime that contains the analyzer work budget and compiler
evidence features, then refresh the cache-busted Codex plugin manifest.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `d6beb20`, with approved uncommitted maintenance work.
- Relevant specifications: `specs/005-analysis-work-budget/` and
  `specs/006-compiler-correlation/`.
- Constraint: do not infer an MQL5 analysis target from this toolchain repository. A real-project pilot
  needs an explicitly selected trusted root.

## Work completed

- Bumped the private plugin manifest to `0.1.0+codex.20260729205910` so Codex can refresh its cached
  plugin instructions and capability metadata.
- Built `dist/mql5_codegraph-0.2.0-py3-none-any.whl` from the current checkout and force-reinstalled the
  non-editable wheel into `C:\Python314\Lib\site-packages`.
- Reinstalled `mql5-codegraph-intelligence@mql5-codegraph-internal`; Codex now reports the refreshed
  manifest version and cache path.
- Verified the installed `mql5-codegraph-mcp` executable through an official MCP stdio client: it exposed
  exactly nine tools and correlated the isolated fixture log as `current` / `success`.
- Updated consumer quickstart text to include the compiler-correlation tool.

## Decisions

- No new ADR: this is the rebuild/reinstall consequence of ADR-0005, not a new architecture or boundary.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Wheel build | `uvx --from build pyproject-build --wheel` | Passed; wheel includes `compiler_evidence.py` and MCP adapter changes. |
| Non-editable runtime | `python -m pip show mql5-codegraph` and import-location check | Passed; package imports from `C:\Python314\Lib\site-packages`, not the source checkout. |
| Dependency consistency | `python -m pip check` | No broken requirements. |
| Codex plugin refresh | `codex plugin add mql5-codegraph-intelligence@mql5-codegraph-internal --json` | Installed version `0.1.0+codex.20260729205910`. |
| Installed MCP protocol | Official stdio `ClientSession` against `mql5-codegraph-mcp` | Passed: 9 tools; fixture compiler evidence was `current` / `success`. |
| Source regression suite | `$env:PYTHONPATH='src'; python -m unittest discover -s tests` | Passed: 132 tests. |
| Syntax compilation | `python -m compileall -q src tests tools` | Passed. |
| Directed Graphify refresh | `graphify . --update --directed --no-viz --code-only` plus `graphify diagnose multigraph --directed --json` | Passed: 1,813 nodes / 3,205 edges; directed health had 0 dangling, missing, self-loop, duplicate, or collapsed edges. |

## Risks and unresolved questions

- Five old MCP server processes held the console executable lock during reinstall. They were stopped as
  part of the approved runtime refresh; their in-memory snapshots were ephemeral and must be re-indexed.
- Pip left `~ql5_codegraph*` backup directories from the initial lock-conflicted uninstall. The new wheel
  is healthy and `pip check` passes, but the execution environment rejected cleanup of those external
  backup directories; they may cause a harmless pip warning until an operator removes them.
- Graphify skipped 69 documentation/image files because no approved semantic backend was available and
  classified the plugin manifest as an empty JSON source. The directed code graph itself is healthy.
- No trusted real MQL5 project root or operator-provided MetaEditor log has been selected for the pilot.

## Next objective

Run the release gate and compiler-evidence pilot against one Sếp-selected trusted MQL5 project root and
its supplied compiler log; report it as conditional unless external MetaEditor compilation is evidenced.
