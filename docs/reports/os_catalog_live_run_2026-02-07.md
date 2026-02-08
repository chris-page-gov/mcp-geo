# OS Catalog Live Validation Run Report (2026-02-07)

## Run Metadata

- Date: 2026-02-07 (UTC)
- Repo: `mcp-geo`
- Branch: `codex/os-catalog`
- Commit: `1b40daef43d09538a4b02c899ff1e402e58bc4ad` (working tree dirty)
- Environment: devcontainer (Linux), Python 3.11.12
- Command:
  - `RUN_LIVE_API_TESTS=1 OS_LIVE_THROTTLE_SECONDS=0.2 OS_LIVE_MAX_RETRIES=6 OS_LIVE_BACKOFF_BASE=2.0 OS_LIVE_CONNECT_MAX_RETRIES=2 OS_LIVE_CONNECT_BACKOFF_BASE=0.5 pytest -q -s tests/test_os_catalog_snapshot.py --cov-fail-under=0`
- OS API base: `https://api.os.uk`
- Snapshot catalog: `resources/os_catalog.json` (178 probe entries)
  - `generatedAt`: `2026-02-07T22:22:53.817047+00:00`

## What Was Validated

The run executes `/Users/crpage/repos/mcp-geo/tests/test_os_catalog_snapshot.py` with live mode enabled
(`RUN_LIVE_API_TESTS=1`).

Local snapshot checks:
- Snapshot file exists at `OS_CATALOG_PATH` and is non-placeholder (`placeholder=false`).
- `items` is a list with a minimum size threshold (`OS_CATALOG_MIN_ITEMS`, default 150) and all `id` values are
  present and unique.
- Each catalog entry validates required fields and basic types:
  - Required fields: `id`, `kind`, `category`, `title`, `description`, `required`, `request`
  - `request` validates required fields: `method`, `url`, `params`
- Secret hygiene: the snapshot must not contain `key=` query params anywhere (prevents leaking `OS_API_KEY`).

Live API checks:
- Coverage: snapshot products vs live `GET /downloads/v1/products` meets `OS_LIVE_PRODUCTS_COVERAGE_MIN` (default 0.99).
- Coverage: snapshot NGD collections vs live `GET /features/ngd/ofa/v1/collections` meets
  `OS_LIVE_COLLECTIONS_COVERAGE_MIN` (default 0.99).
- For every catalog probe entry:
  - Execute the probe request and validate expected status code(s).
  - Validate content-type prefix when configured (JSON, GeoJSON, XML, PNG, YAML, etc).
  - Parse and lightly validate JSON/GeoJSON responses without printing payloads.

Backoff/throttling controls (environment variables, defaults unless noted):
- `OS_LIVE_THROTTLE_SECONDS=0.2` (sleep between probe requests)
- `OS_LIVE_MAX_RETRIES=6` (retries for `429` at the test level)
- `OS_LIVE_BACKOFF_BASE=2.0` (exponential backoff base seconds for `429`)
- `OS_LIVE_CONNECT_MAX_RETRIES=2` (retries for connection/read timeouts)
- `OS_LIVE_CONNECT_BACKOFF_BASE=0.5` (short backoff base seconds for connection/read timeouts)

Disk safety:
- No bulk downloads are performed.
- Raster/vector tiles are validated by fetching a single small tile each.
- Downloads API checks only fetch product metadata and download listings (no redirect-to-zip follows).

## Performance Summary

Observed output from the live probe run:
- Probes: 178
- Successes: 163
- Rate limits (429): 0
- Auth failures (401/403): 2 (optional probes; see Entitlements Summary)
- Connect/read timeouts (synthetic status 0): 13
- Other non-200 errors: 0
- Latency seconds (mean / p50 / p95): `1.885 / 0.331 / 10.152`

## Error/Timeout Summary

Required failures:
- 13 probes timed out (connection/read timeouts) against OS NGD OGC API Features `.../collections/{id}/items`
  endpoints (GeoJSON).

Sample failing required probes (first 10 emitted by pytest):
- `os.features.ngd.collection.bld-fts-building-2.items`
- `os.features.ngd.collection.bld-fts-buildingpart-1.items`
- `os.features.ngd.collection.lnd-fts-land-1.items`
- `os.features.ngd.collection.lnd-fts-land-2.items`
- `os.features.ngd.collection.lnd-fts-land-3.items`
- `os.features.ngd.collection.lus-fts-site-1.items`
- `os.features.ngd.collection.str-fts-structureline-1.items`
- `os.features.ngd.collection.trn-fts-roadtrackorpath-1.items`
- `os.features.ngd.collection.trn-ntwk-pathlink-1.items`
- `os.features.ngd.collection.trn-ntwk-pavementlink-1.items`

## Entitlements Summary (Auth Errors)

The run observed two auth failures (401/403) on optional probes, which likely indicates that the current
`OS_API_KEY` does not have entitlements enabled for these APIs:
- `os.search.match.match` (OS Match & Cleanse API)
- `os.features.wfs.archive.capabilities` (WFS Product Archive)

## Actions Taken

- Added OS catalog snapshot and refresh tooling:
  - `resources/os_catalog.json`
  - `scripts/os_catalog_refresh.py`
- Exposed the catalog as a data resource:
  - `resource://mcp-geo/os-catalog` via `server/mcp/resource_catalog.py`
- Added OS catalog validation tests:
  - `tests/test_os_catalog_snapshot.py`
- Fixed OS VTS template correctness in the vector tiles descriptor:
  - `tools/os_vector_tiles.py` now uses `/vts/tile/{z}/{y}/{x}.pbf` (singular `tile`, y/x order)
- Devcontainer robustness (local port conflicts):
  - `.devcontainer/docker-compose.yml` maps PostGIS to host port `5433` instead of `5432` to avoid conflicts with
    local PostgreSQL installs.

## Final Status

FAIL

The OS live probe run detected 13 required NGD collection item probes that timed out, indicating current reliability
issues (or overly strict timeouts) for a subset of OS NGD OGC API Features collections under this environment/config.

