# 2026-07-30 — Authoritative reference corpus

## Objective

Turn operator-owned official MQL5 PDFs into a durable local knowledge source for humans and agents, with
exact page provenance, deterministic search, optional Graphify discovery, open-source guidance, and honest
tool attribution.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `fff1b02`
- Relevant specification: `specs/007-authoritative-reference-corpus/spec.md`
- Known constraints: do not redistribute third-party PDFs or generated derivatives; preserve evidence
  classes; keep MCP read-only; treat Graphify as an optional external inferred overlay.

## Work completed

- Added the backend-neutral `mql5_codegraph.reference` core for source declarations, page-aware PDF
  extraction, deterministic JSON/JSONL plus linked Markdown, immutable snapshots, integrity validation,
  authority-aware lexical search, and exact bounded excerpts.
- Added offline CLI build/status/search/excerpt commands and an explicit bounded Graphify 0.9.x adapter
  with local/remote processing authority.
- Added an independent read-only MCP reference session and four tools:
  `load_reference_corpus`, `reference_status`, `search_reference`, and `get_reference_excerpt`.
- Added the `mql5-reference-research` agent skill, consumer-safety guidance, public operator/contributor
  documentation, v1 contracts, ADR-0008, package/CI policy, and acknowledgements.
- Cache-busted the plugin manifest as `0.1.0+codex.20260730223236` and updated its discovery metadata for
  the five-skill, 13-tool project/reference surface.
- Installed the committed wheel non-editably in the Python user site, refreshed the Codex plugin cache,
  and exercised the installed MCP entry point against the real corpus without stopping existing tasks.
- Built the operator-owned PDFs from `D:\mql5-pdf` into the external
  `D:\mql5-reference-corpus` root. The published fingerprint is
  `65caa3269d15a0d585805dd13f79365fd32e79c754f08dd88cd60b1b9bdde375`.
  It contains 3 documents, 10,021 physical pages, 4,748 sections, and zero extraction warnings.
- Kept the PDFs, 62 MiB generated corpus, Graphify overlays, build products, and Graphify project output
  outside tracked source.

## Decisions

- Accepted [ADR-0008](../decisions/ADR-0008-authoritative-reference-corpus.md): canonical reference
  evidence remains separate from project code graphs, compiler evidence, and semantic inference.
- Use pypdf for outlines, page labels, and destinations; use pypdfium2/PDFium for streaming page text.
  Both observed versions participate in corpus identity. On a 20-page local sample, PDFium took 0.155
  seconds versus 41.19 seconds for pypdf text extraction.
- Rank exactness and query-term coverage first, authority next, and occurrence counts after that. This
  makes normative material win equally relevant ties without suppressing a more exact specialist result.
- Reuse Graphify as an external version-checked CLI instead of copying or reimplementing it. Its output
  is always `semantic_overlay_inference`, never normative evidence.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Full regression | `python -m unittest discover -s tests` | 158 tests passed in 16.820 s |
| Bytecode | `python -m compileall -q src tests tools` | Passed |
| Corpus build | `python -m mql5_codegraph.cli reference build D:\mql5-pdf --output D:\mql5-reference-corpus --json` | New snapshot published in 107.2 s; 3 documents, 10,021 pages, 4,748 sections, 0 warnings |
| Deterministic reuse | Repeat the same real build | `reused: true`, same fingerprint and manifest hash, 8.32 s |
| Real retrieval | One loaded corpus, 20 exact/conceptual golden queries | 20/20 returned a normative source and physical-page citation; 9.391 s total after 6.419 s validated load |
| Snapshot validation | `reference status D:\mql5-reference-corpus --json` | Complete; all 10,021 pages are `text`; source hashes match the selected files |
| Skill bundle | `quick_validate.py plugins\mql5-codegraph-intelligence\skills\mql5-reference-research` | `Skill is valid!` |
| Package | `python -m pip wheel . --no-deps` plus ZIP metadata inspection | Wheel built; 52 files; reference extra includes both PDF dependencies; zero PDF files |
| Non-editable runtime | Force-reinstall committed wheel with `--user --no-deps`; inspect import locations; `python -m pip check` | Imports resolve under `C:\Users\SUNNY\AppData\Roaming\Python\Python314\site-packages`, not the source checkout; no broken requirements |
| Plugin refresh | `codex plugin add mql5-codegraph-intelligence@mql5-codegraph-internal --json` | Installed and enabled version `0.1.0+codex.20260730223236` |
| Installed MCP real-corpus smoke | Official MCP `ClientSession` against `mql5-codegraph-mcp` | 13 tools; loaded the real fingerprint; `OrderSend` returned normative MQL5 Reference page 2454 and a bounded exact excerpt |
| Schema | Parse `reference-corpus-v1.schema.json` with Python JSON parser | Passed |
| Graph refresh | `graphify update D:\mql5-codegraph` | 2,411 nodes, 4,320 edges, 184 communities; 11 metadata/config sources produced zero nodes and were reported |
| Directed graph health | `graphify diagnose multigraph --graph graphify-out\graph.json --json --directed` | 4,320 valid directed edges; no missing/dangling/self-loop/duplicate/collapsed edges |
| Patch hygiene | `git diff --check` | Passed; only the existing Git LF-to-CRLF warning for `.gitignore` remains |

## Risks and unresolved questions

- v1 does not perform OCR or reconstruct semantic layout. Tables, columns, code formatting, ligatures,
  headers, footers, and spaced glyphs may still need inspection against the cited original page.
- The real Graphify semantic overlay was intentionally not run: the active Ollama environment points at a
  non-loopback host, and no remote document-transmission authority was granted. Fake-process coverage
  verifies success, rejection, timeout, malformed output, and atomic preservation.
- MCP processes that were already running before deployment do not hot-reload code or tool schemas. They
  were left undisturbed; newly started processes use the verified non-editable wheel and refreshed plugin.
- The system Python installation reports pre-existing invalid `~*mql5-codegraph` distribution remnants
  during pip operations. They did not affect source imports or verification but should be cleaned during
  runtime maintenance.

## Next objective

Push the feature branch, open a structured draft pull request, and verify the hosted CI matrix before
merging or tagging a release.
