# OS Catalog Live Validation Run Report (2026-02-08)

This run fixes the 2026-02-07 timeouts by using a smaller bbox for NGD per-collection `items` probes.

## Run Metadata

- Date: 2026-02-08 (UTC)
- Repo: `mcp-geo`
- Branch: `codex/os-catalog`
- Commit: `879a12558aab48c480f312e0edf418794f8c242d`
- Environment: devcontainer (Linux), Python 3.11.12
- Command:
  - `RUN_LIVE_API_TESTS=1 OS_LIVE_THROTTLE_SECONDS=0.2 OS_LIVE_MAX_RETRIES=6 OS_LIVE_BACKOFF_BASE=2.0 OS_LIVE_CONNECT_MAX_RETRIES=2 OS_LIVE_CONNECT_BACKOFF_BASE=0.5 pytest -q -s tests/test_os_catalog_snapshot.py --cov-fail-under=0`
- OS API base: `https://api.os.uk`
- Snapshot catalog: `resources/os_catalog.json` (178 probe entries)
  - `generatedAt`: `2026-02-07T23:55:33.283402+00:00`
  - NGD items probe bbox: `-0.127,51.503,-0.126,51.504`

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

Disk safety:
- No bulk downloads are performed.
- Raster/vector tiles are validated by fetching a single small tile each.
- Downloads API checks only fetch product metadata and download listings (no redirect-to-zip follows).

## Root Cause And Fix (v1 Timeouts)

Root cause:
- NGD per-collection `.../collections/{id}/items` probes previously used a ~2km bbox over central London
  (`-0.13,51.49,-0.11,51.51`).
- Several NGD collections can take > 10 seconds (and in some cases > 40 seconds) to return results for that bbox,
  even with `limit=1`, causing repeated read timeouts in unattended validation runs.

Fix:
- Introduced a dedicated small bbox for NGD items probes (`-0.127,51.503,-0.126,51.504`) in
  `scripts/os_catalog_refresh.py` and regenerated `resources/os_catalog.json`.
- This keeps probes bounded and stable while still validating endpoint availability, auth, and response shape.

## Performance Summary

Observed output from the live probe run:
- Probes: 178
- Successes: 176
- Rate limits (429): 0
- Auth failures (401/403): 2 (optional probes; see Entitlements Summary)
- Connect/read timeouts (synthetic status 0): 0
- Other non-200 errors: 0
- Latency seconds (mean / p50 / p95): `0.207 / 0.174 / 0.274`

## Entitlements Summary (Auth Errors)

The run observed two auth failures (401/403) on optional probes, which likely indicates that the current
`OS_API_KEY` does not have entitlements enabled for these APIs:
- `os.search.match.match` (OS Match & Cleanse API)
- `os.features.wfs.archive.capabilities` (WFS Product Archive)

## Final Status

PASS (all required live catalog validation tests passed).
