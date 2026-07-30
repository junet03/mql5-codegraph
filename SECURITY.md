# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.3.x | Yes |
| 0.2.x and older | No |

Security fixes target the latest public release and the latest commit on `main`. Experimental branches
and pre-release plugin snapshots are not maintained as separate supported versions.

## Reporting a vulnerability

Do not open a regular issue for a suspected vulnerability.

Use the repository's
[private security advisory form](https://github.com/junet03/mql5-codegraph/security/advisories/new)
or contact the repository owner through an approved private channel. Include:

- the affected commit or version;
- a minimal reproduction;
- the expected and observed security boundary;
- impact and preconditions;
- any suggested mitigation.

The maintainer aims to acknowledge a complete report within three business days and provide an initial
triage decision within seven business days. Timelines may change for complex findings.

## Security boundary

The supported public beta is offline, local, single-user, and intended for trusted repositories. Reports are
especially useful when they concern:

- filesystem containment or source-viewer authorization;
- loopback, request deadline, or browser-origin controls;
- parser, resolver, or graph-expansion denial of service;
- unintended MCP source writes, persistence, or network access;
- evidence, ambiguity, or freshness being silently misrepresented.

The dashboard accepts filesystem authority only from its startup CLI arguments. HTTP re-index requests
cannot change the authorized repository or include roots, and source reads select only indexed `.mq5` or
`.mqh` files from the active graph before containment, type, and size are rechecked.

Analyzer-wide work budgets are implemented, but hosted, multi-tenant, and untrusted-repository ingestion
remain unsupported until the remaining isolation, authentication, and adversarial-scaling boundaries are
designed and verified.

## Tokens and API credentials

The core analyzer, CLI, loopback dashboard, reference builder/search, and MCP stdio server require no
provider API key and do not read provider credentials.

The optional external Graphify overlay is the only workflow that may use a model credential:

- local processing permits only the explicit Ollama backend and verifies a configured endpoint is
  loopback;
- remote processing requires both `--processing-boundary remote` and `--allow-remote`;
- the Graphify version probe receives no provider secret;
- extraction receives only a small runtime environment plus variables for the explicitly selected
  backend; unrelated values such as `GITHUB_TOKEN` and credentials for other providers are not inherited;
- credentials are never placed in command arguments, overlay manifests, structured errors, or MCP
  lifecycle records.

Graphify remains an operator-selected external executable, not a sandboxed component. Use a trusted
installation, least-privileged and short-lived provider credentials, and OS/container isolation when the
documents or execution environment are untrusted. Do not store secrets in this repository, command
history, issue reports, compiler logs, or generated corpora. If a credential may have been exposed,
revoke or rotate it before reporting the incident privately.
