# 2026-08-22 — Analysis-budget agent guidance

## Objective

Make analyzer budget exhaustion self-describing so agents do not misreport it as a model-token or
account quota problem and retry in the safest order.

## Starting state

- Branch and commit: `main` at `ce0e986` with a clean working tree.
- Relevant specification: `specs/005-analysis-work-budget/spec.md` and its v1 contract.
- Known constraints: preserve the stable `analysis_budget_exceeded` code, deterministic accounting,
  complete-graph publication, and the prior MCP snapshot on failed refresh.

## Work completed

- Extended the canonical exhaustion details with the stable `analyzer_work_units` discriminator, an
  explicit model-token exclusion, ordered machine-readable retry actions, and the supported maximum.
- Updated the MCP `index_project` description to tell agents to select the narrowest project root,
  avoid broad MT5 standard-library include roots, and increase `max_work` only after narrowing scope.
- Added core and MCP regression assertions, and synchronized the public budget and MCP contracts,
  README guidance, data model, and changelog.
- Built and force-reinstalled a non-editable 0.3.0 wheel into the Python 3.14 consumer runtime, then
  cache-busted and reinstalled the Codex plugin as `0.1.0+codex.20260821181319`.
- Stopped only the PM2-managed `dsh-web` app after proving its autorestart loop recreated the locked MCP
  child, completed installation, and restored `dsh-web` with one new MCP child.

## Decisions

- Keep `analysis_budget_exceeded`, its message, and the original phase/counter fields unchanged; the
  new fields are additive to the v1 envelope.
- Encode retry policy as ordered action identifiers instead of relying only on prose so adapters and
  agents can handle it deterministically.
- No ADR is required because this clarifies the accepted ADR-0006 recovery contract without changing
  its accounting, publication, security, or compatibility boundaries.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| TDD red | `python -m unittest tests.test_analysis_budget tests.mcp_adapter.test_service` with `PYTHONPATH=src` before implementation | Expected failure and error: missing `budget_kind` in core and MCP payloads |
| Focused regression | Same command after implementation | 18 tests passed |
| Full Python regression | `python -m unittest discover -s tests` with `PYTHONPATH=src` | 167 tests passed in 19.958s |
| Python bytecode | `python -m compileall -q src tests` with `PYTHONPATH=src` | Passed |
| CLI exhaustion | Analyze `tests/fixtures/basic_ea` with `--max-work 1 --json` | Exit 1; structured guidance present; output graph absent |
| Wheel build | `uvx --from build pyproject-build --wheel --outdir <temp>` | Built `mql5_codegraph-0.3.0-py3-none-any.whl`; changed core and MCP server files were included |
| Installed runtime | Force-reinstall the wheel after stopping the lock-owning `dsh-web` app; then import and `pip show` | Version 0.3.0 imports from `C:\Python314\Lib\site-packages`; `pip check` reported no broken requirements |
| Installed MCP protocol | Official stdio `ClientSession` against `mql5-codegraph-mcp`; list tools and force `max_work=1` | 13 tools; new `index_project` description visible; error content contained all structured guidance fields |
| Codex plugin refresh | Cachebuster helper, plugin validator, and `codex plugin add ... --json` | Installed and enabled `0.1.0+codex.20260821181319` |
| Runtime recovery | PM2 and process-tree inspection after reinstall | `dsh-web` online with PID 4208; one MCP child owned by it |
| Graphify code refresh | `graphify update .` | Rebuilt 2,496 nodes, 4,429 edges, and 189 communities; 11 metadata files produced zero nodes |
| Graph health | `graphify diagnose multigraph --graph graphify-out/graph.json --directed --json` | 0 missing/dangling/self-loop/duplicate/collapsed edges; directed graph retained all 4,429 edges |

## Risks and unresolved questions

- Existing consumers that reject unknown JSON fields would need correction; supported consumers treat
  error details as an extensible object and the stable fields remain unchanged.
- Graphify 0.9.27 refreshed code without an LLM, so changed prose remains dependent on the prior semantic
  graph until a credential-backed or agent-assisted semantic refresh; generated output stays uncommitted.
- The first wheel reinstall was interrupted by `dsh-web` immediately respawning its MCP child. Runtime
  recovery succeeded, but pip left two invalid-distribution backup directories named `~ql5_codegraph*`;
  the execution policy rejected their recursive cleanup. They cause warnings but `pip check` passes and
  the installed package imports correctly.
- External v0.3.0 installations still need a new release artifact before they receive the guidance.

## Next objective

Prepare the next compatible release so installed MCP clients receive the actionable budget envelope.
