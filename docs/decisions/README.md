# Architecture Decision Records

ADRs capture decisions that constrain future implementation. Use `ADR-NNNN-short-title.md`; mark a record
as Proposed, Accepted, Superseded, or Deprecated, and link the superseding record when applicable.

| ADR | Status | Decision |
| --- | --- | --- |
| [ADR-0001](ADR-0001-intelligence-kernel.md) | Accepted | Stabilize an Intelligence Kernel before the public MCP contract |
| [ADR-0002](ADR-0002-local-dashboard-security-boundary.md) | Accepted | Keep the unauthenticated dashboard loopback-only with bounded request reads |
| [ADR-0003](ADR-0003-private-mcp-plugin-alpha.md) | Accepted | Ship a private local read-only MCP plugin alpha over the Intelligence Kernel |
| [ADR-0004](ADR-0004-licensing-and-github-release-governance.md) | Accepted | Use MIT for code, separate brand rights, and CI-gated GitHub releases |
| [ADR-0005](ADR-0005-plugin-consumer-isolation.md) | Accepted | Isolate plugin consumers from editable toolchain source and require explicit maintenance scope |
| [ADR-0006](ADR-0006-analysis-work-budget.md) | Accepted | Bound canonical analysis work without publishing partial graphs |
| [ADR-0007](ADR-0007-compiler-evidence-correlation.md) | Accepted | Correlate bounded supplied compiler logs without compiler process control |
| [ADR-0008](ADR-0008-authoritative-reference-corpus.md) | Accepted | Keep authoritative references page-aware and Graphify optional |
| [ADR-0009](ADR-0009-graphify-credential-isolation.md) | Accepted | Give Graphify only runtime and selected-backend environment values |
| [ADR-0010](ADR-0010-dashboard-filesystem-authority.md) | Accepted | Bind dashboard filesystem access to startup authority |
