# Project Journal

This directory is the durable handoff log for MQL5 CodeGraph. It records verified outcomes, decisions,
open risks, and the exact next objective so work can continue safely across sessions.

## Logging protocol

1. Read the newest journal entry, relevant ADRs, and the active specification before changing code.
2. Create one entry per meaningful work session using `YYYY-MM-DD-NNN-short-title.md`.
3. Record evidence, not optimistic summaries. Include commands and observed results for every verification claim.
4. Separate completed work, decisions, risks, and follow-ups. Never mark an unverified item complete.
5. When an architectural choice changes, add or supersede an ADR in `docs/decisions/`.
6. Before ending a session, update the next objective and refresh the Graphify index when tracked knowledge changed.

## Entry index

| Date | Entry | Outcome | Next objective |
| --- | --- | --- | --- |
| 2026-07-22 | [001 — Foundation and dashboard](2026-07-22-001-foundation-and-dashboard.md) | Core analyzer, CLI, and local dashboard v0.2.0 established | Intelligence Kernel and Structural Guardrails |
| 2026-07-22 | [002 — Graphify and project governance](2026-07-22-002-graphify-and-project-governance.md) | Directed project graph, journal protocol, and ADR system established | Specify feature 003 |
| 2026-07-22 | [003 — Intelligence Kernel specification](2026-07-22-003-intelligence-kernel-specification.md) | Feature 003 scope, acceptance criteria, and quality gate established | Plan feature 003 contracts and architecture |
| 2026-07-22 | [004 — Intelligence Kernel implementation plan](2026-07-22-004-intelligence-kernel-plan.md) | Research, data model, v1 contracts, migration, and validation design completed | Generate and analyze feature 003 tasks |
| 2026-07-22 | [005 — Intelligence Kernel implementation](2026-07-22-005-intelligence-kernel-implementation.md) | T001–T048 complete; receiver-aware resolver fix committed as `0de2118`; DCA-Hedge edges reduced from 10,720 to 6,386 | Profile bounded path enumeration on dense graphs |
| 2026-07-23 | [001 — Release and security gate](2026-07-23-001-release-security-gate.md) | Slow-drip, local transport, include containment, and dependency gates hardened | Define an analyzer work-budget contract |
| 2026-07-23 | [002 — Private MCP plugin alpha](2026-07-23-002-private-mcp-plugin-alpha.md) | Private plugin, four skills, and eight-tool local MCP adapter verified | Pilot the plugin on one real private MQL5 repository |
| 2026-07-23 | [003 — GitHub professionalization](2026-07-23-003-github-professionalization.md) | MIT/community/CI presentation and secure GitHub metadata established | Verify the hosted PR checks and protect `main` |
| 2026-07-24 | [001 — Plugin consumer isolation](2026-07-24-001-plugin-consumer-isolation.md) | Consumer policy, regression gates, non-editable runtime, and cache-busted plugin established | Pilot from a separate MQL5 project under a read-only profile |
| 2026-07-29 | [001 — Analyzer work-budget implementation](2026-07-29-001-analysis-work-budget.md) | Canonical analysis is bounded across all local entry points without partial publication | Design compiler correlation against a local MetaEditor fixture |
| 2026-07-29 | [002 — Compiler evidence correlation](2026-07-29-002-compiler-evidence-correlation.md) | Bounded supplied compiler logs now correlate with static evidence through CLI and MCP | Pilot a real trusted-project MetaEditor log |
| 2026-07-29 | [003 — Plugin runtime refresh](2026-07-29-003-plugin-runtime-refresh.md) | Non-editable wheel and cache-busted nine-tool plugin runtime installed and verified | Run a trusted-project compiler-evidence pilot |
| 2026-07-29 | [004 — UTF-16 compiler-log support and DCA dashboard pilot](2026-07-29-004-utf16-compiler-log-support.md) | BOM-marked UTF-16 logs correlate through the installed plugin; DCA dashboard is live locally | Review code-89 warnings and run an operator-controlled runtime check |
| 2026-07-30 | [001 — MCP transport lifecycle evidence](2026-07-30-001-mcp-transport-lifecycle.md) | MCP exits are attributable, idle continuity is covered, and the non-editable runtime/plugin are deployed | Run a 30-minute Codex host idle/resume soak |
| 2026-07-30 | [002 — Authoritative reference corpus](2026-07-30-002-authoritative-reference-corpus.md) | Page-aware 10,021-page corpus, cited search, agent tools, optional Graphify overlay, and local runtime deployed | Push the branch, open a draft PR, and verify hosted CI |
| 2026-07-30 | [003 — Cross-platform compiler paths](2026-07-30-003-cross-platform-compiler-paths.md) | Windows and POSIX absolute diagnostic paths now retain outside-project semantics on every host | Push the focused fix and verify the full hosted CI matrix |
| 2026-07-30 | [004 — Public v0.3.0 release](2026-07-30-004-public-v0.3.0-release.md) | v0.3.0 published with verified artifacts, public install, and zero open security alerts | Harden v0.3.1 artifact provenance and upload runtime |
| 2026-08-22 | [001 — Analysis-budget agent guidance](2026-08-22-001-analysis-budget-agent-guidance.md) | Budget exhaustion now distinguishes analyzer work from model tokens and returns ordered retry actions | Prepare the next compatible release |
| 2026-08-22 | [002 — ZCode/Claude marketplace manifest](2026-08-22-002-zcode-marketplace-manifest.md) | Standard `.claude-plugin` marketplace and plugin manifests added for ZCode/Claude plugin-management ingestion | Post-merge: install via ZCode Plugin Management and confirm the plugin id |

## Truth hierarchy

When records disagree, use this order: current source and tests, active specification, accepted ADRs, newest
journal entry, Graphify output, then older generated reports.
