# Boundary Variant Coverage Gap Report (2026-02-23)

## Scope

This report summarizes boundary-variant coverage gaps from:

- `data/boundary_runs/20260223T082527Z/run_report.json`
- Mode: `resolve`
- Verification: `--verify-resolved`
- Result: `COMPLETE_BOUNDARIES_RESOLVED_AND_VERIFIED`

Source resolution is verified, but variant availability is not yet complete for
all families.

## Missing Variant Inventory

`not_published` variants recorded with evidence: **49**

Breakdown by reason:

- `variant_not_listed_in_manifest_downloads`: 32
- `no_ckan_resource_match`: 14
- `boundaryline_not_variant_specific`: 3

By family:

- `built_up_area_subdivisions_uk`: `BFE,BGC,BUC`
- `built_up_areas_uk`: `BFE,BGC,BUC`
- `data_zones_2021_ni`: `BFE,BGC,BUC`
- `data_zones_2022_scotland`: `BFE,BGC,BUC`
- `intermediate_zones_2022_scotland`: `BFE,BGC,BUC`
- `island_groups_2022_scotland`: `BFE,BGC,BUC`
- `localities_2022_scotland`: `BFE,BGC,BUC`
- `lsoa_2021_ew`: `BUC`
- `msoa_2021_ew`: `BUC`
- `ni_dea_fallback`: `BFE,BGC,BUC`
- `ni_lgd_fallback`: `BFE,BGC,BUC`
- `oa_2021_ew`: `BUC`
- `oa_2022_scotland`: `BGC,BUC`
- `os_boundaryline_gb_bulk`: `BFE,BGC,BUC`
- `parishes_ew`: `BUC`
- `settlements_2022_scotland`: `BFE,BGC,BUC`
- `small_areas_2011_ni`: `BFE,BGC,BUC`
- `super_data_zones_2021_ni`: `BFE,BGC,BUC`
- `super_output_areas_2011_ni`: `BFE,BGC,BUC`
- `wards_uk`: `BUC`

## Variant Definitions

- `BFC`: Full resolution, coastline-clipped.
- `BFE`: Full resolution, extent of the realm (includes wider maritime/extent envelope).
- `BGC`: Generalised (coarser than full) coastline-clipped.
- `BUC`: Ultra-generalised (much coarser) coastline-clipped.
- `BSC`: Super-generalised (often published instead of `BUC` for some families).
- `BGG` (seen in ONS Built-up Areas): Generalised variant naming used by that
  product line; not currently mapped by this repo's variant policy.

## Accuracy and Zoom Implications

Boundary generalisation has direct impact on high-zoom correctness:

- At close zoom, `BGC/BUC/BSC` can visibly shift edges relative to parcels,
  roads, and UPRN points.
- Containment checks near boundary edges can disagree between full-resolution
  and generalised variants.
- For governance/reporting boundaries, precision-sensitive checks should prefer
  full-resolution (`BFC/BFE`) geometry where available.

Required explicit metadata for downstream safety:

- `meta.resolution` and `meta.resolutionRank` (already present in cache rows).
- Variant-derived provenance flag (`source=derived` vs published).
- Accuracy guidance field for UI/API consumers, for example:
  - `accuracy.class`: `authoritative_full`, `published_generalised`, `derived_generalised`
  - `accuracy.zoomCautionAbove`: zoom threshold where generalisation warnings
    should be surfaced.

## Why ONSUD/ONSPD Matter for Practical Accuracy

`ONSUD`/`ONSPD` provide exact-mode geography lookup anchors for UPRN/postcode.
These can be used to validate or triage boundary-edge ambiguity without
rendering heavy geometry first:

1. Resolve UPRN/postcode using `ons_geo.by_uprn` or `ons_geo.by_postcode`
   (`derivationMode=exact`).
2. Use returned geography codes to shortlist candidate boundaries.
3. Render only required boundary geometries for visual confirmation/testing.

This is especially useful for edge cases like "property spans or touches a
boundary" where cheap code-based gating avoids over-rendering.

## Built-up Areas (BUA/BUASD) Requirement

Built-up Areas are needed for "which UPRNs/RoadLinks/PathLinks are within this
area?" workflows. This is solvable in `mcp-geo` if we ensure:

1. `BUA` and `BUASD` are ingested into `admin_boundaries` with searchable level
   values (`BUA`, `BUASD`).
2. Boundary selection tools can find those levels from cache.
3. Existing inventory flow (`os_map.inventory`) is run over selected BUA/BUASD
   geometry to return UPRNs/buildings/road/path links.

No new inventory primitive is required if BUA boundaries are available in the
boundary cache and selectable in UI/tools.

## Resolution Strategy for Full Availability (Required)

To enforce full availability, apply all of the following together:

1. Family-specific required variants:
   - Stop treating `completion_definition.required_variants` as global for all
     families.
   - Use per-family/per-template requirements and explicit equivalence mapping
     (for example `BSC` can satisfy `BUC` where appropriate and documented).

4. Boundary-Line as non-variant source profile:
   - Keep `os_boundaryline_gb_bulk` as one published source stream
     (non-variant-specific), then derive additional generalised outputs locally
     where variant-complete availability is required.

5. Derived variant generation:
   - For families lacking published `BGC/BUC/BFE`, generate derived variants
     from best available full-resolution source.
   - Store as separate datasets with explicit derivation metadata:
     - `source=derived`
     - `derivedFromDatasetId`
     - `derivationMethod` (for example topology-preserving simplify)
     - `derivationTolerance`
     - `accuracy.class=derived_generalised`
   - Include derivation QA checks (topology validity, area-change thresholds,
     edge drift checks for sampled points/links).

## Immediate Next Implementation Targets

1. Add family-level required-variant evaluation and variant-equivalence rules in
   `scripts/boundary_pipeline.py`.
2. Extend variant parser/mapping to include `BSC` and `BGG` compatibility rules
   per family.
3. Implement derivation stage in boundary pipeline (published -> derived
   variants) with provenance fields.
4. Ensure boundary cache ingest includes `BUA` and `BUASD` levels and that
   selection/search workflows can target those levels.
