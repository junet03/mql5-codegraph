# ADR-0009: Isolate Graphify subprocess credentials by backend

- Status: Accepted
- Date: 2026-07-30
- Owners: Project maintainers

## Context

The optional Graphify adapter launches an operator-selected executable with `shell=False` and keeps
provider credentials out of command arguments and overlay manifests. Python subprocesses nevertheless
inherit the complete parent environment unless an explicit `env` is supplied. A maintainer or agent host
may hold GitHub, cloud, and multiple model-provider credentials that are unrelated to the selected
Graphify backend.

Graphify needs ordinary process runtime values plus endpoint, model, and credential variables for the
explicit backend. Giving the version probe or another provider access to every host variable violates the
least-authority boundary required for public release.

## Decision

- Construct an explicit cross-platform runtime allowlist for child process startup, temporary storage,
  locale, home discovery, and TLS trust configuration.
- Give `graphify --version` only that runtime environment and no provider credential.
- Give semantic extraction only the runtime environment plus the exact endpoint, model, and credential
  variables documented for the selected supported backend.
- Never forward credential variables through a wildcard or pass a provider secret in command arguments,
  overlay identity, artifact metadata, structured errors, or MCP lifecycle logs.
- Require a source change, documentation update, and regression coverage before another backend or
  environment variable is allowed.
- Continue to treat the operator-selected Graphify executable as trusted external code. Environment
  filtering is least-authority hardening, not filesystem or process sandboxing.

## Consequences

- Positive: unrelated values such as `GITHUB_TOKEN` and keys for unselected providers are unavailable to
  the Graphify child.
- Positive: a harmless version probe cannot observe a model credential.
- Positive: the authorized provider key remains compatible without being exposed on the process command
  line or in persistent overlay metadata.
- Cost: undocumented proxy, custom provider, or Graphify tuning variables are no longer inherited
  automatically.
- Risk: a malicious executable still runs with the operator's filesystem and OS identity and can access
  data available through those authorities.

## Guardrails

- Regression tests must inspect both version-probe and extraction environments using distinct unrelated
  host/provider credentials.
- Release secret scans must cover tracked content, distribution archives, and complete Git history.
- Public guidance must recommend trusted executables, least-privileged short-lived credentials, and hard
  OS/container isolation for untrusted execution.
