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

## Truth hierarchy

When records disagree, use this order: current source and tests, active specification, accepted ADRs, newest
journal entry, Graphify output, then older generated reports.
