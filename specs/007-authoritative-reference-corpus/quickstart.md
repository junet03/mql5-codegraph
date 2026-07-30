# Quickstart Validation: Authoritative MQL5 Reference Corpus

This guide validates the feature with local, user-owned documents. Do not copy third-party PDFs or the
generated corpus into this repository.

## Prerequisites

- Python 3.11+
- A checkout of MQL5 CodeGraph
- Local text-bearing MQL5 PDF references
- Graphify 0.9.x only for the optional overlay scenario

## Install

```powershell
python -m pip install -e ".[reference,mcp]"
```

The `reference` extra is required only to build PDFs. It uses pypdf for document structure and PDFium for
streaming text extraction. Existing corpus search and MCP reads import neither dependency.

## Prepare local locations

Keep input and output outside the checkout:

```powershell
$sourceDir = 'D:\mql5-pdf'
$corpusDir = 'D:\mql5-knowledge\reference-corpus'
```

The known filenames `mql5.pdf`, `mql5book.pdf`, and `neuronetworksbook.pdf` receive documented authority
defaults. For another edition or document set, copy the example source declaration from
`docs/reference-corpus.md`, pin hashes if desired, and pass `--sources`.

## Build and validate

```powershell
mql5-codegraph reference build $sourceDir --output $corpusDir --json
mql5-codegraph reference status $corpusDir --json
```

Expected:

- no network request and no Graphify invocation;
- one immutable snapshot and a valid `current.json`;
- all physical pages accounted for;
- every source shows its hash, authority, page states, and warnings;
- rebuilding unchanged bytes reports `reused: true`.

## Search and inspect

```powershell
mql5-codegraph reference search $corpusDir 'OrderSend' --limit 5 --json
mql5-codegraph reference search $corpusDir 'neural network optimization' --limit 5 --json
mql5-codegraph reference excerpt $corpusDir '<section-id>' --start 0 --max-chars 1200 --json
```

Confirm each result identifies:

- corpus fingerprint;
- source ID, SHA-256, authority, and official URL if declared;
- section path and Markdown path;
- exact physical PDF citation pages and character offsets;
- completion/truncation metadata.

## Attach to the experimental local MCP beta

Configure the existing `mql5-codegraph-mcp` server, then call:

1. `load_reference_corpus` with the explicit corpus root.
2. `reference_status`.
3. `search_reference` for the same query used by CLI.
4. `get_reference_excerpt` for one returned section.

The CLI and MCP evidence should be semantically equivalent. Loading a malformed copy must fail without
replacing the active reference snapshot.

## Optional Graphify overlay

Review Graphify's own privacy/backend behavior first. Documentation content enters its semantic model
pipeline. For local Ollama:

```powershell
$overlayDir = 'D:\mql5-knowledge\graphify-overlay'
mql5-codegraph reference graphify $corpusDir `
  --output $overlayDir `
  --graphify graphify `
  --backend ollama `
  --processing-boundary local `
  --timeout-seconds 3600 `
  --json
```

For a remote provider, specify `--processing-boundary remote --allow-remote`. The command reports the
boundary before execution, publishes only validated output, and never changes the authoritative corpus.
Use Graphify for concept discovery; cite the reference corpus for platform claims.

## Contributor verification

```powershell
python -m unittest discover -s tests
python -m compileall -q src tests tools
git diff --check
```

An opt-in smoke against the three local references should additionally confirm 10,021 total physical
pages and exercise at least 20 golden queries. Public CI uses generated fixtures and does not require or
download the official PDFs.
