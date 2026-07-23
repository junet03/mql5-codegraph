# 2026-07-23 — Private MCP plugin alpha

## Objective

Package MQL5 CodeGraph as a private Codex plugin, expose a read-only MCP adapter for internal agents,
complete the release/security/dependency/privacy gates, and publish one clean private feature branch.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` from `main` at `efc97cb`
- Relevant specification: `specs/004-mql5-agent-plugin/spec.md`
- Known constraints: local single-user trusted repositories only; stable public MCP, hosted ingestion,
  source mutation, persistent indexes, and MetaEditor control remain out of scope.

## Work completed

- Created Feature 004 specification, design, data model, experimental tool contract, quickstart, checklist,
  and dependency-ordered tasks. Cross-artifact analysis covered all 14 functional requirements and all
  six success criteria with no critical or high inconsistency.
- Added an optional `mcp>=1.28.1,<2` dependency and the `mql5-codegraph-mcp` stdio console entry point.
- Implemented a protocol-neutral `ProjectSession` with sanitized adapter errors, atomic snapshot
  replacement, unchanged-fingerprint reuse, and one-to-one Intelligence Kernel delegation.
- Exposed eight structured, non-destructive MCP tools through the official SDK and verified the installed
  console entry point with the official client against `tests/fixtures/basic_ea`.
- Added and validated four plugin skills for project onboarding, architecture navigation, change impact,
  and release gating.
- Added the repository-local `mql5-codegraph-internal` marketplace, cache-busted the finished plugin as
  `0.1.0+codex.20260723151025`, and confirmed it is installed and enabled.
- Renamed the test package from `tests/mcp` to `tests/mcp_adapter` after the full discovery gate exposed
  that the former shadowed the external `mcp` SDK package.
- Documented the private MCP boundary in
  [ADR-0003](../decisions/ADR-0003-private-mcp-plugin-alpha.md), README, architecture, and limitations.

## Decisions

- Keep the MCP surface private and experimental; its tool names are not a stable compatibility promise.
- Keep the server local over stdio with one in-memory trusted project snapshot, no network access,
  persistence, source editing, or raw-source retrieval.
- Pin the optional official MCP SDK below 2.x and require a deliberate compatibility review before upgrade.
- Preserve the existing slow-drip decision: dashboard request reads have an absolute deadline, while
  analysis work remains a separate budget problem. Hosted or untrusted ingestion stays blocked until an
  analyzer-wide work-budget contract and adversarial scaling regressions exist.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Focused MCP suite | `python -m unittest tests.mcp_adapter.test_service tests.mcp_adapter.test_protocol` | 9 passed in 2.854s |
| Full Python suite | `python -m unittest discover -s tests` | 101 passed in 9.328s |
| Python compilation | `python -m compileall -q src tests tools` | Exit 0 |
| Frontend lint | `npm --prefix web run lint` | Exit 0; no warnings |
| Frontend build | `npm --prefix web run build` | Vite 8.1.5 build passed in 625ms |
| Node dependency audit | `npm --prefix web audit --json` and `npm --prefix web audit --omit=dev --json` | 0 vulnerabilities |
| Python dependency audit | `pip-audit --strict` over `mcp>=1.28.1,<2` and `setuptools>=83` | No known vulnerabilities |
| Distribution build | `uvx --from build pyproject-build` | sdist and wheel built successfully |
| Distribution metadata | `uvx --from twine twine check dist\*` | Wheel and sdist passed |
| Wheel contents | Standard-library ZIP inspection | MCP package files and console entry point present |
| Plugin validation | Official `validate_plugin.py` | Passed |
| Skill validation | Official `quick_validate.py` for all four plugin skills | All four passed |
| Installed plugin | Cachebuster, `codex plugin add`, and `codex plugin list` | Version `0.1.0+codex.20260723151025` installed and enabled |
| MCP smoke | Official client over installed `mql5-codegraph-mcp` executable | Eight tools, fixture indexing/query, and structured error behavior passed |
| Source immutability | Service regression hashes all fixture files before and after indexing | No file created or modified |
| Privacy scan | 159 prospective files; sensitive filenames, emails, profile paths, workstation name, private-key/token formats | No matches |
| GitHub privacy | `gh repo view junet03/mql5-codegraph --json url,visibility,isPrivate` | `PRIVATE`, `isPrivate=true` |
| Git identity | Repository history and active config inspection | GitHub noreply email only |
| Directed project graph | `graphify update .` plus directed multigraph diagnostic | 1,581 nodes, 2,879 edges, 135 communities; no missing, dangling, self-loop, duplicate, or collapsed edges |

## Risks and unresolved questions

- Initial repository analysis has no universal wall-clock or analyzer-wide work budget. Four previously
  accepted low-severity adversarial scaling paths continue to block hosted or untrusted ingestion.
- MCP SDK 2.x is intentionally excluded until protocol and compatibility behavior are reviewed.
- The active in-memory snapshot becomes stale after source changes; skills require status/fingerprint
  checks and explicit re-indexing.
- The finished plugin is available only to fresh Codex tasks; the task that installed it cannot load newly
  contributed skills or MCP tools retroactively.
- Graphify reported 11 JSON/manifest source files that produced zero nodes. Directed graph integrity is
  clean; doc-semantic refresh remains optional because the local incremental command updates code only.

## Next objective

Start a fresh Codex task in one real private MQL5 repository, exercise all four skills against the bundled
MCP server, and record index latency plus evidence quality before expanding the alpha.
