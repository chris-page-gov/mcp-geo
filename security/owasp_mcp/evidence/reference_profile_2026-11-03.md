# Reference profile assessment: 3 November 2026

## Scope

The owner confirmed on 3 November 2026 that there is no production deployment
and requested assessment of the reference profile only. This record assesses
repository configuration, implementation and synthetic regression tests.
Production attestations and their historical dates remain unchanged.

## Reviewed boundaries

- The HTTP implementation supports JWT signature, issuer, audience, scope and
  subject checks; authenticated routes and session quotas have synthetic tests.
  The reference Compose file enables JWT authentication, a 900-second session
  TTL and a 100-call quota, with secret-file configuration.
- The Dockerfile selects `appuser`. The reference app configuration uses an
  internal network, read-only filesystem, dropped capabilities, bounded scratch
  space and `no-new-privileges`. Caddy exposes the intended MCP/health routes
  and blocks metrics at the edge.
- CODEOWNERS identifies the owner of security-sensitive files. CI includes
  tests, static analysis, secret scanning, dependency audit, manifest integrity
  and reference validation. This records a review procedure and repository
  wiring; it does not attest that human approval is enforced by GitHub settings.
- Prometheus and Vector configuration describes internal metrics, security
  alerts and structured log delivery. Synthetic rate-limit/metrics tests verify
  the implementation; no external monitoring service was contacted.

The focused command passed 73 tests:

```sh
.venv/bin/python -B -m pytest tests/test_mcp_http.py \
  tests/test_config_secret_file.py tests/test_rate_limit_metrics.py \
  tests/test_owasp_mcp_validation.py --no-cov -q
```

The validator regressions cover altered and missing hash bindings, unsafe paths,
future evidence dates, production/reference separation, unknown profiles and
high-risk approval requirements. The full required CI remains the final candidate
verification plane.

## Pre-deployment requirements

The reference files contain example endpoints and placeholders. Before any
deployment, supply real credentials through approved secret delivery, configure
Prometheus bearer access to the protected metrics route, verify monitoring egress
and SIEM delivery, and test the actual ingress, session, token and hardening
boundaries. Capture current review protections and operational evidence then.
No live scraping, external delivery, production authentication or production
readiness is asserted here.

The accompanying `environment: reference` attestation binds this document and
the reviewed files by SHA-256. A changed or missing reviewed file invalidates
the reference assessment. This evidence cannot satisfy `prod-strict`; that
profile continues to report the expired production claims separately.
