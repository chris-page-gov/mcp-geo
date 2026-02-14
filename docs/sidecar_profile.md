# Optional Map Sidecar Profile (Martin + pg_tileserv)

This profile is optional and is only for scaled/self-hosted map delivery. The
baseline compatibility path remains `os_maps.render` and fallback skeleton
contracts.

## Topology

- `mcp-geo` remains the MCP API and compatibility contract surface.
- `postgis` stores map layers/materialized views.
- `martin` serves vector tiles from PostGIS for high-volume tile access.
- `pg_tileserv` exposes table/function tiles and metadata for operational tools.

## Quick start

```bash
docker compose -f scripts/sidecar/docker-compose.map-sidecar.yml up -d --wait
```

Optional smoke check:

```bash
./scripts/sidecar/smoke_sidecar_profile.sh
```

## Security and boundaries

- Keep sidecars on private network segments.
- Enforce auth and IP controls at ingress (reverse proxy/API gateway).
- Do not expose raw PostGIS publicly.
- Continue to serve fallback `map_card`/`overlay_bundle` paths when sidecars are
  unavailable.

## Fallback behavior

If Martin/pg_tileserv is unavailable:

1. Keep `os_maps.render` available.
2. Return `degradationMode=no_ui` guidance where appropriate.
3. Use resource-backed exports (`export_handoff`) for large outputs.

## Config surfaces

- `BOUNDARY_CACHE_ENABLED`, `BOUNDARY_CACHE_DSN` for PostGIS access.
- `MCP_TOOLS_DEFAULT_TOOLSET=starter` for lean startup in constrained hosts.
- Sidecar compose profile at `scripts/sidecar/docker-compose.map-sidecar.yml`.
