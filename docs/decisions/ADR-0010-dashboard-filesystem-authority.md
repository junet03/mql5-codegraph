# ADR-0010: Bind dashboard filesystem access to startup authority

- Status: Accepted
- Date: 2026-07-30
- Owners: Project maintainers

## Context

The dashboard is loopback-only and validates request authority and browser origin, but its legacy
`POST /api/analyze` body accepted a repository root and include roots from the HTTP caller. The source
viewer also joined a requested relative path to the active root before checking containment. These paths
were bounded for the intended single-user local deployment, yet they left filesystem authority in the
request dataflow and produced four high-severity CodeQL path-injection alerts when the repository became
public.

The local web adapter must not invent or broaden filesystem authority. Repository selection is an
operator action made when the process starts.

## Decision

- Resolve and store the repository root and include roots supplied through the local CLI before the HTTP
  server starts.
- Permit a dashboard analysis or re-index only against that stored authority. The legacy request fields
  may be omitted or may echo the exact authorized values; they cannot add or change a path.
- Build an immutable source-viewer allowlist from file nodes in the atomically published graph. HTTP file
  input selects from that allowlist instead of being joined directly to a filesystem root.
- Re-resolve the selected allowlisted file at read time and recheck root containment, extension, file
  type, and size to cover symlink replacement and filesystem changes after indexing.
- Render startup-authorized paths as read-only dashboard fields and remove machine-specific defaults.
- Build the dashboard before the package job creates distributions and inspect the wheel payload so a
  clean CI checkout cannot silently publish a package without its web assets.

## Consequences

- Positive: HTTP callers cannot expand the process's filesystem reach.
- Positive: the source viewer can read only an indexed `.mq5` or `.mqh` file that remains within the
  authorized repository at request time.
- Positive: package artifacts are independently checked for dashboard assets, notices, and forbidden
  local/reference content.
- Cost: changing repository or include roots requires restarting `mql5-codegraph serve` with new CLI
  arguments.
- Cost: an intentionally excluded source file is no longer available through the source viewer.
- Compatibility: clients that send the exact startup paths continue to work; arbitrary path selection
  through the HTTP body now returns a structured authorization error.

## Guardrails

- Tests must cover absent startup authority, mismatched root/include requests, parent traversal, and
  indexed-source selection.
- CodeQL, secret scanning, dependency alerts, and the repository's own cross-platform CI must be green
  before a public tag is created.
- This boundary does not turn the dashboard into an authenticated hosted service. Non-loopback,
  multi-user, and untrusted-repository deployments remain unsupported.
