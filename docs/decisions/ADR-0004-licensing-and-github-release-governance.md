# ADR-0004: Licensing and GitHub release governance

- Status: Accepted
- Date: 2026-07-23
- Owners: Project maintainers

## Context

The repository declared MIT in Python and plugin metadata but did not include a detectable root license.
The private alpha also lacked automated CI, contribution/security guidance, protected release flow, and
an independent visual identity. MQL5 and MetaTrader 5 are third-party trademarks, so project presentation
must not imply an official MetaQuotes relationship.

## Decision

- License the source code and associated software documentation under the standard MIT License with
  `junet03` as the 2026 copyright holder.
- Keep the MQL5 CodeGraph name, visual identity, and `docs/assets/` artwork outside the MIT grant under
  the separate notice in `BRAND.md`.
- Use original project artwork only; do not include MetaQuotes logos or official product artwork.
- State prominently that MQL5 CodeGraph is independent and not affiliated with, sponsored by, or endorsed
  by MetaQuotes Ltd.
- Require GitHub Actions CI for Python 3.11 and 3.14 on Windows and Linux, dashboard lint/build, and package
  validation before merging to `main`.
- Pin third-party GitHub Actions to complete commit SHAs and use Dependabot for Python, npm, and Actions
  update proposals.
- Prefer squash merges, delete merged branches automatically, and protect `main` with passing CI checks
  when the repository plan supports private branch protection.

## Consequences

- Positive: GitHub and downstream tooling can detect the code license consistently.
- Positive: contributors have explicit testing, security-reporting, and pull-request expectations.
- Positive: the project can use a distinctive banner without reusing restricted third-party brand assets.
- Positive: dependency and CI drift become visible through automated checks.
- Cost: visual assets have a separate usage notice from the software license.
- Cost: a four-combination Python matrix and dashboard/package jobs consume additional Actions minutes.
- Risk: private-repository branch protection or code scanning may depend on the owner's GitHub plan.

## Guardrails

- Keep `LICENSE` text standard so license detection is not made ambiguous.
- Do not add private source, credentials, account identifiers, or workstation paths to examples or artwork.
- Security reports must use private advisory or approved private contact channels, never regular issues.
- A public release must re-check third-party notices, repository visibility, security settings, and the
  trademark disclaimer before publication.
