# ADR-0005: Plugin consumer isolation

- Status: Accepted
- Date: 2026-07-24
- Owners: Project maintainers

## Context

The private plugin exposes only read-only MCP tools, but its repository-local marketplace reveals the
MQL5 CodeGraph source path. The machine also used an editable Python installation, so the MCP executable
imported live code from that checkout. An agent with ordinary filesystem tools and the same Windows
identity could therefore modify source even though the MCP surface itself was non-destructive.

Skill instructions cannot create an operating-system security boundary. The consumer workflow needs a
clear immutable-toolchain policy and must avoid executing directly from editable source.

## Decision

- Treat the MQL5 CodeGraph source repository, marketplace, plugin source/cache, and installed Python
  package as immutable toolchain material during consumer workflows.
- Require every bundled skill to load one common consumer safety policy before calling MCP tools.
- Never infer an MQL5 target from the current directory or toolchain paths; require a separate,
  user-selected project root.
- Install the consumer MCP runtime from a built wheel, not an editable checkout.
- Suppress Python bytecode writes in the bundled MCP process.
- Permit source mutation only when the user explicitly names MQL5 CodeGraph as the maintenance target.
- Require a read-only workspace or separate OS/container identity for untrusted agents; instructions and
  Git branch protection are defense in depth, not hard local access control.

## Consequences

- Positive: normal plugin use no longer imports live source from the development checkout.
- Positive: every skill applies the same target-resolution and no-mutation boundary.
- Positive: accidental edits become both instruction violations and CI-detectable policy regressions.
- Cost: maintainers must rebuild and reinstall the wheel after runtime changes.
- Cost: a fresh Codex task is required after cache-busting and reinstalling plugin instructions.
- Risk: an agent running under the owner's unrestricted OS identity can still bypass prose instructions;
  hard isolation remains an operator/runtime responsibility.

## Guardrails

- Do not describe the consumer policy as a filesystem sandbox or access-control list.
- Do not point consumer tasks at the MQL5 CodeGraph repository as their writable workspace.
- Keep the MCP tool inventory free of source-write, raw-source retrieval, shell, Git, or package-install
  operations.
- Reinstall a non-editable wheel before handing the machine back from a maintainer session to consumer
  agents.
