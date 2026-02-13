# Final Report: Map Delivery Strategy for MCP Geo

## Executive summary

`mcp-geo` should adopt a **layered map delivery model** that defaults to compatibility-first outputs and progressively upgrades to richer interactivity when clients support it.

Recommended layered default:

1. **Layer 1 (always available):** tool-driven static map contract (`os_maps.render`) with textual fallback.
2. **Layer 2 (broad app compatibility):** resource-backed GeoJSON overlays and descriptors.
3. **Layer 3 (rich clients):** MCP-App interactive widgets (MapLibre-based UI resources).
4. **Layer 4 (GIS/pro workflows):** QGIS/vector tile/GeoPackage descriptors and optional sidecar map servers.

This model best serves personas from the public resident to professional GIS users, while reducing failure risk in heterogeneous MCP clients.

## Methodology

### User research structure

- Persona-based requirement extraction (`01_personas_and_user_journeys.md`).
- Journey-to-requirement mapping for six personas.
- Acceptance criteria framed around reliability, reproducibility, accessibility, and interoperability.

### Technical evaluation structure

- Longlist option scan (`02_map_delivery_options_longlist.md`).
- Trial shortlist with explicit pass/fail criteria (`03_trial_design.md`).
- Containerized execution and evidence capture (`04_trial_results.md`).
- External standards/ecosystem scan (`05_external_scan_os_and_community.md`).

## Options considered

### Option group A: Static delivery contracts

- `os_maps.render` + overlay metadata.
- Strongest client compatibility and lowest integration friction.

### Option group B: Interactive widget delivery

- `os_apps.render_*` resources for geography and boundary workflows.
- High value where host supports MCP Apps UI.

### Option group C: Standards/GIS interop

- WMTS/ZXY, OGC Features/WFS, GeoJSON, vector tile descriptors.
- Essential for analyst and GIS personas.

### Option group D: Sidecar map-server architecture

- GeoServer, QGIS Server, TileServer GL, Martin, pg_tileserv, Tegola, TiTiler.
- Valuable for scale/performance and enterprise workflows.

### Option group E: Notebook-first analysis workflows

- Jupyter-supported reproducible exploratory path.
- Useful for analysts/developers, not default for public users.

## Options selected for autonomous trial

Selected trial set (implemented and executed):

- `trial-1-static-osm`: cross-browser static route rendering.
- `trial-2-os-maps-render`: tool-contract-driven map rendering.
- `trial-3-geography-selector`: interactive widget overlay persistence.
- `trial-4-boundary-explorer`: local-layer interaction and polygon selection.

Rationale:

- Covers both broad-compatibility and high-value interactive workflows.
- Validates end-to-end from MCP tool output to visible map artifacts.
- Produces screenshots and machine-readable logs for regression tracking.

## Trial outcomes

- Final run: `8 passed`, `4 skipped`.
- Cross-browser static and tool-driven delivery: fully passed.
- Widget-interaction trials: validated in deterministic Chromium path.
- No blocking defects found in selected compatibility-first stack.

See:

- `research/map_delivery_research_2026-02/reports/trial_summary.md`
- `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_results.json`

## Persona fit and recommended delivery by journey

| Persona/Journey | Recommended primary mode | Secondary mode |
| --- | --- | --- |
| Public resident map lookup | `os_maps.render` static card | MCP widget if host supports UI |
| Analyst boundary/statistics exploration | MCP widget + resource overlays | notebook + export descriptors |
| Data journalist publication workflow | static image + provenance text | overlay resources for reproducibility |
| GIS specialist handoff | `os_qgis.*` descriptors + resources | sidecar map-server integration |
| App engineer multi-client support | layered fallback contract | progressive enhancement to widgets |
| Accessibility-first user | textual geography summary + map card alt text | optional keyboard-first widget |

## Recommendations for `mcp-geo`

### Immediate (high impact)

1. Promote `os_maps.render` contract as the canonical compatibility baseline in docs/tutorial flows.
2. Standardize fallback skeleton payloads (`map_card`, `overlay_bundle`, `export_handoff`).
3. Keep default toolset lean for initialization (`starter`) and defer heavy discovery.
4. Add explicit browser/widget support matrix in docs.

### Near-term (engineering)

1. Add deterministic host simulation utilities for UI resource tests across engines.
2. Add explicit “widget unsupported” guidance payload fields for clients.
3. Expand trial suite with mobile viewport projects and latency budgets.
4. Add optional PostGIS/vector-tile sidecar profile (Martin/pg_tileserv) for scaled deployments.

### Medium-term (product)

1. Add PMTiles/MBTiles delivery option for offline-friendly deployments.
2. Add map output quality checks (label density, contrast, and accessibility metadata).
3. Integrate notebook-generated scenario packs into resource outputs.

## Suggestions for OS API and ecosystem improvements

1. Publish explicit client-side best-practice bundles for MCP/AI-hosted contexts (worker/CSP-safe map patterns).
2. Provide normalized lightweight style profiles optimized for AI-client embedding constraints.
3. Expand official examples showing progressive fallback from full vector map to static-card output.
4. Provide clearer guidance for mixed UI/no-UI hosts where map rendering must degrade predictably.

## QGIS/map-server strategy decision

- **Do not fork QGIS** for this roadmap.
- Prefer **descriptor-first integration** with existing QGIS/QGIS Server capabilities.
- For server-side scaling, adopt sidecar architecture instead of monolithic in-process map serving.

## Conclusion

The optimal strategy is not a single rendering technology; it is a layered contract model that prioritizes reliability first, then progressively adds richer interactivity and GIS depth. The implemented trial system and research artifacts provide a repeatable baseline for future map delivery evolution in `mcp-geo`.
