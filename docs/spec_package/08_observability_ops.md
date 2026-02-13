# Observability and Operations

## Logging

- Structured logs via `loguru`.
- Correlation IDs included in error payloads when available.

## Metrics

- Prometheus endpoint at `/metrics`.
- Rate limiting counters and request latency histograms.

## Operational controls

- `RATE_LIMIT_PER_MIN` and `RATE_LIMIT_BYPASS`.
- `METRICS_ENABLED` toggle.
- `DEBUG_ERRORS` for stack traces (dev only).

## Cache monitoring

- `admin_lookup.get_cache_status` returns coverage and freshness metadata.
- Boundary ticker script for progress: `scripts/boundary_status_ticker.py`.

