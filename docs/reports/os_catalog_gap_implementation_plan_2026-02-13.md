# OS Catalog Gap Implementation Plan (2026-02-13)

## Objective

Close all OS catalog and MCP tooling gaps identified in:

- `/Users/crpage/repos/mcp-geo/docs/reports/os_catalog_repo_usage_and_delivery_plan_2026-02-12.md`
- `/Users/crpage/repos/mcp-geo/docs/Geography/api-endpoints.md`

This revision restructures delivery into safe parallel workstreams for separate threads/subagents.

## Completion Criteria

The plan is complete when all are true:

1. Every endpoint family in the reference list has current probe evidence.
2. Catalog gaps are closed, including runtime-used paths missing from the catalog.
3. High-value unwired OS families are implemented or explicitly deferred with rationale.
4. Large OS responses follow `delivery=inline|resource|auto` with cache/export controls.
5. `PROGRESS.MD`, report docs, and endpoint documentation are internally consistent.

## Implementation Status (2026-02-13)

Completed workstreams:

- WS-INT-0
- WS-CAT-1
- WS-DL-2
- WS-SEARCH-3
- WS-MAP-4
- WS-POS-5
- WS-QGIS-6
- WS-OBS-7
- WS-DOC-8
- WS-INT-9

Current validation snapshot:

- Full regression: `pytest -q --cov-report=term-missing:skip-covered`
- Result: 90.16% coverage, 683 passed, 6 skipped.
- Refreshed OS catalog size: 273 entries (`resources/os_catalog.json`).

## Verified Baseline (Initial)

Family probe artifact:

- `/Users/crpage/repos/mcp-geo/docs/reports/os_endpoint_family_probe_2026-02-13.json`
- Result: 12/12 families returned HTTP 200.

Full catalog live probe snapshot (from test output):

- items: 178
- ok: 176
- rate_limits: 1
- auth_errors: 2
- connect_errors: 0
- other_errors: 0

## Gap Set to Close

### A. Implemented in runtime but missing from catalog

- `GET /features/ngd/ofa/v1/collections/{collection}/queryables`

### B. Additional catalog coverage gaps

- Missing OFA root probe: `GET /features/ngd/ofa/v1`
- Missing OS Net root probe: `GET /positioning/osnet/v1`
- Missing Downloads root probe: `GET /downloads/v1`
- Raster style coverage should explicitly include Road and Outdoor ZXY probes

### C. High-value catalog areas not yet wired to MCP

- OS Downloads API family
- OS Net API family
- WFS capabilities surfaces
- NGD OTA tiles surfaces
- Places `radius` and `polygon`
- Linked IDs paths: `identifiers`, `featureTypes`, `productVersionInfo`
- Raster WMTS/ZXY operational tools

### D. Documentation alignment gaps

- Endpoint-family doc structure and deduplication hygiene
- Execution tracking coverage in `PROGRESS.MD`

## Parallel Delivery Model

### Parallelization Rules

1. Use one integration owner for shared hot files to avoid repeated merge conflicts.
2. Each feature stream edits only its owned files plus stream-specific tests.
3. Shared-file edits are queued through integration checkpoints.
4. Every stream lands with focused tests; integration runs full regression.
5. Live probe reruns are integration-only to avoid duplicate API load and noisy variance.

### Shared Hot Files (integration-owned)

These files are edited only by integration streams `WS-INT-0` and `WS-INT-9`:

- `/Users/crpage/repos/mcp-geo/server/config.py`
- `/Users/crpage/repos/mcp-geo/server/mcp/tools.py`
- `/Users/crpage/repos/mcp-geo/server/mcp/resource_catalog.py`
- `/Users/crpage/repos/mcp-geo/tests/test_tool_upstream_endpoint_contracts.py`
- `/Users/crpage/repos/mcp-geo/PROGRESS.MD`
- `/Users/crpage/repos/mcp-geo/CHANGELOG.md`
- `/Users/crpage/repos/mcp-geo/README.md`
- `/Users/crpage/repos/mcp-geo/CONTEXT.md`

If a feature stream needs one of these touched, it records a handoff note for integration.

## Workstreams

### WS-INT-0: Contract Freeze and Integration Scaffolding (serial, first)

Dependencies: none

Scope:

- Define shared OS large-payload contract:
  - `delivery=inline|resource|auto`
  - common export metadata (`bytes`, `sha256`, `contentType`, `resourceUri`, `expiresAt`)
- Add/finalize config keys:
  - `OS_EXPORT_INLINE_MAX_BYTES`
  - `OS_DATA_CACHE_DIR`
  - `OS_DATA_CACHE_TTL`
  - `OS_DATA_CACHE_SIZE`
- Introduce shared helper module contract (for later stream reuse).
- Reserve tool-registration and resource-registration merge points.

Owned files:

- `/Users/crpage/repos/mcp-geo/server/config.py`
- `/Users/crpage/repos/mcp-geo/server/mcp/tools.py` (scaffold only)
- `/Users/crpage/repos/mcp-geo/server/mcp/resource_catalog.py` (scaffold only)
- shared helper module and helper tests

Acceptance:

- Downstream streams can implement tool families without redefining delivery behavior.

Focused tests:

- delivery-mode selection
- export metadata shape
- cache path safety

### WS-CAT-1: Catalog Gap Closure (parallel after WS-INT-0 starts)

Dependencies: none (can run in parallel with WS-INT-0; merge after WS-INT-0)

Scope:

- Update catalog refresh coverage for:
  - OFA root
  - OS Net root
  - Downloads root
  - OFA `queryables`
  - explicit Road/Outdoor ZXY styles
- Refresh `resources/os_catalog.json`.

Owned files:

- `/Users/crpage/repos/mcp-geo/scripts/os_catalog_refresh.py`
- `/Users/crpage/repos/mcp-geo/resources/os_catalog.json`
- `/Users/crpage/repos/mcp-geo/tests/test_os_catalog_snapshot.py`

Acceptance:

- Catalog includes all runtime-used and family-root probes required by endpoint matrix.

Focused tests:

- snapshot structure and endpoint presence assertions
- optional live probe run in integration stage

### WS-DL-2: OS Downloads MCP Tools (parallel wave 1)

Dependencies: WS-INT-0 contract freeze

Scope:

- Add `/Users/crpage/repos/mcp-geo/tools/os_downloads.py`:
  - `os_downloads.list_products`
  - `os_downloads.get_product`
  - `os_downloads.list_product_downloads`
  - `os_downloads.list_data_packages`
  - `os_downloads.prepare_export`
  - `os_downloads.get_export`
- Use shared delivery helper for large payloads.

Owned files:

- `/Users/crpage/repos/mcp-geo/tools/os_downloads.py`
- `/Users/crpage/repos/mcp-geo/tests/test_os_downloads_tools.py`

Integration handoff needed for:

- tool registration in `/Users/crpage/repos/mcp-geo/server/mcp/tools.py`

Acceptance:

- Downloads APIs are discoverable and return resource-backed artifacts when payload exceeds
  inline thresholds.

Focused tests:

- schema validation
- success path with mocked upstream
- auth/rate-limit/timeout/invalid JSON normalization

### WS-SEARCH-3: Places + Linked IDs Gap Closure (parallel wave 1)

Dependencies: none

Scope:

- Add Places coverage:
  - `os_places.radius`
  - `os_places.polygon`
- Add linked identifiers coverage:
  - `os_linked_ids.identifiers`
  - `os_linked_ids.feature_types`
  - `os_linked_ids.product_version_info`
- Update route-query guidance for new intents.

Owned files:

- `/Users/crpage/repos/mcp-geo/tools/os_places.py` or
  `/Users/crpage/repos/mcp-geo/tools/os_places_extra.py`
- `/Users/crpage/repos/mcp-geo/tools/os_linked_ids.py`
- `/Users/crpage/repos/mcp-geo/tools/os_mcp.py`
- stream-specific tests for these tools

Integration handoff needed for:

- tool registration in `/Users/crpage/repos/mcp-geo/server/mcp/tools.py`

Acceptance:

- Catalog path gaps for Places and Linked IDs are no longer runtime gaps.

Focused tests:

- per-tool input validation
- endpoint contract assertions
- error normalization

### WS-MAP-4: Raster Maps + WFS Capabilities (parallel wave 1)

Dependencies: WS-INT-0 if resource delivery helper is required for large XML

Scope:

- Add tools:
  - `os_maps.wmts_capabilities`
  - `os_maps.raster_tile`
  - `os_features.wfs_capabilities`
  - `os_features.wfs_archive_capabilities` (entitlement-aware)
- Ensure XML handling and optional resource fallback for large capability documents.

Owned files:

- `/Users/crpage/repos/mcp-geo/tools/os_maps.py`
- `/Users/crpage/repos/mcp-geo/tools/os_features.py`
- stream-specific tests for map/features capability endpoints

Integration handoff needed for:

- tool registration in `/Users/crpage/repos/mcp-geo/server/mcp/tools.py`

Acceptance:

- WMTS/WFS capabilities become first-class MCP tools with robust entitlement handling.

Focused tests:

- XML content-type parsing/forwarding
- 401/403 normalization
- response-size fallback behavior

### WS-POS-5: NGD OTA + OS Net Tooling (parallel wave 1)

Dependencies: WS-INT-0 for shared delivery behavior

Scope:

- Add OTA tools:
  - `os_tiles_ota.collections`
  - `os_tiles_ota.tilematrixsets`
  - `os_tiles_ota.conformance`
- Add OS Net tools:
  - `os_net.rinex_years`
  - `os_net.station_get`
  - `os_net.station_log`

Owned files:

- `/Users/crpage/repos/mcp-geo/tools/os_tiles_ota.py` (new)
- `/Users/crpage/repos/mcp-geo/tools/os_net.py` (new)
- stream-specific tests for OTA/OS Net

Integration handoff needed for:

- tool registration in `/Users/crpage/repos/mcp-geo/server/mcp/tools.py`

Acceptance:

- OTA and OS Net stop being catalog-only families.

Focused tests:

- discovery/success/error normalization
- endpoint contract assertions

### WS-QGIS-6: QGIS Linkage (parallel wave 2)

Dependencies: WS-MAP-4 and WS-POS-5 outputs available

Scope:

- Add QGIS helper tools:
  - `os_qgis.vector_tile_profile`
  - `os_qgis.export_geopackage_descriptor`
- Reuse style artifacts from:
  - `/Users/crpage/repos/mcp-geo/submodules/os-vector-tile-api-stylesheets/`
- Provide resource-backed descriptors for delayed-access artifacts.

Owned files:

- `/Users/crpage/repos/mcp-geo/tools/os_qgis.py` (new)
- QGIS-focused tests
- QGIS usage doc/report updates

Integration handoff needed for:

- tool registration and resource registration in integration-owned files

Acceptance:

- MCP clients can fetch QGIS-ready connection/export descriptors without inline payload bloat.

Focused tests:

- descriptor schema and URL validation
- resource URI integrity checks

### WS-OBS-7: Observability for New OS Surfaces (parallel wave 2)

Dependencies: WS-DL-2 plus at least one of WS-MAP-4/WS-POS-5 merged

Scope:

- Add metrics for new OS tools:
  - latency
  - payload bytes
  - inline-to-resource fallback counts
- Add structured export-lifecycle logs:
  - requested
  - queued
  - completed
  - failed

Owned files:

- metrics/logging implementation files
- observability regression tests

Integration handoff needed for:

- shared metric registry touchpoints in integration-owned files

Acceptance:

- New tool families have measurable operational behavior and export lifecycle visibility.

Focused tests:

- metrics increment assertions
- export lifecycle audit/log assertions

### WS-DOC-8: Documentation Closure (parallel wave 2, finalize in wave 3)

Dependencies: WS-CAT-1 + at least one feature stream landed

Scope:

- Keep endpoint matrix, catalog report, and tool coverage docs synchronized.
- Update implementation tracker entries and docs links.

Owned files:

- `/Users/crpage/repos/mcp-geo/docs/reports/*.md` (except integration-owned progress files)
- endpoint reference docs under `/Users/crpage/repos/mcp-geo/docs/Geography/`

Integration handoff needed for:

- final updates to `PROGRESS.MD`, `README.md`, `CHANGELOG.md`, `CONTEXT.md`

Acceptance:

- No doc contradictions on catalog coverage, runtime coverage, or delivery strategy.

Focused tests:

- doc link checks/manual consistency pass

### WS-INT-9: Final Integration, Regression, and Probe Closure (serial, last)

Dependencies: all other workstreams

Scope:

- Merge stream outputs and apply all shared hot-file changes.
- Register all new tools/resources.
- Finalize progress/changelog/readme/context updates.
- Run full regression and live probe closure run.

Owned files:

- all integration-owned shared files
- final test/probe artifacts and summary updates

Acceptance:

- Endpoints reviewed and implemented as planned, with consistent docs and passing tests.

Required validation:

- `pytest -q`
- catalog snapshot tests
- optional live catalog probe command for evidence refresh

## Parallel Execution Waves

Wave 0 (serial):

- WS-INT-0

Wave 1 (parallel):

- WS-CAT-1
- WS-DL-2
- WS-SEARCH-3
- WS-MAP-4
- WS-POS-5

Wave 2 (parallel):

- WS-QGIS-6
- WS-OBS-7
- WS-DOC-8 (partial, then finalize after integration)

Wave 3 (serial):

- WS-INT-9

## Subagent Safety Checklist

Each thread/subagent should follow this checklist:

1. Work only in assigned files and stream-specific tests.
2. Do not edit integration-owned shared hot files.
3. If blocked by shared files, create a short handoff note for integration instead of editing.
4. Keep commits stream-scoped and small.
5. Include focused tests in the same stream PR.

## Tracking Checklist

- [x] WS-INT-0 contract freeze merged
- [x] WS-CAT-1 catalog closure merged
- [x] WS-DL-2 downloads tool family merged
- [x] WS-SEARCH-3 places/linked IDs merged
- [x] WS-MAP-4 raster/WFS tooling merged
- [x] WS-POS-5 OTA/OS Net tooling merged
- [x] WS-QGIS-6 QGIS linkage merged
- [x] WS-OBS-7 observability updates merged
- [x] WS-DOC-8 documentation closure merged
- [x] WS-INT-9 final integration and regression merged
