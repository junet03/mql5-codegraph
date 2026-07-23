# 2026-07-23 — GitHub professionalization

## Objective

Turn the verified private alpha into a professional GitHub repository presentation and contribution
surface without changing its local trusted-input product boundary.

## Starting state

- Branch and commit: `codex/mql5-agent-plugin` at `4a2217f`
- Relevant specification: implemented Feature 004 private MCP plugin alpha
- Known constraints: repository remains private; the feature branch is not yet merged into `main`;
  private code scanning and branch protection may depend on the owner's GitHub plan.

## Work completed

- Designed an original 1280 by 640 MQL5 CodeGraph hero in SVG and PNG, with no MetaQuotes logos or
  third-party artwork, and added it to the README with CI, Python, license, and alpha-status badges.
- Added a detectable standard MIT `LICENSE`, separate `BRAND.md` artwork notice, independent-project
  trademark disclaimer, `SECURITY.md`, `CONTRIBUTING.md`, and `CHANGELOG.md`.
- Added CODEOWNERS, bug/feature issue forms, a structured pull-request template, and weekly Dependabot
  updates for Python, npm, and GitHub Actions.
- Added SHA-pinned GitHub Actions CI for Python 3.11 and 3.14 on Windows and Linux, dashboard lint/build,
  and distribution build/metadata validation.
- Added five standard-library plugin-bundle tests covering marketplace paths, manifest/MCP consistency,
  skill frontmatter, license alignment, and Social Preview image constraints.
- Recorded the licensing, brand, trademark, and release-governance decisions in
  [ADR-0004](../decisions/ADR-0004-licensing-and-github-release-governance.md).
- Updated the live private repository description and nine topics; disabled unused Wiki and Projects;
  enabled squash-only merging, branch updates, automatic head-branch deletion, Dependabot alerts,
  automated security fixes, and mandatory SHA-pinned Actions.
- Added matching dependency, Python, JavaScript, and GitHub Actions labels.
- Diagnosed the first hosted Linux CI failure as a test-fixture checkout mismatch: the golden CLI
  contract declares LF bytes, while the repository-wide MQL5 rule requested CRLF. Added fixture-specific
  LF attributes and a contract assertion without changing production fingerprint semantics.
- Enabled `main` branch protection with strict up-to-date CI, pull requests, stale-review dismissal,
  conversation resolution, linear history, admin enforcement, and force-push/deletion prevention.

## Decisions

- Use MIT for code and associated software documentation while reserving the project visual identity and
  artwork under `BRAND.md`.
- Keep artwork independent of MetaQuotes branding and include a non-affiliation disclaimer.
- Use SHA-pinned Actions plus Dependabot proposals instead of moving action tags.
- Use squash-only pull requests and keep `main` as the release branch.
- Do not enable a paid GitHub Advanced Security entitlement without separate approval.

## Verification evidence

| Check | Command or method | Result |
| --- | --- | --- |
| Banner render | Playwright Chromium render plus visual inspection | 1280 by 640 PNG, 525,462 bytes, correct hero content |
| Banner regression | `python -m unittest tests.test_plugin_bundle` | 5 passed in 0.013s |
| YAML validation | `uvx --from yamllint yamllint .github` | Exit 0 |
| Actions validation | `go run github.com/rhysd/actionlint/cmd/actionlint@latest .github/workflows/ci.yml` | Exit 0 |
| Full Python suite | `python -m unittest discover -s tests` | 106 passed in 9.524s |
| CI regression fix | `python -m unittest tests.test_cli.CliTests.test_legacy_contract_golden_bytes` | 1 passed in 0.072s; Git attributes resolve all three MQL5 fixtures to LF |
| Full Python suite after CI fix | `python -m unittest discover -s tests` | 106 passed in 9.350s |
| Hosted CI after regression fix | GitHub Actions run `30022280211` | All six jobs passed: dashboard, package, and Python 3.11/3.14 on Ubuntu and Windows |
| Python compilation | `python -m compileall -q src tests tools` | Exit 0 |
| Frontend lint | `npm --prefix web run lint` | Exit 0; no warnings |
| Frontend build | `npm --prefix web run build` | Vite 8.1.5 build passed in 423ms |
| Node dependency audit | Full and production `npm audit --json` | 0 vulnerabilities |
| Distribution build | `uvx --from build pyproject-build` | sdist and wheel built successfully with the MIT license |
| Distribution metadata | `uvx --from twine twine check dist\*` | Wheel and sdist passed |
| Plugin validation | Official plugin validator and four skill validators | Plugin and all skills passed |
| GitHub metadata | Repository API readback | Description, nine topics, squash-only, auto-delete, Wiki/Projects off |
| GitHub dependency security | Vulnerability-alert and automated-fix API readback | Alerts enabled; automated fixes enabled |
| GitHub Actions policy | Actions permissions API readback | Actions enabled; complete SHA pinning required |
| GitHub branch protection | Branch protection API readback | Strict six-check CI, pull requests, conversations, linear history, admins enforced; force push and deletion disabled |
| Directed project graph | `graphify update .` plus directed multigraph diagnostic | 1,628 nodes, 2,919 edges, 152 communities; no missing, dangling, self-loop, duplicate, or collapsed edges |
| Privacy scan | 178 prospective files; sensitive filenames, emails, profile paths, workstation name, and high-confidence key/token formats | No matches |

## Risks and unresolved questions

- GitHub does not expose a first-time Social Preview upload for this new private repository. The compliant
  PNG is committed and ready; upload becomes available if the repository is made public.
- CodeQL/default code scanning remains disabled because private-repository support can require a paid
  GitHub Code Security or Advanced Security entitlement.
- Graphify again reported 11 JSON/manifest files that produced zero AST nodes. Directed integrity is clean;
  the warning is unchanged and does not concern executable source.

## Next objective

Open the professionalization pull request, verify every hosted CI job, enable supported `main` protection,
and merge by squash when review is complete.
