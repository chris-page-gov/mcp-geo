# Backlog and Completion Plan

## Backlog (issues discovered)

### Recently completed
- **Map render tool**: `os_maps.render` now returns a static map proxy URL (OSM tile proxy).
- **Resources catalog**: expanded `/resources/*` with boundary manifest, latest report, cache status, and ONS cache index.
- **Circuit breaker**: added upstream circuit breaker with jittered retries for OS/ONS calls.
- **Route planning surface**: `os_route.get` and `os_route.descriptor` now provide a
  first-class routing contract, and `os_apps.render_route_planner` delegates to the
  solver instead of acting as a UI-only demo shell.

### High priority
1. **CI pipeline**: add lint/type/test/coverage CI with badges.
2. **MCP-Apps client compatibility**: validate UI initialization across Claude and Inspector; document required client steps.
3. **Restore strict quality gates**: raise pytest coverage back to `>=90%` and
   clear current static-analysis debt (`ruff`/`mypy`) so release gating is enforceable.
4. **Route graph operationalization**: automate OS MRN package ingestion,
   pgRouting graph builds, and environment bootstrap in deployment workflows.

### Medium priority
6. **Pagination for large tool results**: token-based paging for OS features and large datasets.
7. **Structured JSON logging sink**: allow log shipping to OTLP / JSON.
8. **ONS dataset caching**: expand on-disk cache to cover query outputs, add TTL and invalidation.
9. **Admin cache staleness policy**: configurable freshness thresholds with alerting.
10. **Performance regression tests**: boundary cache and maps proxy latency baselines.
11. **Route restriction depth**: promote turn restrictions and RAMI-derived hazards
    from warnings/penalties to full route-cost enforcement where data supports it.

### Low priority
12. **UI polish**: improve MCP-Apps widgets with real data bindings.
13. **CLI/Playground UX**: expose UI session details and rendering hints.
14. **Full documentation cross-links**: consolidate tutorial and evaluation docs.

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
- Fix MCP-Apps initialization flow for Claude and Inspector.
- Produce real UI screenshots and update docs.

### Phase 4 - Resources & observability (4-6 weeks)
- Populate resources with admin datasets and code lists (beyond current manifests).
- Add metrics for tool latency and cache hit rates.
- Add alerting guidance (Prometheus rules).
