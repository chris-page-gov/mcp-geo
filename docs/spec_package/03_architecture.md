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
  MCP --> Logs["Structured Logs + Correlation IDs"]
  MCP --> Metrics["Prometheus Metrics /metrics"]

  subgraph Boundary Pipeline
    Pipeline["Boundary Pipeline\n(download -> ingest -> validate)"] --> Cache
    Pipeline --> Reports["Run reports + ticker"]
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
- **MCP-Apps UI**: HTML resources delivered by `resources/read`.

## Optional map sidecar profile

For higher-throughput vector delivery, MCP Geo can run with optional sidecars:

- Martin (vector tiles from PostGIS)
- pg_tileserv (table/function tile endpoints)

This profile is additive and must not replace the baseline compatibility path
(`os_maps.render` plus fallback skeleton contracts).

Reference runbook: `docs/sidecar_profile.md`
