# ONS Catalog Live Validation Run Report (2026-02-07, v2)

## Run Metadata

- Date: 2026-02-07 (UTC)
- Repo: `mcp-geo`
- Branch: `sota-mcp`
- Commit: `2937e43efd499501bc9cc26a5909d4b2ecca213e`
- Environment: devcontainer (Linux), Python 3.11.12
- Command:
  - `RUN_LIVE_API_TESTS=1 ONS_LIVE_THROTTLE_SECONDS=0.5 ONS_LIVE_COVERAGE_MIN=0.99 pytest -q -s tests/test_ons_catalog_snapshot.py --cov-fail-under=0`
- Target API base: `ONS_DATASET_API_BASE` (default) = `https://api.beta.ons.gov.uk/v1`
- Snapshot catalog: `resources/ons_catalog.json` (337 dataset entries)
  - `generatedAt`: `2026-02-07T11:27:58.063539+00:00`

## What Was Validated

The run executes `/Users/crpage/repos/mcp-geo/tests/test_ons_catalog_snapshot.py` with live mode enabled
(`RUN_LIVE_API_TESTS=1`).

Local snapshot checks:
- Snapshot file exists at `ONS_CATALOG_PATH` and is non-placeholder (`placeholder=false`).
- `items` is a list with >= 300 entries and all `id` values are present and unique.
- Each catalog entry validates required fields and types:
  - Required fields: `id`, `title`, `description`, `keywords`, `state`, `links`
  - Optional fields: `themes`, `topics`, `taxonomies` (string or list of strings)
- Link validation (snapshot):
  - `links` must be a dict
  - Required link keys: `editions`, `latest_version`, `self`
  - `links.latest_version.href` must be a non-empty string
- Field coverage sanity checks:
  - >= 90% of entries have a non-empty `title`
  - >= 70% of entries have a non-empty `description`

Live API checks:
- Live datasets listing (`GET /datasets` across all pages) succeeds and snapshot coverage is >= `ONS_LIVE_COVERAGE_MIN`
  (0.99 in this run).
- For every dataset `id` in `resources/ons_catalog.json`:
  - `GET /datasets/{id}` returns `200`, response `id` matches requested id, and key response fields validate.
  - `links.latest_version.href` is resolved and `GET <latest_version.href>` returns `200`.
  - Latest version metadata validates:
    - `edition` is a non-empty string
    - `version` is present (string or int)
    - `dimensions` is a non-empty list with object entries that include an `id` or `name` string

Timeouts and error monitoring:
- Each request is classified into one of:
  - `429` rate limit events (retries with exponential backoff)
  - upstream connect/timeout failures (`code=UPSTREAM_CONNECT_ERROR`)
  - other non-200 errors (recorded verbatim)
  - schema/field validation errors (200 responses with unexpected structure), recorded per dataset id

Backoff/throttling controls (environment variables, defaults unless noted):
- `ONS_LIVE_COOLDOWN_SECONDS=10.0` (pause before live `/datasets` listing)
- `ONS_LIVE_THROTTLE_SECONDS=0.5` (sleep between per-dataset validations)
- `ONS_LIVE_MAX_RETRIES=6` (retries for `429` at the test level)
- `ONS_LIVE_BACKOFF_BASE=5.0` (exponential backoff base seconds for `429`)
- `ONS_LIVE_COVERAGE_MIN=0.99` (catalog coverage threshold)

Note: the HTTP client (`tools/ons_common.py`) uses `timeout=5s` and retries connection/timeout failures internally.

## Performance Summary

- Total wall time: 269.24s (4 tests)
- Dataset detail validations: 337 `GET /datasets/{id}` calls
- Latest version validations: 337 `GET <links.latest_version.href>` calls
- Total dataset-related requests (detail + latest): 674
- Effective throughput (dataset validations only): ~1.25 datasets/sec
- Expected throttle time: ~168.5s (`337 * 0.5s`)
- Estimated request/overhead time (excluding throttle): ~100.7s total, ~0.30s per dataset

## Error/Timeout Summary

- Rate limits (429): 0
- Timeouts/connect errors (`UPSTREAM_CONNECT_ERROR`): 0
- Other non-200 errors: 0
- Schema/field validation errors: 0

## Actions Taken

- Strengthened snapshot and live link validation to ensure `links.latest_version.href` is present and usable.
- Extended the live validation to resolve and validate the latest version metadata for every dataset in the snapshot.
- Made `scripts/ons_catalog_refresh.py` runnable from the repo root by ensuring repo imports work without installing the package.

Related commit:
- `2937e43`: validate latest versions in live catalog checks

## Per-Error Detail

No errors were observed in this run.

## Final Status

PASS (all live catalog validation tests passed).

