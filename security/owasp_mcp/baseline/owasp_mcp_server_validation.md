# OWASP MCP Server Validation (2026-03-16)

- Project: `mcp-geo`
- Profile: `prod-strict`
- Verdict: `compliant`
- Score: `100.0`
- Source baseline: `A Practical Guide for Secure MCP Server Development` `1.0`
- Source URL: https://genai.owasp.org/resource/a-practical-guide-for-secure-mcp-server-development/
- Source PDF SHA-256: `e0681dc7f64074f9dfceedda90533cf6db1cc3566508d28f77c69cc3cc2307b0`

## Summary

| Status | Count |
| --- | ---: |
| `pass` | 25 |
| `fail` | 0 |
| `not_applicable` | 2 |

## Required / Minimum-Bar Failures

- None

## Remediation Backlog

- No open remediation items.

## Control Results

### `OMCP-ARCH-001` Remote transport is inventoried `pass`

- Section: `secure architecture`
- Requirement: `required`
- Severity: `medium`
- Check type: `static_repo`
- Rationale: Remote /mcp transport is present and classified as remotely reachable.
- Evidence:
  - `server/mcp/http_transport.py`: FastAPI route declaration for /mcp

### `OMCP-ARCH-002` Remote /mcp requires authenticated ingress policy `pass`

- Section: `secure architecture`
- Requirement: `minimum_bar`
- Severity: `critical`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/remote_auth_and_session_controls_prod_strict.json`: Remote /mcp authentication, token binding, and session safeguards are deployed

### `OMCP-ARCH-003` JSON-RPC messages are validated before dispatch `pass`

- Section: `secure architecture`
- Requirement: `required`
- Severity: `high`
- Check type: `static_repo`
- Rationale: JSON-RPC requests are validated before dispatch.
- Evidence:
  - `server/mcp/http_transport.py`: JSON-RPC parse and params validation

### `OMCP-ARCH-004` Session isolation and cleanup exist `pass`

- Section: `secure architecture`
- Requirement: `required`
- Severity: `medium`
- Check type: `static_repo`
- Rationale: Session state is isolated and stale sessions are cleaned up deterministically.
- Evidence:
  - `server/mcp/http_transport.py`: Session map, TTL, and cleanup logic

### `OMCP-ARCH-005` Per-session quotas are evidenced `pass`

- Section: `secure architecture`
- Requirement: `required`
- Severity: `high`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/remote_auth_and_session_controls_prod_strict.json`: Remote /mcp authentication, token binding, and session safeguards are deployed

### `OMCP-TOOL-001` Explicit tool risk inventory covers every tool `pass`

- Section: `safe tool design`
- Requirement: `required`
- Severity: `medium`
- Check type: `static_repo`
- Rationale: Tool risk inventory matches the registered tool set.
- Evidence:
  - `security/owasp_mcp/tool_risk_inventory.json`: Explicit per-tool risk metadata

### `OMCP-TOOL-002` Signed tool manifest matches the registry `pass`

- Section: `safe tool design`
- Requirement: `minimum_bar`
- Severity: `critical`
- Check type: `static_repo`
- Rationale: Signed tool manifest matches the registered tool contracts.
- Evidence:
  - `security/owasp_mcp/tool_manifest.lock.json`: Committed tool manifest lockfile
  - `security/owasp_mcp/tool_manifest.lock.json.sig`: Verified OK

### `OMCP-TOOL-003` Tool additions and changes have approval evidence `pass`

- Section: `safe tool design`
- Requirement: `required`
- Severity: `high`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/tool_change_review_and_branch_protection_prod_strict.json`: Security-sensitive tool changes require protected-branch review

### `OMCP-TOOL-004` Tool metadata exposure is minimized `pass`

- Section: `safe tool design`
- Requirement: `required`
- Severity: `medium`
- Check type: `static_repo`
- Rationale: Tool names are listed separately from richer describe metadata.
- Evidence:
  - `server/mcp/tools.py`: Separate /tools/list and /tools/describe surfaces

### `OMCP-DATA-001` Tool contracts remain schema-bound `pass`

- Section: `data validation and resource management`
- Requirement: `minimum_bar`
- Severity: `high`
- Check type: `static_repo`
- Rationale: Every registered tool exposes input/output schemas for structured validation.
- Evidence:
  - `tools/registry.py`: Structured tool registry with schemas per tool

### `OMCP-DATA-002` Outputs are redacted and size-bounded `pass`

- Section: `data validation and resource management`
- Requirement: `required`
- Severity: `medium`
- Check type: `static_repo`
- Rationale: Redaction helpers and output size limits are present.
- Evidence:
  - `server/security.py`: Secret and key-name redaction helpers
  - `server/config.py`: Inline/export size limits

### `OMCP-DATA-003` Tool invocation stays structured JSON `pass`

- Section: `data validation and resource management`
- Requirement: `minimum_bar`
- Severity: `high`
- Check type: `static_repo`
- Rationale: Tool invocation surfaces enforce structured JSON payloads.
- Evidence:
  - `server/mcp/tools.py`: HTTP tools/call expects a JSON object
  - `server/mcp/http_transport.py`: JSON-RPC tools/call payload must be object

### `OMCP-PI-001` High-risk tools have HITL or equivalent approval `not_applicable`

- Section: `prompt injection controls`
- Requirement: `required`
- Severity: `high`
- Check type: `attestation`
- Rationale: Control does not apply for the current profile/tool inventory.

### `OMCP-PI-002` Long-lived sessions have compartmentalization evidence `pass`

- Section: `prompt injection controls`
- Requirement: `required`
- Severity: `high`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/remote_auth_and_session_controls_prod_strict.json`: Remote /mcp authentication, token binding, and session safeguards are deployed

### `OMCP-AUTH-001` OAuth 2.1/OIDC or equivalent protects remote /mcp `pass`

- Section: `authentication and authorization`
- Requirement: `minimum_bar`
- Severity: `critical`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/remote_auth_and_session_controls_prod_strict.json`: Remote /mcp authentication, token binding, and session safeguards are deployed

### `OMCP-AUTH-002` Token passthrough is prohibited `pass`

- Section: `authentication and authorization`
- Requirement: `required`
- Severity: `high`
- Check type: `static_repo`
- Rationale: No token passthrough surface was detected in the checked transport code.
- Evidence:
  - `server/maps_proxy.py`: Authorization bearer forwarding logic

### `OMCP-AUTH-003` Short-lived scoped tokens are evidenced `pass`

- Section: `authentication and authorization`
- Requirement: `required`
- Severity: `high`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/remote_auth_and_session_controls_prod_strict.json`: Remote /mcp authentication, token binding, and session safeguards are deployed

### `OMCP-AUTH-004` Restricted data uses centralized policy enforcement `not_applicable`

- Section: `authentication and authorization`
- Requirement: `required`
- Severity: `high`
- Check type: `attestation`
- Rationale: Control does not apply for the current profile/tool inventory.

### `OMCP-DEPLOY-001` Runtime hardening and network restrictions are evidenced `pass`

- Section: `secure deployment and updates`
- Requirement: `minimum_bar`
- Severity: `critical`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/hardened_runtime_and_secret_delivery_prod_strict.json`: Runtime hardening and secret-file delivery are configured for production

### `OMCP-DEPLOY-002` Secrets delivery is controlled beyond plain env vars `pass`

- Section: `secure deployment and updates`
- Requirement: `required`
- Severity: `high`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/hardened_runtime_and_secret_delivery_prod_strict.json`: Runtime hardening and secret-file delivery are configured for production

### `OMCP-DEPLOY-003` CI includes security gates `pass`

- Section: `secure deployment and updates`
- Requirement: `minimum_bar`
- Severity: `critical`
- Check type: `static_repo`
- Rationale: CI includes static analysis, dependency auditing, and secret scanning gates.
- Evidence:
  - `.github/workflows/ci.yml`: CI workflow security gates

### `OMCP-GOV-001` Audit trails are immutable enough to verify and redact `pass`

- Section: `governance`
- Requirement: `required`
- Severity: `medium`
- Check type: `static_repo`
- Rationale: Audit packs include integrity and redaction support.
- Evidence:
  - `server/audit/pack_builder.py`: Audit pack assembly and manifests
  - `server/audit/redaction.py`: Disclosure/redaction derivatives
  - `server/audit/integrity.py`: SHA-256 integrity verification

### `OMCP-GOV-002` Security-sensitive change review is evidenced `pass`

- Section: `governance`
- Requirement: `required`
- Severity: `medium`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/tool_change_review_and_branch_protection_prod_strict.json`: Security-sensitive tool changes require protected-branch review

### `OMCP-GOV-003` Monitoring and alerting evidence exists `pass`

- Section: `governance`
- Requirement: `required`
- Severity: `medium`
- Check type: `attestation`
- Rationale: Valid attestation evidence present.
- Evidence:
  - `/Users/crpage/repos/mcp-geo/security/owasp_mcp/attestations/monitoring_and_alerting_prod_strict.json`: Monitoring, alerting, and SIEM log routing are defined for production

### `OMCP-CONT-001` OWASP validator runs in CI and publishes artifacts `pass`

- Section: `tools and continuous validation`
- Requirement: `required`
- Severity: `medium`
- Check type: `static_repo`
- Rationale: OWASP validator is wired into CI and artifacts are uploaded.
- Evidence:
  - `.github/workflows/ci.yml`: Dedicated OWASP validation job and artifact upload
  - `scripts/validate-owasp-mcp-local`: Single local entrypoint wrapper

### `OMCP-CONT-002` Supply-chain posture checks exist `pass`

- Section: `tools and continuous validation`
- Requirement: `required`
- Severity: `medium`
- Check type: `static_repo`
- Rationale: Supply-chain posture checks include OpenSSF Scorecard or equivalent.
- Evidence:
  - `.github/workflows/ci.yml`: Supply-chain posture checks

### `OMCP-MIN-001` OWASP MCP minimum bar checklist passes `pass`

- Section: `minimum-bar checklist`
- Requirement: `minimum_bar`
- Severity: `critical`
- Check type: `static_repo`
- Rationale: All minimum-bar controls passed.
- Evidence:
  - `security/owasp_mcp/control_catalog.json`: Minimum-bar control dependencies
