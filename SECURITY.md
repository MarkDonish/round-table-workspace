# Security Policy

Round Table Workspace is a local-first review workflow for AI-assisted
engineering decisions. Please treat security reports, claim-boundary reports,
and unsafe workflow examples as seriously as code vulnerabilities.

## Supported Versions

Security fixes are handled on the `main` branch first. The latest GitHub
release is the public reference point for packaged project state.

Older tags and demo artifacts may remain available for historical context, but
they are not maintained as long-term support branches unless a release note says
otherwise.

## Reporting a Vulnerability

If GitHub shows a private "Report a vulnerability" flow for this repository,
use that first.

If a private report flow is not available, open a minimal public issue that says
you have a security concern, but do not include exploit details, credentials,
tokens, private logs, local account data, or screenshots with secrets.

For public issues, include only:

- the affected command, document, or workflow area
- the kind of risk at a high level
- whether the issue is code, documentation, claim wording, or release evidence
- the safest way for the maintainer to reproduce or discuss it privately

## Claim Boundary Reports

This project is conservative about support claims. Please report wording that
appears to overstate:

- host-live support
- provider-live execution
- universal local-agent compatibility
- correctness guarantees for AI-generated work
- production readiness without current evidence

Use the claim-boundary issue template when the concern is about wording rather
than an exploitable code vulnerability.

## Handling Rules

Do not post secrets, API keys, cookies, `.env` files, database dumps, private
transcripts, or local machine paths that expose sensitive information.

Maintainers should keep fixes small, preserve the evidence trail, and update
tests, fixtures, or release checks when the issue changes a verified claim.
