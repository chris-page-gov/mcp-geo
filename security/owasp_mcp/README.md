# OWASP MCP Validation Namespace

This directory contains the repo-pinned validation inputs and baseline outputs for
`mcp-geo` against the OWASP GenAI Security Project guide _A Practical Guide for
Secure MCP Server Development_, Version 1.0 (February 2026).

## Local command

The owner confirmed on 3 November 2026 that there is no production deployment.
CI assesses the reviewed repository reference profile, with a separate production
evidence report. Run the reference assessment explicitly:

```bash
./scripts/validate-owasp-mcp-local --profile reference --format both \
  --output-dir output/owasp-mcp-reference --fail-on required
```

The default wrapper and CLI still select `prod-strict`, write to
`output/owasp-mcp-validation/` and fail when a required or minimum-bar control
fails. Production evidence remains stale; a passing reference report cannot
satisfy that profile or establish production readiness.

Reference reports use the verdict `reference_configuration_verified`, identify
their scope in JSON and Markdown, and require fresh, reference-only attestations
whose reviewed artefact hashes still match. Unknown profiles, changed or missing
artefacts, future verification dates and unbound evidence documents fail closed.
Existing manifest, applicability and minimum-bar checks remain active. See the
[current assessment](evidence/reference_profile_2026-11-03.md) for tested controls
and pre-deployment work.

## Tool contract maintenance

Any tool addition, removal, rename, or schema/description change must update
the OWASP MCP inputs in the same change:

1. Update `tool_risk_inventory.json` for the affected tool names.
2. Regenerate `tool_manifest.lock.json`, `tool_manifest.lock.json.sig`, and
   `tool_manifest.pub.pem` with `scripts/generate_owasp_mcp_tool_manifest.py`.
3. Rerun `./scripts/validate-owasp-mcp-local` and commit any baseline refresh
   that the change requires.

If these files drift from the registered tool set, `OMCP-TOOL-001`,
`OMCP-TOOL-002`, and the minimum-bar gate can fail in CI.

## Contents

- `control_catalog.json`: locked OWASP-MCP control set and pass criteria.
- `tool_risk_inventory.json`: explicit per-tool risk metadata used for applicability.
- `tool_manifest.lock.json`: generated tool manifest lockfile.
- `tool_manifest.lock.json.sig`: detached signature for the tool manifest.
- `tool_manifest.pub.pem`: public key used to verify the detached signature.
- `attestations/`: machine-readable deployment/runtime/governance evidence.
- `evidence/`: human-readable supporting evidence and captured GitHub policy state.
- `baseline/`: committed baseline validator outputs for the current repo snapshot.

## Strict evidence model

Controls backed by attestations fail when evidence is missing, invalid, or stale.
That is intentional for the `prod-strict` profile.

Preserve the historical production baseline and attestations. A new reference
assessment requires a fresh review of configuration and relevant tests, a dated
evidence document, matching SHA-256 entries including that document, and an
`environment` of `reference`. Do not renew production dates from reference tests.
The CI artefact retains both assessments with separate scopes.
