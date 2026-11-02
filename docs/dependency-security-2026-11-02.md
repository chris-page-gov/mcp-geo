# Playground dependency candidate — 2 November 2026

The candidate updates MCP SDK 1.32.0, Zod 4.6.6, Vite 8.1.6 and affected
transitive dependencies in the playground. Every resolved copy falls outside
the 61 affected ranges in the reviewed alert snapshot. This does not establish
exploitation or a repository-wide security scan. The Python server and provider
policy are unchanged.

Frozen installation, production build and all six synthetic full-browser cases
pass with the matching Playwright Chromium. Two widget/routing cases fail on
the separately installed Chrome; temporary timing workarounds were removed.
The synthetic server now emits standard MCP text content alongside structured
output, preserving SDK response validation. Frontend CI uses Ubuntu 24.04:
the moving runner alias selected Ubuntu 26.04, which the existing Playwright
version cannot install on.

The separate OWASP gate currently fails ten expired attestation controls and
the resulting minimum-bar control. These cover authenticated ingress, quotas,
tool approval, session compartmentalisation, OAuth/OIDC, token scope/lifetime,
runtime hardening, secret delivery, change review and monitoring. The current
Python dependency audit reports no vulnerabilities. The attestation failures
are not evidence that a dependency update changed those operational controls.

Do not change attestation dates, expiry policy or required controls to make the
gate green. A reviewer with access to the named current operational evidence
must reverify each assertion before renewing it. This candidate does not
authorise deployment, authentication or credential changes. Full canonical
assurance remains required before merge or a complete verification claim.
