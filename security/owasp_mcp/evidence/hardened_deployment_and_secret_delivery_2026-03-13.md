# Hardened Deployment and Secret Delivery

Verified on 2026-03-13 for the strict OWASP MCP profile.

- `Dockerfile` runs the production image as non-root (`USER appuser`).
- `ops/deployment/docker-compose.prod.yml` keeps the application on an internal Docker network, terminates TLS at the edge proxy, uses `read_only` filesystems, drops Linux capabilities, sets `no-new-privileges`, and constrains scratch space to `tmpfs`.
- The deployment profile mounts OS, NOMIS, and JWT secrets from files under `/run/secrets` and binds them into the app with `*_FILE` environment variables.
- `ops/deployment/Caddyfile.example` exposes `/mcp` and `/health` on the public edge while blocking `/metrics` from public access.
- `ops/deployment/README.md` defines the required secret files and run command for the hardened profile.
