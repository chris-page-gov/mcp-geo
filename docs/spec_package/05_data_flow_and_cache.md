# Data Flow and Cache Pipeline

## Admin boundary cache pipeline

```mermaid
sequenceDiagram
  participant Operator
  participant Pipeline as boundary_pipeline.py
  participant Sources as ONS/NRS/NISRA/OS
  participant PostGIS
  participant Reports as run_report.json

  Operator->>Pipeline: Run pipeline
  Pipeline->>Sources: Resolve/download datasets
  Pipeline->>Pipeline: Extract + normalize
  Pipeline->>PostGIS: Ingest tables + indexes
  Pipeline->>Pipeline: Validate (schema/geom/rows)
  Pipeline->>Reports: Write run report + metrics
  PostGIS-->>Operator: Cached queries ready
```

## Cache read flow (admin_lookup)

```mermaid
sequenceDiagram
  participant Client
  participant MCP
  participant Cache as PostGIS
  participant Live as Live ONS/OS (fallback)

  Client->>MCP: admin_lookup.*
  MCP->>Cache: Query cache (if enabled)
  alt Cache hit
    Cache-->>MCP: Boundary geometry
    MCP-->>Client: Result + freshness metadata
  else Cache miss or disabled
    MCP->>Live: Live lookup
    Live-->>MCP: Response
    MCP-->>Client: Live fallback response
  end
```

## ONS codes caching

- `ons_codes.list` and `ons_codes.options` optionally cache results on disk
  (`ONS_DATASET_CACHE_ENABLED=true`).
- All ONS tools require live mode enabled (`ONS_LIVE_ENABLED=true`).

## Cache freshness

- Boundary cache status exposes freshness (`fresh`, `ageDays`) per dataset.
- `BOUNDARY_CACHE_MAX_AGE_DAYS` controls cache staleness evaluation.

