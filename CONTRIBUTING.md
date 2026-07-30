# Contributing to MQL5 CodeGraph

Thank you for helping improve evidence-backed intelligence for MQL5 projects.

## Prerequisites

- Python 3.11 or newer
- Node.js 22.13 or newer for dashboard work
- Git and GitHub CLI for repository workflows

Install the core and optional MCP runtime:

```powershell
python -m pip install -e ".[mcp]"
```

For dashboard work:

```powershell
npm --prefix web ci
```

## Working agreement

1. Read the newest entry in `docs/project-journal/`, relevant ADRs in `docs/decisions/`, the active
   feature specification, and applicable `AGENTS.md` instructions.
2. Preserve evidence origin, confidence, ambiguity, completion, and deterministic serialization.
3. Keep CLI, Web, and MCP as adapters; analysis semantics belong in the Intelligence Kernel.
4. Add focused regression coverage before changing behavior.
5. Do not commit generated graphs, build output, caches, logs, environment files, credentials, or private
   MQL5 source.
6. Use English Conventional Commits such as `fix(resolver): reject escaping include paths`.

## Verification

Run the strongest checks relevant to the change:

```powershell
python -m unittest discover -s tests
python -m compileall -q src tests tools
npm --prefix web run lint
npm --prefix web run build
```

For a release-sensitive change, also validate package metadata, dependency audits, the plugin bundle, and
the directed Graphify health diagnostic described in the current project journal.

## Pull requests

- Keep a PR focused on one objective.
- Explain why the change is needed and identify user-visible behavior.
- List exact verification commands and observed results.
- Call out compatibility, security, schema, storage, and performance risks.
- Update the active specification, ADRs, and journal when the change affects their contracts.
- Ensure `git diff --cached --check` passes before committing.

## Community

- Use [GitHub Discussions](https://github.com/junet03/mql5-codegraph/discussions) for design questions
  and early proposals.
- Use [GitHub Issues](https://github.com/junet03/mql5-codegraph/issues) for bounded, reproducible work.
- Follow [SECURITY.md](SECURITY.md) instead of opening a public issue for a vulnerability.
- GitHub maintains the canonical [**Contributors**](https://github.com/junet03/mql5-codegraph/graphs/contributors)
  list from commit history.

If the project helps your work, a [⭐ star](https://github.com/junet03/mql5-codegraph) helps other MQL5
developers find it. Contributions remain welcome regardless of whether you star the repository.
