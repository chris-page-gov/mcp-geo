# Hardened Production Deployment

This profile is the repo-backed reference deployment for the strict OWASP MCP
validation run.

## Security posture

- TLS terminates at `caddy`; the application container is not published directly.
- `mcp-geo` only joins the internal `app_internal` network.
- The runtime container is `read_only`, drops all Linux capabilities, enables
  `no-new-privileges`, and uses a bounded `tmpfs` scratch area.
- Remote `/mcp` requires app-layer JWT authentication with issuer, audience,
  scope, and subject validation.
- Session TTL and per-session tool call quotas are enabled by default in the
  deployment profile.
- Secrets are mounted as files under `/run/secrets` and consumed with
  `*_FILE` environment variables.
- Prometheus scrapes the private `/metrics` endpoint on the internal network.
- Vector forwards structured logs and audit/event files to a SIEM HTTP sink.

## Required secret files

Create the following files under `ops/deployment/secrets/` before deployment:

- `os_api_key.txt`
- `nomis_uid.txt`
- `nomis_signature.txt`
- `mcp_http_jwt_hs256_secret.txt`
- `tls.crt`
- `tls.key`

## Run

```bash
docker compose -f ops/deployment/docker-compose.prod.yml up -d
```

## Notes

- Replace `MCP_GEO_PUBLIC_HOST`, `SIEM_HTTP_ENDPOINT`, and `SIEM_HTTP_TOKEN`
  for the target environment.
- The reference profile keeps `/metrics` off the public edge and relies on the
  internal Docker network for scraping.
