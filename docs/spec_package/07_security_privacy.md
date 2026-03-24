# Security and Privacy

## Secrets handling

- OS and ONS credentials can be injected via `*_FILE` environment variables.
- Remote `/mcp` can require HS256 JWT bearer tokens with issuer, audience, scope, and subject checks.
- Logs and generic exception responses redact configured `OS_API_KEY`,
  `NOMIS_UID`, `NOMIS_SIGNATURE`, `MCP_HTTP_AUTH_TOKEN`, and
  `MCP_HTTP_JWT_HS256_SECRET` values via `server/security.py`.

## Input validation

- All tool inputs validated against JSON schema.
- Postcode normalization and regex validation in OS Places.

## Transport

- HTTPS expected for live OS/ONS calls.
- Remote `/mcp` sessions support TTL-based cleanup and per-session tool quotas.
- STDIO adapter used for local client integrations.

## Risk areas

- UI clients must trust `ui://` resources and enforce CSP.
- Boundary cache DSN must be protected; avoid logging DSNs.

## Privacy

- No user PII stored by MCP Geo beyond upstream API calls.
- Cache stores boundary geometries and metadata only (no user data).
