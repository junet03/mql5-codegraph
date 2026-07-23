# ADR-0003: Private MCP plugin alpha

- Status: Accepted
- Date: 2026-07-23
- Owners: Project maintainers

## Context

The Intelligence Kernel now provides versioned, evidence-preserving query, context, impact, path,
diagnostic, and context-package operations. Internal Codex agents need a reusable MQL5 workflow without
duplicating those semantics in prompts or adapter code. The analyzer is still a local single-user alpha:
four adversarial scaling paths and the absence of an analyzer-wide work budget prevent a safe hosted or
multi-tenant ingestion claim.

## Decision

Ship an experimental private Codex plugin backed by a local MCP stdio adapter:

- keep the adapter as a one-to-one projection over `IntelligenceKernel`;
- maintain one in-memory project snapshot per server process and publish replacement snapshots atomically;
- expose eight bounded, non-destructive tools and no source-editing or raw-source retrieval tool;
- index only operator-selected trusted local roots, with no network access or persisted graph;
- package four workflow skills for onboarding, architecture, change impact, and release gating;
- distribute the plugin through the repository-local private marketplace;
- use the official MCP Python SDK as an optional dependency pinned to `mcp>=1.28.1,<2`.

This tool surface is alpha and private. It does not supersede ADR-0001 or declare a stable public MCP
compatibility contract.

## Consequences

- Positive: internal agents get the same evidence, ambiguity, freshness, and completion semantics as CLI
  and Web callers.
- Positive: project indexing cannot modify source files, persist an index, or expand the network boundary.
- Positive: a fresh Codex task can load the plugin without copying project instructions into every prompt.
- Cost: the MCP extra and console entry point must be installed in the environment that launches Codex.
- Cost: one server process tracks only one active project snapshot and must re-index after source changes.
- Risk: MCP SDK 2.x requires an explicit compatibility review before the dependency ceiling is raised.

## Guardrails

- MCP adapter code must not implement analyzer or ranking semantics owned by the Intelligence Kernel.
- Failed indexing must leave the last successful snapshot available and unchanged.
- Every intelligence result must retain graph identity, evidence, ambiguity, bounds, and completion metadata.
- Hosted, multi-user, or untrusted-repository ingestion is blocked until an analyzer-wide work-budget
  contract and adversarial scaling regressions exist.
- Adding mutation, source retrieval, persistence, remote transport, or a public contract requires a new or
  superseding ADR and a security review.
