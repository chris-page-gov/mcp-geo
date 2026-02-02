# Security and Privacy

## Secrets handling

- OS and ONS API keys are environment variables.
- Logs redact sensitive tokens via `server/security.py`.

## Input validation

- All tool inputs validated against JSON schema.
- Postcode normalization and regex validation in OS Places.

## Transport

- HTTPS expected for live OS/ONS calls.
- STDIO adapter used for local client integrations.

## Risk areas

- UI clients must trust `ui://` resources and enforce CSP.
- Boundary cache DSN must be protected; avoid logging DSNs.

## Privacy

- No user PII stored by MCP Geo beyond upstream API calls.
- Cache stores boundary geometries and metadata only (no user data).

