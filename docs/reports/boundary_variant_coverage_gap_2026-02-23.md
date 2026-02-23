# Boundary Variant Coverage Hardening Report (2026-02-23)

## Scope

This report tracks boundary-variant availability hardening from baseline gap to
strict full-coverage resolution.

Evidence runs:

- Baseline gap run: `data/boundary_runs/20260223T082527Z/run_report.json`
  - Mode: `resolve`
  - Verification: `--verify-resolved`
  - Pipeline status: `COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED`
  - Variant gap state: `49` required variants still `not_published`.
- Hardened strict run: `data/boundary_runs/20260223T120022Z/run_report.json`
  - Mode: `resolve`
  - Verification: `--verify-resolved`
  - Pipeline status: `COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED`
  - Variant gap state: `0` required variants `not_published`.

## Definition of Complete (Boundary Variant Full Coverage)

Boundary variant hardening is complete when all of the following hold:

1. For every `boundary_family` and each required variant, status is
   `resolved` or `derived`.
2. For every `resolved` or `derived` variant, source verification is `status=ok`
   in `--mode resolve --verify-resolved`.
3. With `completion_definition.require_full_variant_availability=true`,
   `not_published` count for required variants is `0`.
4. Every non-direct authoritative mapping (`derived` or
   `availability=equivalent_variant`) carries explicit accuracy metadata so
   downstream hosts can surface zoom/precision cautions.
5. A reproducible run artifact exists (`run_report.json` + evidence files).

## Hardening Outcome

Strict hardened run (`20260223T120022Z`) meets the definition above:

- `pipeline_status`: `COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED`
- `family_errors`: `0`
- `exceptions`: `0`
- `status_counts`: `resolved=112`, `derived=44`, `not_published=0`
- `source_verification`: `ok=156`, `error=0`, `pending=0`

Availability composition:

- `published`: `106`
- `equivalent_variant`: `6`
- `derived_variant`: `44`

Accuracy metadata emitted in run evidence:

- Equivalent mappings: `published_equivalent_variant=6`
- Derived mappings:
  - `derived_generalised=14`
  - `derived_ultra_generalised=15`
  - `derived_extent_proxy=13`
  - `derived_from_coarser_source=2`

Current coarser-source warnings are explicit and bounded:

- `built_up_areas_uk`: `BFC <- BGG`
- `built_up_areas_uk`: `BFE <- BGG`

These now carry `derived_from_coarser_source` and zoom caution metadata.

## Baseline Gap Inventory (for Traceability)

Baseline (`20260223T082527Z`) missing required variants (`not_published`):
`49`

Reason breakdown:

- `variant_not_listed_in_manifest_downloads`: `32`
- `no_ckan_resource_match`: `14`
- `boundaryline_not_variant_specific`: `3`

Key affected families included:

- `os_boundaryline_gb_bulk`
- `built_up_areas_uk`
- `built_up_area_subdivisions_uk`
- NI fallback families
- Scotland/NI products that published only one high-resolution variant

These are now covered via equivalent or derived variant policy paths.

## Variant Glossary

- `BFC`: Full resolution, coastline-clipped.
- `BFE`: Full resolution, extent of the realm.
- `BGC`: Generalised (coarser than full), coastline-clipped.
- `BUC`: Ultra-generalised (much coarser), coastline-clipped.
- `BSC`: Super-generalised (optional publication in some families).
- `BGG`: Generalised variant label used by some ONS built-up-area families.

## Accuracy and Zoom Implications

Generalisation materially affects high-zoom interpretation:

- `BGC/BUC/BSC/BGG` can shift apparent edges relative to parcels, UPRNs,
  road links, and path links.
- Edge containment can differ between full and generalised variants.
- Precision-sensitive governance/reporting checks should prefer authoritative
  full-resolution where published, and visibly flag derived/equivalent use.

Hardening now makes this visible in machine output via variant-level accuracy
classification and zoom caution metadata.

## ONSUD/ONSPD for Lower-Cost Exact Checks

`ONSUD` and `ONSPD` exact-mode lookups remain key for boundary-edge validation
workflows without rendering heavy geometry first:

1. Resolve postcode/UPRN geography codes (`ons_geo.by_postcode`,
   `ons_geo.by_uprn`, `derivationMode=exact`).
2. Shortlist candidate boundary records by code.
3. Render only required geometries for final visual confirmation.

This supports low-cost, auditable checks where properties or assets touch
administrative edges.

## Built-up Area (BUA/BUASD) Requirement

Built-up area workflows remain solvable via existing primitives if cache content
is present and indexed:

1. Ensure `BUA` and `BUASD` are ingested into `admin_boundaries`.
2. Ensure boundary selection/search exposes these levels.
3. Run `os_map.inventory` against selected BUA/BUASD geometry for containment
   analysis over UPRNs/buildings/road links/path links.

## Remaining Follow-On Work

Variant resolution hardening is complete for resolve+verify gates. Remaining
follow-on work is downstream operational depth:

1. Complete full-manifest download/ingest/validate execution at scale so all
   resolved/derived variants are materialized in PostGIS tables.
2. Confirm BUA/BUASD are fully present in runtime cache and validated through
   end-to-end containment scenarios (UPRN/RoadLink/PathLink).
3. Add an explicit release report section that quantifies coarser-source usage
   by family so precision-sensitive consumers can apply policy controls.
