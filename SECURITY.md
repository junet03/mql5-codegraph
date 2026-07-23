# Security policy

## Supported versions

MQL5 CodeGraph is currently a private local alpha. Security fixes target the latest commit on `main`;
older commits and experimental branches are not maintained as separate supported releases.

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

The supported alpha is offline, local, single-user, and intended for trusted repositories. Reports are
especially useful when they concern:

- filesystem containment or source-viewer authorization;
- loopback, request deadline, or browser-origin controls;
- parser, resolver, or graph-expansion denial of service;
- unintended MCP source writes, persistence, or network access;
- evidence, ambiguity, or freshness being silently misrepresented.

Hosted, multi-tenant, and untrusted-repository ingestion are not supported until analyzer-wide work
budgets and the remaining adversarial scaling guardrails are implemented.
