---
name: mql5-reference-research
description: Search an operator-built authoritative MQL5 reference corpus and return page-cited platform, language, API, standard-library, or specialist guidance. Use for MQL5 behavior and contract questions that project source alone cannot establish, or when an answer needs an official-document citation.
---

# MQL5 Reference Research

Before any tool call, read and obey:

- [the consumer safety boundary](../../references/consumer-safety.md);
- [the reference-corpus evidence rules](../../references/reference-corpus.md).

Never infer a corpus path from the plugin, package, cache, current directory, or an MQL5 project.

1. Call `reference_status`.
2. If status is `not_loaded`, ask for or use only the absolute corpus root explicitly selected by the
   operator, then call `load_reference_corpus`. Do not build, repair, enumerate, or download a corpus.
3. Call `search_reference` with a focused identifier or concept and a small result limit.
4. Preserve `corpus_fingerprint`, authority, completion, truncation, source hash, section, physical page
   range, and extraction warnings.
5. Pass `expected_corpus_fingerprint` on follow-up search/excerpt calls.
6. Call `get_reference_excerpt` only for the result sections needed to verify wording or surrounding
   context. Quote sparingly; otherwise paraphrase and cite.

Prefer an exact normative-reference match for platform contracts. Explanatory and specialist sources may
clarify usage but do not silently override a normative source. If editions conflict, report both document
identities and pages rather than resolving the conflict by guesswork.

Keep evidence classes separate:

- `reference_document` supports claims about documented MQL5 behavior;
- `code_graph` supports claims about the selected project's source relationships;
- `external_compiler_evidence` supports only the supplied compile observation;
- `semantic_overlay_inference` is discovery help, never a normative citation.

Report exhaustive no-match differently from a truncated search. A missing reference match does not prove
that MQL5 lacks the behavior. PDF extraction warnings also limit what can be concluded.
