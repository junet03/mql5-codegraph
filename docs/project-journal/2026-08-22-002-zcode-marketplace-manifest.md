# 2026-08-22 — ZCode/Claude marketplace manifest

## Objective

Publish a standard plugin marketplace manifest so ZCode (and Claude Code compatible clients) can add
this repository as a plugin marketplace and install `mql5-codegraph-intelligence` through normal
plugin management, without manual cache copies.

## Starting state

- Branch and commit: `main` at `197d81e` with a clean working tree; branch `feat/zcode-marketplace` created from it.
- Relevant specification: `specs/004-mql5-agent-plugin/quickstart.md` (local plugin workflow).
- Known constraints: the Codex plugin ships `.codex-plugin/plugin.json`, `.mcp.json`, and five skills; ZCode reads `.claude-plugin/plugin.json` manifests and discovers `.mcp.json` at the plugin root automatically. The existing `gitnexus-marketplace` manifest shape is a proven-working reference for ZCode marketplace ingestion.

## Work completed

- Added `.claude-plugin/marketplace.json` at the repository root exposing one plugin,
  `mql5-codegraph-intelligence` v0.1.0, sourced from `./plugins/mql5-codegraph-intelligence`.
- Added `plugins/mql5-codegraph-intelligence/.claude-plugin/plugin.json` mirroring the Codex manifest's
  identity fields and pointing `skills` at `./skills`; the existing root `.mcp.json` is reused as-is
  (read-only stdio server `mql5-codegraph-mcp`).
- Updated the journal index.

## Decisions

- Marketplace `name` is `mql5-codegraph-marketplace` (suffixed, matching the `gitnexus-marketplace`
  convention) so the installed plugin id reads `mql5-codegraph-intelligence@mql5-codegraph-marketplace`.
- The `.claude-plugin/plugin.json` stays minimal (name, version, description, author, license,
  keywords, skills) like proven Anthropic-hosted plugin manifests; no Codex `interface` block is
  mirrored because it is consumer-specific.
- No ADR added: this is distribution metadata, not an architectural choice; ADR-0003 (private plugin
  alpha) remains authoritative for the plugin itself.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Marketplace JSON parses | `python -m json.tool .claude-plugin/marketplace.json` | OK |
| Plugin manifest parses | `python -m json.tool plugins/mql5-codegraph-intelligence/.claude-plugin/plugin.json` | OK |
| Referenced paths exist | `git ls-files` for `plugins/mql5-codegraph-intelligence/skills`, `.mcp.json` | OK (5 skills, `.mcp.json` present) |
| Source tree untouched | `git status --short` after edits | Only the two new manifests and journal files |
| Unit tests (proportional, metadata-only change) | `python -m unittest discover -s tests` | See PR checks |
| Live ZCode ingestion | Add `https://github.com/junet03/mql5-codegraph` as a marketplace in ZCode Plugin Management after merge | Pending post-merge on the operator machine |

## Risks and unresolved questions

- ZCode plugin ids and marketplace display naming were inferred from the working `gitnexus-marketplace`
  example on the same machine; the exact installed plugin id must be confirmed after the first install.
- The Codex `interface` metadata is not represented in the Claude-style manifest; if a future ZCode
  build surfaces marketplace UI fields (icon, category), the manifest may need optional additions.
- `version` in the marketplace entry is decoupled from the Codex plugin build stamp; keep both in sync
  when the plugin skills or MCP surface change.

## Next objective

After merge: add the marketplace in ZCode Plugin Management, install the plugin while keeping it
disabled in the lean `daily` profile, then verify the five skills load and the `mql5-codegraph` MCP
server connects read-only; record the confirmed plugin id in the consumer vault's registry.
