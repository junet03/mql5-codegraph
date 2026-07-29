# Quickstart: Validate Compiler Evidence Correlation

## Prerequisites

- Run from the repository root on Python 3.11+.
- Set `PYTHONPATH=src` while testing the checkout rather than an installed wheel.
- Use the supplied fixture logs for automated validation. In an operator workflow, compile an entry file
  through installed MetaEditor with its log option, then pass the generated local log explicitly.

## Focused contract tests

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m unittest tests.test_compiler_evidence tests.test_cli tests.mcp_adapter.test_service tests.mcp_adapter.test_protocol
```

Expected: success, warning, error, stale, unsupported, outside-root, no-declaration, and MCP-no-snapshot
paths remain deterministic and do not mutate fixture source/log hashes.

## End-to-end CLI check

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m mql5_codegraph.cli analyze tests/fixtures/basic_ea --output $env:TEMP/basic-ea.codegraph.json --json
Copy-Item tests/fixtures/compiler_logs/basic-success.log tests/fixtures/basic_ea/basic-success.log
python -m mql5_codegraph.cli compiler-evidence $env:TEMP/basic-ea.codegraph.json --entry BasicEA.mq5 --log basic-success.log --json
```

Expected: the correlation report is `current`, reports the observed compiler outcome, includes a stable
log fingerprint, and does not modify the graph, the MQL5 files, or the log. Remove the copied fixture
log after validation.

## Regression gate

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
python -m unittest discover -s tests
python -m compileall -q src tests tools
```

No dashboard build is required unless a dashboard projection is added in a later feature.
