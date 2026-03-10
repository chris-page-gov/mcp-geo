# Detailed System Design

## Server core

- **`server/main.py`**: FastAPI app, middleware (rate limiting), metrics endpoint.
- **`server/mcp`**: MCP routers for tools/resources/prompts; HTTP JSON-RPC handling.
- **`server/stdio_adapter.py`**: JSON-RPC over STDIO with Content-Length framing and
  optional line-based framing.

## Tool registry and metadata

- Tools register via side-effects in `tools/registry.py`.
- `server/mcp/tools.py` explicitly imports all tool modules to guarantee registration.
- Every tool exposes input/output JSON schema and annotations.

## Tools taxonomy

- **OS Places**: address lookup (`os_places.*`).
- **OS Names**: gazetteer name search (`os_names.*`).
- **OS NGD**: features by bbox (`os_features.query`).
- **Linked IDs**: resolve UPRN/USRN/TOID (`os_linked_ids.get`).
- **Maps**: `os_maps.render` returns a static map proxy URL; `os_vector_tiles.descriptor`.
- **Admin lookup**: cache-backed area geometry, containment, hierarchy.
- **ONS**: dataset search, dimensions, codes, observations, filter output.
- **Routing**: `os_route.descriptor` reports graph readiness and `os_route.get`
  resolves stops, computes routes, and returns geometry/steps/warnings.
- **MCP-Apps**: UI render tools that return a UI resource + structured payload.

## Boundary cache

- PostGIS cache for admin boundaries; used by `admin_lookup.*` tools.
- `BOUNDARY_CACHE_DSN` and related envs configure cache access.
- Cache status tool: `admin_lookup.get_cache_status`.

## Routing backend

- `server/route_graph.py` encapsulates graph readiness checks, pgRouting execution,
  and restriction warning assembly.
- The intended network source is OS Multi-modal Routing Network data captured via the
  OS Downloads API and loaded into a dedicated `routing` schema.
- Graph metadata is versioned in-table and mirrored with raw download provenance in the
  runtime directory so tool responses can report freshness.
- Current route profiles are `drive`, `walk`, `cycle`, `emergency`, and `multimodal`.
- Avoidance constraints support `avoidIds`, `avoidAreas`, and `softAvoid`.
- Turn restrictions are surfaced as warnings today; hard turn-enforcement remains a
  follow-up item.

## Route stop resolution

- `tools/os_route.py` resolves stops in this order:
  1. Explicit coordinates.
  2. UPRN via `os_places.by_uprn`.
  3. Postcode-only input via `os_places.by_postcode`.
  4. Address-like text via `os_places.search`.
  5. Place-like fallback via `os_names.find`.
- Ambiguous or unresolved stops return explicit route-specific errors such as
  `AMBIGUOUS_STOP` and `STOP_NOT_FOUND`.

## Route planner UI contract

- `os_apps.render_route_planner` now mirrors the `os_route.get` contract:
  `stops`, optional `via`, `profile`, `constraints`, and `delivery`.
- The widget still accepts legacy coordinate-prefill fields and the benchmark runner's
  `origin` / `destination` / `routeMode` payload for compatibility.
- The browser widget normalizes MCP payloads from `structuredContent`, `result.data`,
  and host notifications before calling `os_route.get`.

## Dataset caching (ONS codes)

- Short-lived in-memory TTL cache via `tools/ons_common.py`.
- Optional on-disk cache for ONS codes via `DatasetCache`.

## Error handling

- Consistent error envelope (`isError`, `code`, `message`, `correlationId?`).
- Upstream errors mapped with explicit taxonomy.

## Resilience

- Circuit breaker + jittered retries for OS/ONS upstream calls.

## Optional sidecar profile (scaled map delivery)

- Optional deployment assets: `scripts/sidecar/docker-compose.map-sidecar.yml`
  and `scripts/sidecar/smoke_sidecar_profile.sh`.
- Sidecars:
  - Martin (`http://<host>:3000`) for PostGIS vector tiles.
  - pg_tileserv (`http://<host>:7800`) for table/function tile access.
- Baseline compatibility contract remains mandatory:
  `os_maps.render` first, widget enhancement second, deterministic fallback
  skeletons (`map_card`, `overlay_bundle`, `export_handoff`) always available.
- Operational guide: `docs/sidecar_profile.md`.

## Offline and scenario-pack resources

- Offline PMTiles/MBTiles catalog: `resource://mcp-geo/offline-map-catalog`.
- Offline pack artifacts (when provisioned): `resource://mcp-geo/offline-packs/*`.
- Notebook scenario-pack resources:
  `resource://mcp-geo/map-scenario-packs-index` and
  `resource://mcp-geo/map-scenario-packs/*`.
- Offline tooling:
  `os_offline.descriptor` and `os_offline.get`.
