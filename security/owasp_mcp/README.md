# OWASP MCP Validation Namespace

This directory contains the repo-pinned validation inputs and baseline outputs for
`mcp-geo` against the OWASP GenAI Security Project guide _A Practical Guide for
Secure MCP Server Development_, Version 1.0 (February 2026).

## Local command

Run the strict validator with the repo-local wrapper:

```bash
./scripts/validate-owasp-mcp-local
```

The default wrapper run writes artifacts to `output/owasp-mcp-validation/` and
fails when any `minimum_bar` or `required` control fails.

## Contents

- `control_catalog.json`: locked OWASP-MCP control set and pass criteria.
- `tool_risk_inventory.json`: explicit per-tool risk metadata used for applicability.
- `tool_manifest.lock.json`: generated tool manifest lockfile.
- `tool_manifest.lock.json.sig`: detached signature for the tool manifest.
- `tool_manifest.pub.pem`: public key used to verify the detached signature.
- `attestations/`: machine-readable deployment/runtime/governance evidence.
- `baseline/`: committed baseline validator outputs for the current repo snapshot.

## Strict evidence model

Controls backed by attestations fail when evidence is missing, invalid, or stale.
That is intentional for the `prod-strict` profile.
