# LandIS MVP Implementation Plan

## Summary

- Rebase or merge `codex/landis` onto current `main` first, because this branch diverged at `8d93cec` and `main` is now 8 commits ahead through `c39d5dd` on April 4, 2026.
- Treat the report added on `main` by commit `f47470b` as the authoritative requirements source; that commit adds research/docs only, so all LandIS server work is greenfield in this branch.
- Deliver the report-aligned MVP inside `mcp-geo`, with live ingestion in phase 1: product catalog, metadata, `soilscapes.point`, `soilscapes.area_summary`, one hero derived tool for pipe corrosion and shrink-swell risk, plus core resources and prompt templates.
- Do not include a new MCP-App workbench or route-intersection tool in this first slice; keep the MVP area-based and evidence-heavy.

## Key Changes

- Add a LandIS integration surface using repo-native naming and transport patterns:
  `landis_catalog.list_products`
  `landis_metadata.get`
  `landis_soilscapes.point`
  `landis_soilscapes.area_summary`
  `landis_derive.pipe_risk`
- Keep resource URIs on the existing scheme rather than inventing `landis://`:
  `resource://mcp-geo/landis-products`
  `resource://mcp-geo/landis-docs-soil-data-structures`
  `resource://mcp-geo/landis-docs-soil-classification`
  `resource://mcp-geo/landis-licence-current`
- Extend the existing prompt registry with three LandIS prompts rather than adding a new prompt subsystem:
  planner soil constraints brief
  water utility pipe risk brief
  catchment soil behaviour brief
- Add LandIS config in the existing settings model for enablement, portal/API base URLs, cache/warehouse locations, timeouts, and live-disable behavior; follow current repo error conventions with `LIVE_DISABLED`, `INVALID_INPUT`, `NOT_FOUND`, and normalized upstream-connect failures.
- Implement a LandIS product registry as checked-in resource data plus a loader/update script, so `list_products` and `metadata.get` can work even when live services are unavailable.
- Build ingestion into the existing geospatial stack with a split between lean runtime and heavier import tooling:
  runtime tools read normalized LandIS tables from PostGIS via `psycopg`
  ingestion scripts use the repo’s optional geospatial extras to load Soilscapes polygons and the minimum derived-layer inputs needed for the hero tool
- Scope the first warehouse to the minimum report MVP data model:
  Soilscapes polygons and class attributes
  metadata/product registry tables
  the specific LandIS layers needed for corrosion and shrink-swell screening
  provenance/version tables for every loaded dataset
- Keep the first derived tool area-based, not route-based:
  accept bbox or polygon geometry
  return risk band, raw underlying classes/values, explanation, caveats, and provenance/version block
  explicitly warn against site-specific inference and field-investigation substitution
- Wire the new tool modules into the existing explicit registration/import flow, tool search metadata, resource catalog, and prompts list/get surfaces.
- Update `PROGRESS.MD`, `CONTEXT.md`, `CHANGELOG.md`, and user-facing docs in the same change set as implementation milestones complete.

## Public Interfaces And Behavior

- New public tools:
  `landis_catalog.list_products`
  `landis_metadata.get`
  `landis_soilscapes.point`
  `landis_soilscapes.area_summary`
  `landis_derive.pipe_risk`
- New public resources under `resource://mcp-geo/landis-*` for product registry, classification/join guidance, and current licence/provenance notes.
- New public prompts in the existing prompts catalog; no protocol changes required.
- `landis_soilscapes.point` should accept WGS84 lat/lon first, with optional BNG support only if added consistently across point tools in the same change.
- `landis_soilscapes.area_summary` and `landis_derive.pipe_risk` should accept explicit geometry input; admin-area lookup to geometry remains a caller workflow, not hidden magic inside these tools.

## Test Plan

- Add unit tests for every LandIS tool covering validation, success, `LIVE_DISABLED`, not-found, and upstream normalization paths.
- Add fixture-backed warehouse tests for Soilscapes point lookup, polygon area summary, and pipe-risk derivation with deterministic expected outputs.
- Add resource-catalog and prompts tests proving LandIS resources/prompts appear in list/get surfaces and are readable through both MCP transport and `os_resources.get`.
- Add at least one end-to-end regression that starts from an admin area geometry, runs `landis_soilscapes.area_summary`, then runs `landis_derive.pipe_risk`, and verifies provenance plus caveat blocks are present.
- Run focused pytest first, then full `./scripts/pytest-local -q`; keep coverage at or above the repo gate.

## Assumptions And Defaults

- Base branch for implementation is current `main`, not the stale pre-merge branch state.
- The report on `main` is the authoritative functional brief; no separate Meeth materials are in scope except where they help validation later.
- Phase 1 assumes bulk/service access is sufficient to ingest the minimum warehouse now, but product-registry/resources must still work offline or when live access is disabled.
- The MVP optimizes for the utilities precedent from the report, so the first hero derived tool is pipe corrosion and shrink-swell risk, not planning-pack generation or hydrology narrative.
- No new frontend app is included in phase 1; UI or route-based work is a follow-on after the MVP tool/resource surface is stable.
