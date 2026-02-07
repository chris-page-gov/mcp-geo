# ONS Catalog Live Validation Run Report (2026-02-07)

## Run Metadata

- Date: 2026-02-07 (UTC)
- Repo: `mcp-geo`
- Branch: `sota-mcp`
- Commit: `7f3aec655864f40ac9bb7679c8e352c573b6e628`
- Environment: devcontainer (Linux), Python 3.11.12
- Command:
  - `RUN_LIVE_API_TESTS=1 pytest -q -s tests/test_ons_catalog_snapshot.py --cov-fail-under=0`
- Target API base:
  - `ONS_DATASET_API_BASE` (default) = `https://api.beta.ons.gov.uk/v1`
- Snapshot catalog:
  - `resources/ons_catalog.json` (337 dataset entries, all `state=published`)

## What Was Validated

The run executes `/Users/crpage/repos/mcp-geo/tests/test_ons_catalog_snapshot.py` with live mode enabled.

Local snapshot checks:
- Snapshot file exists at `ONS_CATALOG_PATH` and is non-placeholder (`placeholder=false`).
- `items` is a list with >= 300 entries and all `id` values are present and unique.
- Each catalog entry validates required fields and types:
  - Required: `id`, `title`, `description`, `keywords`, `state`, `links`
  - Optional: `themes`, `topics`, `taxonomies` (string or list of strings)
- Field coverage sanity checks:
  - >= 90% of entries have a non-empty `title`
  - >= 70% of entries have a non-empty `description`

Live API checks:
- Live datasets listing (`GET /datasets` across all pages) succeeds and snapshot coverage is >= 95%.
- For every dataset `id` in `resources/ons_catalog.json`, the dataset endpoint resolves:
  - `GET /datasets/{id}` returns `200`
  - Response `id` matches the requested dataset id
  - Key response fields validate presence and types:
    - Required: `id`, `title`, `description`, `state`, `links`
    - Optional: `keywords`, `themes`, `topics`, `taxonomies`

Timeouts and error monitoring:
- Each dataset request is classified into one of:
  - `429` rate limit events (retries with exponential backoff)
  - upstream connect/timeout failures (`code=UPSTREAM_CONNECT_ERROR`)
  - other non-200 errors (recorded verbatim)
- Field validation errors (200 responses with unexpected schema) are recorded per dataset id.
- The test accumulates per-dataset errors and fails at the end with the first 10 errors printed.

Backoff/throttling controls (environment variables, defaults used in this run):
- `ONS_LIVE_COOLDOWN_SECONDS=10.0` (pause before live `/datasets` listing)
- `ONS_LIVE_THROTTLE_SECONDS=0.5` (sleep between dataset detail calls)
- `ONS_LIVE_MAX_RETRIES=6` (retries for `429` at the test level)
- `ONS_LIVE_BACKOFF_BASE=5.0` (exponential backoff base seconds for `429`)

Note: the HTTP client has its own connection retry handling and a request timeout:
- `tools/ons_common.py` uses `timeout=5s` and retries connection/timeout failures internally.

## Performance Summary

- Total wall time: 222.24s (4 tests)
- Dataset detail validations: 337 `GET /datasets/{id}` calls
- Effective throughput (overall): ~1.52 datasets/sec
- Expected throttle time: ~168.5s (`337 * 0.5s`)
- Estimated request/overhead time (excluding throttle): ~53.7s total, ~0.16s per dataset

## Error/Timeout Summary

- Rate limits (429): 0
- Timeouts/connect errors (`UPSTREAM_CONNECT_ERROR`): 0
- Other non-200 errors: 0
- Schema/field validation errors: 0

## Actions Taken

- Expanded live validation from a small sample to all datasets in the snapshot catalog.
- Added throttling and exponential backoff controls to reduce flakiness from rate limiting.
- Added snapshot and live field validation to catch schema drift early.
- Surfaced error/timeout counters and per-dataset error detail on failure.

Related commits:
- `f3b9883`: expanded live catalog validation to all datasets with throttling/backoff.
- `7f3aec6`: added field validation + error/timeout summary reporting.

## Per-Error Detail

No errors were observed in this run.

## Final Status

PASS (all live catalog validation tests passed).

