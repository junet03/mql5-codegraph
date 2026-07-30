# Reference Corpus Evidence Rules

The MCP server may attach one immutable corpus built beforehand by the operator with
`mql5-codegraph reference build`. MCP never extracts PDFs, writes corpus files, invokes Graphify,
installs packages, downloads references, or discovers arbitrary filesystem content.

## Snapshot rules

- Call `reference_status` before reference claims.
- Load only a complete corpus root explicitly selected by the operator.
- Treat `corpus_fingerprint` and `revision` as independent of the project graph fingerprint/revision.
- Pass `expected_corpus_fingerprint` after the first response so a changed attachment fails visibly.
- A failed load preserves the prior active snapshot; never imply that it refreshed.

## Citation rules

Every usable citation must retain:

- `evidence_class=reference_document`;
- corpus fingerprint;
- source ID, title, SHA-256, authority, and official URL when present;
- section ID/path and content SHA-256;
- physical PDF page range and excerpt character bounds;
- extraction warnings and completion/truncation state.

Physical PDF pages are one-based and may differ from printed labels. Prefer the physical page fields in
machine citations; a printed label is supplemental display metadata.

Authority is a tie-breaker among equally relevant matches:

1. `normative`
2. `explanatory`
3. `specialist`
4. `unclassified`

Do not use authority to promote an unrelated passage. When sources disagree, cite the competing editions
and ask the user which contract applies if the answer affects implementation.

## Composition with project evidence

Use CodeGraph tools for what the selected project actually declares and calls. Use reference tools for
documented MQL5 contracts. Use compiler evidence only for the supplied log. Do not add reference sections
or Graphify concepts to the canonical project graph.

Graphify overlays are optional `semantic_overlay_inference`. They may suggest concepts to search, but MCP
does not expose or generate them and they cannot replace page-cited reference evidence.

## Limits

The v1 corpus uses deterministic PDFium text extraction, not OCR. Empty/image-only pages, malformed layout,
tables, code formatting, headers/footers, and spaced glyphs may be lossy. State relevant warnings and do
not reconstruct missing text.
