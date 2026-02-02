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
- **Maps**: `os_maps.render` descriptor; `os_vector_tiles.descriptor`.
- **Admin lookup**: cache-backed area geometry, containment, hierarchy.
- **ONS**: dataset search, dimensions, codes, observations, filter output.
- **MCP-Apps**: UI render tools that return a UI resource + structured payload.

## Boundary cache

- PostGIS cache for admin boundaries; used by `admin_lookup.*` tools.
- `BOUNDARY_CACHE_DSN` and related envs configure cache access.
- Cache status tool: `admin_lookup.get_cache_status`.

## Dataset caching (ONS codes)

- Short-lived in-memory TTL cache via `tools/ons_common.py`.
- Optional on-disk cache for ONS codes via `DatasetCache`.

## Error handling

- Consistent error envelope (`isError`, `code`, `message`, `correlationId?`).
- Upstream errors mapped with explicit taxonomy.

