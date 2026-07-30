# Changelog

All notable changes to MQL5 CodeGraph are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Deterministic analyzer-wide work budgets for discovery, lexing, parsing, resolution, and runtime
  enrichment, with transactional CLI, dashboard, and MCP failure behavior.
- Read-only compiler-evidence correlation for a bounded operator-supplied MetaEditor log, exposed through
  CLI and the private MCP plugin without changing static graph facts or launching a compiler.
- BOM-marked UTF-16 LE/BE MetaEditor compiler-log decoding, alongside UTF-8, with regression coverage.
- Bounded MCP stdio lifecycle telemetry for startup, clean EOF, and unhandled failure, plus idle-session
  and crash-path regression coverage.
- Offline page-aware corpora for operator-owned MQL5 PDF references, with immutable snapshots,
  deterministic authority-aware search, physical-page citations, CLI and read-only MCP access, and an
  optional isolated Graphify semantic overlay.
- A fifth plugin workflow skill for cited MQL5 reference research and public operator/contributor
  guidance covering evidence boundaries, local data ownership, extraction limits, and attribution.

### Fixed

- Cross-platform compiler-diagnostic containment now recognizes absolute Windows, UNC, and POSIX path
  syntax independently of the runner operating system.

## [0.2.0] - 2026-07-23

### Added

- Evidence-backed MQL5 tokenizer, parser, resolver, runtime enrichment, and canonical graph.
- Versioned Intelligence Kernel with query, context, impact, diagnostics, path, and context-package
  operations.
- Loopback-only local dashboard and normalized HTTP adapter.
- Private Codex plugin with four workflow skills and eight read-only MCP tools.
- Security, dependency, privacy, package, and directed graph release gates.

### Security

- Bounded dashboard request reads with an absolute slow-drip deadline.
- Loopback host/origin enforcement and explicit source-viewer roots.
- Include containment before filesystem probes.

[Unreleased]: https://github.com/junet03/mql5-codegraph/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/junet03/mql5-codegraph/releases/tag/v0.2.0
