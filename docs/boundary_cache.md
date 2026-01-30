# Boundary Cache (PostGIS)

This server can use a local PostGIS cache for administrative boundary geometry.
The cache lets `admin_lookup.*` return full, validated boundaries without
relying on the live ArcGIS services.

## Why use the cache

- **Accuracy**: load official boundary datasets from ONS Open Geography Portal
  (UK) or OS Boundary-Line (Great Britain) and keep them in PostGIS.
- **Performance**: queries are local and fast (point-in-polygon and geometry fetch).
- **Reliability**: offline operation and deterministic responses.

## How it works

The cache stores boundaries in a single table (`admin_boundaries`) with:

- `geom` in EPSG:4326 (MultiPolygon)
- `bbox` and `centroid` columns for quick lookups
- `resolution` + `min_zoom`/`max_zoom` for zoom-aware selection
- `is_valid` and `valid_reason` for validity tracking

Metadata about the dataset is stored in `boundary_datasets` so we can report
freshness (release date + ingest time).

## Setup

1) **Create tables**

```bash
psql "$BOUNDARY_CACHE_DSN" -f scripts/boundary_cache_schema.sql
```

2) **Ingest a dataset**

Use the ingestion helper (requires `ogr2ogr` from GDAL):

```bash
python scripts/boundary_cache_ingest.py \
  --apply-schema \
  --dsn "$BOUNDARY_CACHE_DSN" \
  --dataset-id "ons_oa_2021_bgc" \
  --source "ONS Open Geography Portal" \
  --title "Output Areas (2021) EW BGC" \
  --url "/path/or/url/to/dataset.zip" \
  --level "OA" \
  --id-field "OA21CD" \
  --name-field "OA21CD" \
  --resolution "BGC" \
  --resolution-rank 1 \
  --min-zoom 9 \
  --max-zoom 12
```

Repeat with additional datasets or resolutions (e.g. full-resolution at high
zoom and generalised at low zoom).

3) **Enable the cache**

Set env vars:

```
BOUNDARY_CACHE_ENABLED=true
BOUNDARY_CACHE_DSN=postgresql://mcp_geo:mcp_geo@localhost:5432/mcp_geo
```

Restart the server.

## Zoom-aware resolution

The cache selects geometry using `min_zoom`/`max_zoom`:

- **High zoom (detail)**: `min_zoom >= 12` (full-resolution polygons)
- **Mid zoom**: `min_zoom >= 8` (generalised boundaries)
- **Low zoom**: `min_zoom <= 7` (coarse boundaries)

Set `min_zoom`/`max_zoom` during ingest to control which dataset is used at
different map zoom levels.

## Validity + freshness checks

During ingest, boundaries are run through `ST_MakeValid` and stored alongside:

- `is_valid` (boolean)
- `valid_reason` (from `ST_IsValidReason`)

Freshness is evaluated using dataset `release_date` (preferred) or `ingested_at`.
If the age exceeds `BOUNDARY_CACHE_MAX_AGE_DAYS`, results are marked stale in
the tool metadata.

## Query validation

Useful checks:

```sql
-- Count invalid geometries
SELECT COUNT(*) FROM admin_boundaries WHERE NOT is_valid;

-- Coverage by level
SELECT level, COUNT(*) FROM admin_boundaries GROUP BY level ORDER BY level;

-- Dataset metadata
SELECT dataset_id, release_date, ingested_at, record_count FROM boundary_datasets;
```

## Cache audit tools

The MCP server exposes simple cache auditing helpers:

- `admin_lookup.get_cache_status` reports dataset coverage, counts, and geometry availability.
- `admin_lookup.search_cache` searches cached areas by name/id/level (useful to confirm OA/LSOA polygons).

These are surfaced in the geography selector “Cache status” panel for quick checks.
