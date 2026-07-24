# 2026-07-24 — Plugin consumer isolation

## Objective

Prevent consumer agents from treating the MQL5 CodeGraph implementation repository as a writable MQL5
project while preserving the existing read-only MCP workflow.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `3fda14c`
- Relevant specification: implemented Feature 004 private MCP plugin alpha
- Known constraints: agents use the owner's Windows identity; prose instructions cannot enforce OS-level
  write denial; the installed Python package was editable from `D:\mql5-codegraph`.

## Work completed

- Added root and plugin-scoped agent rules that make toolchain source immutable unless the user
  explicitly requests MQL5 CodeGraph maintenance.
- Added one common consumer safety reference and required all four plugin skills to load it before MCP
  calls.
- Preserved the manifest's read-only capability and added bytecode-write suppression to the MCP process.
- Changed consumer setup guidance from editable source to a built wheel and documented the separate
  maintainer-only editable workflow.
- Added policy regression tests and updated Feature 004 with explicit consumer-isolation requirements.
- Cache-busted and reinstalled plugin version `0.1.0+codex.20260724032118`.
- Replaced the machine's editable Python install with the built wheel; the MCP import now resolves from
  `C:\Python314\Lib\site-packages`.

## Decisions

- Adopted [ADR-0005](../decisions/ADR-0005-plugin-consumer-isolation.md): immutable toolchain policy,
  non-editable consumer runtime, and explicit maintenance scope.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Policy regression | `python -m unittest tests.test_plugin_bundle` | 7 passed in 0.114s |
| Full Python suite | `python -m unittest discover -s tests` | 108 passed in 9.494s after non-editable wheel installation |
| Python compilation | `python -m compileall -q src tests tools` | Exit 0 |
| Plugin validation | Official `validate_plugin.py` | Passed |
| Skill validation | Official `quick_validate.py` for all four skills | All four passed |
| Distribution build | `uvx --from build pyproject-build` | Wheel and sdist built successfully |
| Distribution metadata | `uvx --from twine twine check dist\*` | Wheel and sdist passed |
| Runtime isolation | `pip show` plus resolved module path | No editable project; import resolves from `C:\Python314\Lib\site-packages` |
| MCP adapter after wheel install | `python -m unittest discover -s tests/mcp_adapter` | 9 passed in 3.300s |
| Installed plugin | `codex plugin add` plus cached-file readback | Version `0.1.0+codex.20260724032118` installed and policy present |
| Hosted CI | GitHub Actions run `30064297674` | All six jobs passed on commit `d324ad2` |
| Directed project graph | `graphify update .` plus directed multigraph diagnostic | 1,650 nodes, 2,942 edges, 138 communities; no missing, dangling, self-loop, duplicate, or collapsed edges |

## Risks and unresolved questions

- Hard write isolation still requires a read-only workspace or separate OS/container identity.
- The repository-local marketplace still exposes its source path in plugin inventory; consumer tasks must
  use the installed cache and must not attach the source checkout as a writable workspace.
- Graphify again reported 11 JSON/manifest files with zero AST nodes. Directed graph integrity remained
  clean and the warning does not concern executable source.

## Next objective

Pilot the cache-busted plugin from a separate MQL5 project under a read-only consumer permission profile.
