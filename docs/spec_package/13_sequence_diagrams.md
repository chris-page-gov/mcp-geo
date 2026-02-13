# Sequence Diagrams (Critical Tool Workflows)

This section provides sequence diagrams for the critical end-to-end flows. Diagrams are
expressed in Mermaid so they can render in Markdown-aware viewers.

## 1) Postcode lookup (os_places.by_postcode)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Client as MCP Client
  participant Server as MCP Geo (/tools/call)
  participant OS as OS Places API

  User->>Client: Ask about a UK postcode
  Client->>Server: tools/call os_places.by_postcode
  Server->>OS: GET /search/places/v1/postcode
  OS-->>Server: 200 + DPA results
  Server-->>Client: normalized UPRNs + provenance
  Client-->>User: Addresses + coordinates
```

## 2) Place name search (os_names.find)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Client as MCP Client
  participant Server as MCP Geo (/tools/call)
  participant OS as OS Names API

  User->>Client: Search for a place name
  Client->>Server: tools/call os_names.find
  Server->>OS: GET /search/names/v1/find?query=...
  OS-->>Server: 200 + gazetteer entries
  Server-->>Client: normalized results
  Client-->>User: Named features + coords
```

## 3) Admin containment lookup (admin_lookup.containing_areas)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Client as MCP Client
  participant Server as MCP Geo (/tools/call)
  participant Cache as PostGIS boundary cache
  participant ONS as ArcGIS / ONS live API

  User->>Client: "Which admin areas contain this point?"
  Client->>Server: tools/call admin_lookup.containing_areas
  alt Cache enabled and hit
    Server->>Cache: spatial lookup (ST_Contains)
    Cache-->>Server: cached area set
  else Cache miss or disabled
    Server->>ONS: live area containment queries
    ONS-->>Server: live area set
  end
  Server-->>Client: results + live/cache metadata
  Client-->>User: areas list
```

## 4) ONS dataset discovery + query (ons_search.query, ons_data.query)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Client as MCP Client
  participant Server as MCP Geo (/tools/call)
  participant ONS as ONS API

  User->>Client: Ask for ONS statistics
  Client->>Server: tools/call ons_search.query
  Server->>ONS: GET /datasets?query=...
  ONS-->>Server: dataset results
  Server-->>Client: datasets
  Client->>Server: tools/call ons_data.query
  Server->>ONS: GET /observations?dataset=...
  ONS-->>Server: observations
  Server-->>Client: results + pagination
  Client-->>User: metrics + context
```

## 5) Static map render (os_maps.render -> /maps/static/osm)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Client as MCP Client
  participant Server as MCP Geo
  participant OSM as OSM Tile Server

  User->>Client: "Show a map for this bbox"
  Client->>Server: tools/call os_maps.render
  Server-->>Client: render.imageUrl (/maps/static/osm)
  Client->>Server: GET /maps/static/osm?bbox=...
  Server->>OSM: GET /{z}/{x}/{y}.png
  OSM-->>Server: tile image
  Server-->>Client: image/png (cached)
  Client-->>User: static map image
```

## 6) MCP-Apps UI open (ui:// resources)

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant Client as MCP-Apps capable host
  participant Server as MCP Geo

  User->>Client: Start interactive workflow
  Client->>Server: resources/list
  Server-->>Client: ui:// resource descriptors
  Client->>Server: tools/call os_apps.render_* (e.g. route planner)
  Server-->>Client: UI payload + instructions
  Client->>Server: resources/read ui://...
  Server-->>Client: HTML (mcp-app)
  Client-->>User: Interactive UI widget
```

## 7) Boundary cache status (admin_lookup.get_cache_status)

```mermaid
sequenceDiagram
  autonumber
  participant Client as MCP Client
  participant Server as MCP Geo
  participant Cache as PostGIS boundary cache

  Client->>Server: tools/call admin_lookup.get_cache_status
  Server->>Cache: status query
  Cache-->>Server: counts + freshness
  Server-->>Client: cache status payload
```
