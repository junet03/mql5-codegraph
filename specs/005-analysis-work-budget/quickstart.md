# Quickstart: Validate Analyzer Work Budget

## Prerequisites

- Run from the repository root on Python 3.11+.
- Set `PYTHONPATH=src` when testing the checkout rather than an installed wheel.

## Focused contract tests

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m unittest tests.test_analysis_budget tests.test_indexer tests.test_cli tests.test_web_state tests.mcp_adapter.test_service
```

Expected: the focused suite proves validation, exhaustion in every analysis phase, no source mutation,
no CLI graph output on failure, and transactional dashboard/MCP publication.

## End-to-end CLI checks

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m mql5_codegraph.cli analyze tests/fixtures/basic_ea --output $env:TEMP/basic-ea.codegraph.json --json
python -m mql5_codegraph.cli analyze tests/fixtures/basic_ea --output $env:TEMP/should-not-exist.codegraph.json --max-work 1 --json
```

Expected: the first command emits the normal deterministic summary. The second exits non-zero with
`analysis_budget_exceeded` and does not create `should-not-exist.codegraph.json`.

## Regression gate

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m unittest discover -s tests
python -m compileall -q src tests
```

If dashboard-facing state changes, also run `npm run lint` and `npm run build` in `web/`.
