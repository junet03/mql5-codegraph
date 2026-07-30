---
name: mql5-release-gate
description: Run a local evidence-backed readiness gate for an MQL5 project using MQL5 CodeGraph diagnostics plus the repository's own build and test instructions. Use before release, handoff, tagging, publishing, or declaring an EA or indicator ready.
---

# MQL5 Release Gate

Before any tool call, read and obey
[the consumer safety boundary](../../references/consumer-safety.md). Never infer the analysis target from
the plugin, marketplace, package, cache, or MQL5 CodeGraph source path.

Use `$mql5-project-onboarding` to establish a fresh snapshot, then:

1. Call `get_diagnostics` with a sufficient bound and group results by severity/code.
2. Query the main event handlers and use `get_context` or `find_paths` for the project's documented
   critical trading, risk, and order-management flows.
3. Read applicable `AGENTS.md`, project documentation, and build scripts for the real verification
   commands.
4. Run the narrowest relevant checks first, then the strongest proportional suite available.
5. If MetaEditor/terminal compilation is not connected, explicitly report it as not verified.
6. For claims that depend on an MQL5 platform contract, use `$mql5-reference-research` and cite the
   separate [reference evidence](../../references/reference-corpus.md).
7. Check the final diff and repository status; never include generated graphs, logs, credentials,
   local terminal data, or MetaTrader files in a commit.

Return one of:

- `PASS`: all required checks ran and no blocking issue remains;
- `CONDITIONAL`: bounded/static checks passed but a named external verification is missing;
- `FAIL`: a reproducible blocking diagnostic, test, build, security, or release issue remains.

Static graph evidence does not prove profitability, runtime safety, broker compatibility, or
successful compilation.
