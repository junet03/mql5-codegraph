# 2026-07-29 — UTF-16 compiler-log support and DCA dashboard pilot

## Objective

Make compiler-evidence correlation handle the BOM-marked UTF-16 MetaEditor log found in the explicitly
selected DCA-Matrix-Junet project, then verify the installed plugin runtime and local dashboard.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `d6beb20`, with the preceding work-budget and compiler
  evidence implementation intentionally uncommitted.
- Relevant specification: `specs/005-analysis-work-budget/` and `specs/006-compiler-correlation/`.
- Known constraints: `D:\Antigravity-MQL5\Experts\DCA-Matrix-Junet` is an analysis-only target; no source,
  MetaTrader, or compiler artifact in that project may be changed. The existing log is UTF-16 LE with a BOM.

## Work completed

- Added BOM-based UTF-16 LE/BE decoding to `compiler_evidence.py`; UTF-16 without a BOM is intentionally
  not guessed. Decode recovery still makes the evidence incomplete rather than successful.
- Added a UTF-16 regression test and updated the public contract, README, limitations, changelog, and plugin
  quickstart.
- Rebuilt and non-editably reinstalled `mql5-codegraph` 0.2.0, then cache-busted and installed plugin
  `mql5-codegraph-intelligence` `0.1.0+codex.20260729212553`.
- Used the installed MCP executable to index the DCA project and correlate its supplied log. The evidence is
  now `current`, `complete`, and `warnings`, with five code-89 `POSITION_COMMISSION` deprecation warnings.
- Restarted the loopback-only dashboard at `http://127.0.0.1:8766/` for the DCA project and verified its
  rendered graph and diagnostics. No files were written to the DCA project.

## Decisions

- Support only UTF-8 plus BOM-marked UTF-16. BOM detection is deterministic and avoids treating arbitrary
  byte streams or UTF-16-without-BOM logs as trustworthy text.
- Preserve exact-location-only diagnostic correlation. The five DCA findings remain `no_declaration` because
  they point to expressions, not declaration lines; the adapter does not guess a symbol.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Source regression suite | `$env:PYTHONPATH = (Join-Path (Get-Location) 'src'); python -m unittest discover -s tests` | 133 tests passed. |
| Python compilation | `$env:PYTHONPATH = (Join-Path (Get-Location) 'src'); python -m compileall -q src tests` | Passed. |
| Patch integrity | `git diff --check` | Passed; only existing line-ending warnings from Git. |
| Wheel build | `uvx --from build pyproject-build --wheel` | Built `dist/mql5_codegraph-0.2.0-py3-none-any.whl`. |
| Installed runtime | `python -m pip install --force-reinstall --no-deps ...`; `python -m pip check` | Wheel installed; dependency check reports no broken requirements. |
| Plugin refresh | `codex plugin add mql5-codegraph-intelligence@mql5-codegraph-internal --json` | Installed and enabled at version `0.1.0+codex.20260729212553`. |
| DCA installed MCP pilot | Official stdio client against `mql5-codegraph-mcp` | Nine tools; 12 files, 280 nodes, 1,322 edges, 109 static diagnostics; compiler report is complete/current/warnings with five findings. |
| Dashboard HTTP and UI | `Invoke-WebRequest http://127.0.0.1:8766/api/status` and local rendered-DOM inspection | HTTP 200/ready; UI shows 12 files, 280 nodes, 1,322 relationships, and 109 diagnostics. |
| Dashboard build gate | `npm run lint` and `npm run build` in `web/` | Passed; TypeScript/Vite production bundle completed. |
| Graphify incremental index | `graphify . --update --directed --no-viz --code-only`, then directed multigraph diagnostic | 1,818 nodes and 3,199 edges; no dangling, missing, self-loop, duplicate, or collapsed edges. |

## Risks and unresolved questions

- The compiler log proves the observed 2026-06-15 compilation had zero errors and five warnings; it does not
  prove current runtime, broker compatibility, profitability, or Strategy Tester behavior.
- All five compiler warnings concern deprecated `POSITION_COMMISSION` references in
  `DCA-Matrix-Junet-Engine.mqh` (lines 509, 575, 610, 1434, and 1487). They should be reviewed before a
  release claim.
- Static diagnostics remain 108 external/unresolved standard-library call groups (`RESOLVE003`) and one
  ambiguous `CreateLabel` call (`RESOLVE002`); they are analyzer visibility signals, not compiler errors.
- Pip continues to warn about stale `~ql5-codegraph` installation remnants from a historical interrupted
  uninstall. `pip check` reports no broken requirements; safe cleanup needs a separate, explicit Windows
  maintenance action.
- The installed Graphify package is 0.9.20 while its skill is 0.9.27. The health diagnostic passed, but
  upgrading that separate toolchain should be considered in a dedicated maintenance session. Its code-only
  pass also reports `plugin.json` as a zero-node configuration file, not an omitted source relationship.

## Next objective

Review the five code-89 deprecation warnings with the EA owner, then run an operator-controlled Strategy
Tester or paper-trading check before declaring DCA-Matrix-Junet release-ready.
