# Walkthroughs (Common Scenarios)

## 1) Postcode lookup -> admin boundaries

1. Call `os_places.by_postcode` with a UK postcode.
2. Use the returned lat/lon and call `admin_lookup.containing_areas`.
3. Optionally open `os_apps.render_geography_selector` centered on the location.

Expected outcome:
- Address list with coordinates.
- Hierarchy of containing admin areas (from cache).

## 2) Area geometry -> map render

1. Call `admin_lookup.area_geometry` with an area ID.
2. Use bbox for `os_maps.render` or the UI geography selector.

Expected outcome:
- Bounding box and optional geometry, plus cache freshness metadata.

## 3) ONS dataset discovery -> observation query

1. Search datasets with `ons_search.query`.
2. Find versions via `ons_data.editions` and `ons_data.versions`.
3. List dimensions via `ons_codes.list` or `ons_data.dimensions`.
4. Query observations with `ons_data.query`.

Expected outcome:
- Dataset metadata and observation results.

## 4) Feature inspection workflow

1. Identify a feature collection.
2. Query with `os_features.query` for a bbox.
3. Open `os_apps.render_feature_inspector` with feature ID.

Expected outcome:
- UI widget with properties and linked IDs.

## 5) Boundary cache pipeline run

1. Run `scripts/boundary_pipeline.py`.
2. Use `scripts/boundary_status_ticker.py` during execution.
3. Inspect `run_report.json` for validation and size stats.

Expected outcome:
- Cache tables populated and validation OK.

## 6) Optional sidecar profile smoke check

1. Start the sidecar compose profile:
   `docker compose -f scripts/sidecar/docker-compose.map-sidecar.yml up -d --wait`.
2. Run the smoke script:
   `./scripts/sidecar/smoke_sidecar_profile.sh`.
3. Confirm baseline fallback path still works by calling `os_maps.render`.

Expected outcome:
- Martin and pg_tileserv endpoints respond.
- MCP Geo map baseline remains available if sidecars are stopped.

## 7) Offline pack + scenario-pack retrieval

1. Call `os_offline.descriptor` to list offline packs.
2. Call `os_offline.get` with `packId` to receive
   `map_card`/`overlay_bundle`/`export_handoff`.
3. Read `resource://mcp-geo/map-scenario-packs-index` and retrieve a scenario
   pack resource.

Expected outcome:
- Offline handoff contracts are deterministic.
- Scenario packs include notebook provenance metadata.

## Reference screenshots (pending)

![Inspector connected to MCP Geo](images/inspector-tools-resources.png)

![Boundary status ticker](images/boundary-status-ticker.png)
