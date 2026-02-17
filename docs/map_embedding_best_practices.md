# MCP/AI Host Map Embedding Best Practices

This guide defines host-safe map embedding patterns for MCP/AI runtimes with
mixed UI capability.

## 1) Baseline-first contract

Always start with:

1. `os_maps.render` static contract
2. `overlay_bundle` data overlays
3. Widget enhancement (`os_apps.render_*`) only when UI support is explicit

Do not invert this order for convenience.

## 2) Worker/CSP-safe embedding pattern

- Serve worker files from same origin (`/maps/worker/maplibre-gl-csp-worker.js`).
- Keep `connectDomains` and `resourceDomains` minimal.
- Prefer proxied tile/style URLs for local-first and policy-constrained hosts.
- Treat host `ui/initialize` capabilities as authoritative.

## 3) Lightweight style profiles

Use `resource://mcp-geo/map-embedding-style-profiles` to select constrained
profiles by host limits:

- `compact_static`
- `lean_vector`
- `text_only_fallback`

## 4) Progressive fallback recipe

Recommended deterministic sequence:

1. Full UI host: widget + `ui://` resource.
2. Partial UI host: use inline widget metadata but keep `map_card`/`overlay_bundle`.
3. No UI host: return `map_card` + `overlay_bundle` + `export_handoff`.

## 5) Mixed-fleet operations guidance

For deployments with both UI and non-UI hosts:

- Keep one contract source of truth (`map_card`, `overlay_bundle`, `export_handoff`).
- Log host profile and degradation mode per response.
- Validate both paths in CI replay (UI-supported and UI-unsupported profiles).
- Avoid environment-specific payload keys.

## 6) Template checklist

- [ ] `os_maps.render` path verified.
- [ ] Fallback guidance fields populated (`widgetUnsupported*`, `degradationMode`).
- [ ] Style profile selected from catalog.
- [ ] Output validated against support matrix:
  `docs/map_delivery_support_matrix.md`.
