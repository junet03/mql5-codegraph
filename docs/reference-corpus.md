# Local authoritative MQL5 reference corpus

MQL5 CodeGraph can turn your own local MQL5 PDF references into an immutable page-aware Markdown corpus.
The corpus gives humans and agents the same deterministic search results and citations without placing
the PDFs, extracted text, or generated indexes in this repository.

## Evidence boundary

Four evidence classes remain separate:

| Class | Answers |
| --- | --- |
| `reference_document` | What a selected document states, cited by source hash and physical PDF page |
| `code_graph` | What the selected MQL5 project declares and how its symbols relate |
| `external_compiler_evidence` | What one supplied MetaEditor log observed |
| `semantic_overlay_inference` | Concepts/relationships suggested by an optional Graphify model pass |

Reference search is the citation authority for document claims. Graphify is discovery assistance; it
does not replace a document citation or add nodes to the canonical project graph.

## Ownership and copyright

- Obtain and retain your own lawful document copies.
- The project does not download or redistribute PDFs.
- Generated Markdown is a local derivative and remains subject to source-document rights and terms.
- Keep input, corpus, cache, logs, and semantic overlays outside the source checkout and out of Git.
- Official URLs in metadata are provenance labels only; the builder never fetches them.

## Install

```powershell
python -m pip install "mql5-codegraph[reference]"
```

The `reference` extra adds pypdf for document structure and pypdfium2/PDFium for fast streaming text
extraction. They are used only for corpus builds. Status, search, excerpts, and MCP reads of an existing
corpus use the standard library. Install `mql5-codegraph[mcp]` as well for the experimental local agent
adapter.

## Build the three recognized references

The builder recognizes these case-insensitive filenames:

| Filename | Default title | Authority |
| --- | --- | --- |
| `mql5.pdf` | MQL5 Reference | `normative` |
| `mql5book.pdf` | MQL5 Programming for Traders | `explanatory` |
| `neuronetworksbook.pdf` | Neural Networks for Algorithmic Trading with MQL5 | `specialist` |

It does not pin a global hash because publishers may update editions. The resulting snapshot always
records the actual SHA-256. Use an explicit manifest to pin an edition.

```powershell
$pdfDir = 'D:\mql5-pdf'
$corpusDir = 'D:\mql5-knowledge\reference-corpus'

mql5-codegraph reference build $pdfDir --output $corpusDir --json
mql5-codegraph reference status $corpusDir --json
```

Build is offline and never invokes Graphify. The builder hashes each source before and after extraction,
accounts for every physical page, preserves outline ancestry, emits extraction warnings, validates all
canonical files, and publishes `current.json` last. An interrupted or failed build leaves the prior
snapshot active.

## Declare and pin other sources

Create a local `sources.json`:

```json
{
  "contract_version": "1.0.0",
  "sources": [
    {
      "source_id": "mql5-reference",
      "filename": "mql5.pdf",
      "title": "MQL5 Reference",
      "authority": "normative",
      "role": "language_reference",
      "official_url": "https://www.mql5.com/files/docs/mql5.pdf",
      "expected_sha256": null
    },
    {
      "source_id": "team-guide",
      "filename": "team-guide.pdf",
      "title": "Team MQL5 Guide",
      "authority": "unclassified",
      "role": "local_guidance",
      "official_url": null,
      "expected_sha256": "replace-with-64-lowercase-hex-characters"
    }
  ]
}
```

Then run:

```powershell
mql5-codegraph reference build $pdfDir `
  --output $corpusDir `
  --sources D:\mql5-knowledge\sources.json `
  --json
```

Unknown auto-discovered PDFs are `unclassified`; they are never silently elevated to normative status.
Source IDs and filenames must be unique portable values. Symlinks and recursive discovery are rejected.

## Snapshot layout and update policy

```text
<corpus-root>/
├── current.json
└── snapshots/
    └── <corpus-fingerprint>/
        ├── manifest.json
        ├── index.md
        ├── records/{outlines,pages,sections}.jsonl
        └── documents/<source-id>/
            ├── index.md
            └── sections/*.md
```

The fingerprint covers source hashes, declarations, extractor identity, normalization version, and
sectioning configuration—not timestamps or workstation paths. Rebuilding unchanged inputs reuses the
same validated snapshot. When a PDF edition or extraction policy changes, a new snapshot is published;
old content-addressed snapshots remain for operator-managed retention.

`current.json` is the only supported discovery point. Do not make tools guess a snapshot by enumerating
the directory.

## Search and inspect

```powershell
mql5-codegraph reference search $corpusDir 'OrderSend' --limit 5 --json
mql5-codegraph reference search $corpusDir 'neural network optimization' --json
mql5-codegraph reference excerpt $corpusDir '<section-id>' `
  --start 0 `
  --max-chars 1200 `
  --json
```

Search is a deterministic full lexical scan over validated section records. Ranking considers exact
titles/aliases, phrases, and query-term coverage; authority breaks ties at that relevance level before
occurrence counts and stable IDs. A response reports whether candidate enumeration was exhaustive,
whether returned results were truncated, and whether there was no match.

Every result includes corpus and content fingerprints, source hash/authority, section path, physical page
range, exact excerpt character range, and extraction warnings. Physical PDF pages are one-based and may
differ from printed labels.

## Agent workflow

The experimental local MCP beta exposes 13 read-only tools; four are reference-specific:

1. `reference_status`
2. `load_reference_corpus`
3. `search_reference`
4. `get_reference_excerpt`

The operator must select an absolute complete corpus root. MCP rejects relative roots and does not build,
repair, enumerate, download, invoke Graphify, or install anything. After loading, agents should pass
`expected_corpus_fingerprint` on every follow-up call. A mismatch fails visibly so an answer cannot
silently combine revisions.

Install/use the bundled `mql5-reference-research` skill for the full evidence workflow. Project graph and
reference corpus revisions remain independent.

## Optional Graphify overlay

Graphify 0.9.x can derive a separate conceptual graph from the normalized Markdown:

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

The adapter observes the external version, uses `shell=False`, passes only the corpus's `documents/`
Markdown tree, validates `graph.json`, hashes all artifacts, and publishes a separate immutable overlay.
It does not install or vendor Graphify.

Graphify documentation extraction uses a model backend:

- `--processing-boundary local` currently permits only explicit `--backend ollama`.
- Other supported backends require `--processing-boundary remote --allow-remote`.
- Remote authority applies to that invocation only and means normalized document content may leave the
  machine according to the selected provider's configuration.
- The version probe receives only a minimal runtime environment and no provider API key.
- Extraction forwards only the selected backend's documented endpoint/model/credential variables plus
  the runtime allowlist. It does not inherit unrelated host tokens or another provider's key.
- Provider keys stay in the child environment; they are never command arguments, overlay identity,
  artifact metadata, or structured errors.

Graphify absence, timeout, unsupported version, non-zero exit, malformed graph, or oversized output never
invalidates the authoritative corpus or replaces a prior valid overlay.

The external executable is still a trusted operator boundary rather than a filesystem sandbox. Use an
isolated identity for untrusted tools or documents, and prefer least-privileged, short-lived credentials
for any explicitly authorized remote run.

## Known extraction limits

Version 1 targets text-bearing PDFs with usable outlines:

- no automatic OCR;
- empty/image-only and failed pages remain explicit;
- tables, columns, code blocks, headers, footers, ligatures, and inter-letter spacing may be lossy;
- parent/child bookmarks targeting the same page share one content section to avoid duplicate evidence;
- very long outline spans split deterministically at the configured page bound.

Do not infer missing content. Inspect the original local PDF page when formatting or extraction warnings
matter.

## Extending the feature

Keep `ReferenceCorpus` backend-neutral. A new converter or search accelerator must:

- preserve source/page/character provenance and extraction states;
- emit deterministic portable canonical records;
- pass failure-safe publication and CLI/MCP conformance tests;
- keep caches/databases disposable;
- keep inferred semantic edges outside normative evidence;
- add a versioned contract/ADR when compatibility or evidence semantics change.

See [ADR-0008](decisions/ADR-0008-authoritative-reference-corpus.md) and the
[v1 contracts](../specs/007-authoritative-reference-corpus/contracts/reference-corpus-v1.md).
