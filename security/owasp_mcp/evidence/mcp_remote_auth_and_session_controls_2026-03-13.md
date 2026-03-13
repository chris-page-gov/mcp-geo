# Remote Auth and Session Controls

Verified on 2026-03-13 for the strict OWASP MCP profile.

- `server/mcp/http_transport.py` enforces bearer authentication modes, HS256 signature verification, issuer/audience/scope checks, and session subject binding.
- `server/mcp/http_transport.py` also enforces a default session TTL of 900 seconds and a default `tools/call` quota of 100 calls per session.
- `server/config.py` hydrates `MCP_HTTP_JWT_HS256_SECRET` from `MCP_HTTP_JWT_HS256_SECRET_FILE` so the runtime does not need raw secret values committed in config.
- `ops/deployment/docker-compose.prod.yml` enables `MCP_HTTP_AUTH_MODE=hs256_jwt`, constrains issuer/audience/scopes, and mounts the JWT secret via `/run/secrets`.
- `README.md` and `docs/Build.md` document the hardening contract for operators.
