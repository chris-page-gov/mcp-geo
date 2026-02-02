# Backlog and Completion Plan

## Backlog (issues discovered)

### High priority
1. **CI pipeline**: add lint/type/test/coverage CI with badges.
2. **MCP-Apps client compatibility**: validate UI initialization across Claude and Inspector; document required client steps.
3. **Map render tool**: `os_maps.render` is a descriptor stub; implement or proxy real static maps.
4. **Resources catalog**: expand `/resources/*` with real datasets (admin, code lists, boundary sets).
5. **Circuit breaker**: add upstream circuit breaker and jittered retries.

### Medium priority
6. **Pagination for large tool results**: token-based paging for OS features and large datasets.
7. **Structured JSON logging sink**: allow log shipping to OTLP / JSON.
8. **ONS dataset caching**: expand on-disk cache to cover query outputs, add TTL and invalidation.
9. **Admin cache staleness policy**: configurable freshness thresholds with alerting.
10. **Performance regression tests**: boundary cache and maps proxy latency baselines.

### Low priority
11. **UI polish**: improve MCP-Apps widgets with real data bindings.
12. **CLI/Playground UX**: expose UI session details and rendering hints.
13. **Full documentation cross-links**: consolidate tutorial and evaluation docs.

## Completion plan (phased)

### Phase 1 - Reliability and CI (2-3 weeks)
- Add GitHub Actions pipeline (lint, mypy, tests, coverage gate).
- Add release automation script (`release.yml`).
- Integrate structured JSON logging option.

### Phase 2 - Data correctness (2-4 weeks)
- Implement pagination for OS features and ONS outputs.
- Expand dataset caching (optional TTLs and invalidation).
- Extend validation rules for boundary pipeline (explicit overrides).

### Phase 3 - UI fidelity (2-4 weeks)
- Implement map render tool (static map or proxy to OS services).
- Fix MCP-Apps initialization flow for Claude and Inspector.
- Produce real UI screenshots and update docs.

### Phase 4 - Resources & observability (4-6 weeks)
- Populate resources with admin datasets and code lists.
- Add metrics for tool latency and cache hit rates.
- Add alerting guidance (Prometheus rules).

