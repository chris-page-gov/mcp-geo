# System Architecture

## High-level architecture

```mermaid
flowchart LR
  Client["MCP Client\n(Claude, Inspector, custom)"] -->|STDIO or HTTP| MCP["MCP Geo Server\n(FastAPI + MCP adapter)"]
  MCP --> Tools["Tools Layer\n(os_*, ons_*, admin_*)"]
  MCP --> Resources["Resources Layer\n(skills + ui://)"]
  Tools --> OS["Ordnance Survey APIs\n(OS Places, NGD)"]
  Tools --> ONS["ONS APIs\n(dataset, search, observations)"]
  Tools --> Cache["PostGIS Boundary Cache"]
  Tools --> RouteDB["PostGIS + pgRouting\n(routing schema)"]
  MCP --> Logs["Structured Logs + Correlation IDs"]
  MCP --> Metrics["Prometheus Metrics /metrics"]

  subgraph Boundary Pipeline
    Pipeline["Boundary Pipeline\n(download -> ingest -> validate)"] --> Cache
    Pipeline --> Reports["Run reports + ticker"]
  end

  subgraph Routing Pipeline
    MRN["OS Downloads API\n(OS MRN packages)"] --> Build["Routing build pipeline\n(provenance -> ingest -> graph tables)"]
    Build --> RouteDB
  end
```

## Transport architecture

```mermaid
flowchart TB
  subgraph STDIO
    ClientSTDIO["Client"] --> Adapter["stdio_adapter.py"] --> MCPServer["FastAPI app + MCP routers"]
  end
  subgraph HTTP
    ClientHTTP["Client"] --> MCPServer
  end
```

## Core components

- **FastAPI server**: core HTTP endpoints, routing, rate limiting, metrics.
- **MCP routers**: `/tools/*`, `/resources/*`, `/prompts/*`, `/mcp`.
- **Tools layer**: OS + ONS + admin lookup tools with schema metadata.
- **Boundary cache**: PostGIS-backed admin boundaries cache, served by admin tools.
- **Routing graph**: PostGIS + pgRouting schema populated from OS MRN packages,
  surfaced through `os_route.get` and `os_route.descriptor`.
- **MCP-Apps UI**: HTML resources delivered by `resources/read`.
- **Route planner widget**: `os_apps.render_route_planner` is an interactive shell
  over `os_route.get`, not a standalone route engine.

## Optional map sidecar profile

For higher-throughput vector delivery, MCP Geo can run with optional sidecars:

- Martin (vector tiles from PostGIS)
- pg_tileserv (table/function tile endpoints)

This profile is additive and must not replace the baseline compatibility path
(`os_maps.render` plus fallback skeleton contracts).

Reference runbook: `docs/sidecar_profile.md`

## Mixed host fleet behavior

MCP Geo is designed for mixed host fleets where some clients support MCP-Apps
UI and others are data-only:

- UI-capable hosts receive widget resources (`ui://`).
- Non-UI hosts receive deterministic fallback contracts.
- Both paths share the same map contract keys and provenance fields.

Reference guidance: `docs/map_embedding_best_practices.md`
