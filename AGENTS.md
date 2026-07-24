# MQL5 CodeGraph Working Agreement

## Session startup

- Read the newest entry in `docs/project-journal/`, relevant accepted ADRs in `docs/decisions/`, and the
  active feature specification before changing code.
- When `graphify-out/graph.json` exists, query it before broad repository scanning. Treat live source and
  tests as higher authority than generated graph output.
- Confirm the working tree state and preserve unrelated user changes.

## Architecture

- Keep the canonical graph and future Intelligence Kernel backend-neutral. CLI, web, and MCP are adapters.
- Preserve evidence, relationship origin, confidence, and ambiguity. Never turn an inferred edge into a fact.
- Do not add adapter-specific analysis logic when the operation belongs in the Intelligence Kernel.
- Prefer small, versioned schema changes with deterministic serialization and migration tests.

## Plugin consumer boundary

- When this repository is discovered through a plugin marketplace, plugin cache, package metadata, or
  local tool reference, treat the entire repository as immutable toolchain source.
- Do not edit, format, generate into, install into, stage, commit, or push this repository unless the user
  explicitly names MQL5 CodeGraph itself as the maintenance target and asks for a source change.
- Never infer that this repository is the MQL5 analysis target from the current directory or plugin path.
  Resolve a separate user-selected MQL5 project root before indexing or analysis.
- A request to analyze or modify an MQL5 project authorizes work only in that selected project. It does not
  authorize changes to this repository, its marketplace, plugin source, installed cache, or runtime.
- Agent instructions are defense in depth, not an operating-system access control. Untrusted consumer
  agents must use a read-only workspace or a separate OS/container identity without write access here.

## Verification

- Run the narrowest relevant tests during implementation and the strongest proportional suite before handoff.
- For Python changes, run `python -m unittest discover -s tests` and `python -m compileall -q src tests`.
- For dashboard changes, run `npm run lint` and `npm run build` in `web/`, then verify the local UI when behavior changed.
- Record exact verification evidence and unresolved risks in the current journal entry.

## Project journal and decisions

- Use `docs/project-journal/TEMPLATE.md` for each meaningful work session and update the journal index.
- Add or supersede an ADR when a choice constrains architecture, public contracts, storage, security, or compatibility.
- End every journal entry with one concrete next objective suitable for a fresh session.

## Graphify

- Build/query the directed project graph so call and dependency direction is retained.
- After tracked code, specifications, ADRs, or journal records materially change, run an incremental Graphify update.
- Run the graph health diagnostic and surface warnings; never hide dangling, collapsed, inferred, or ambiguous relationships.
- Keep `graphify-out/` generated and uncommitted. Commit canonical source, specifications, ADRs, and journal entries instead.

## Git

- Use Conventional Commits in English and do not commit generated build, cache, log, environment, secret, or Graphify output files.
- Before committing, inspect the staged scope, run `git diff --cached --check`, and ensure required verification is recorded.
