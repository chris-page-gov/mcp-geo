# ONS Geo Source Resolution and Release Audit

This note explains how `mcp-geo` resolves ONS geography products, what the
main abbreviations mean, and why "latest package available" is not the same
thing as "fresh against the AddressBase schedule".

## Glossary

- `UPRN`: Unique Property Reference Number. This is the stable property
  identifier used across AddressBase and the ONS UPRN-derived products.
- `ONSPD`: ONS Postcode Directory. Exact postcode-to-geography lookup.
- `NSPL`: National Statistics Postcode Lookup. Best-fit postcode-to-geography
  lookup.
- `ONSUD`: ONS UPRN Directory. Exact UPRN-to-geography lookup.
- `NSUL`: National Statistics UPRN Lookup. Best-fit UPRN-to-geography lookup.
- `CHD`: Code History Database. Historical and successor-code reference from
  ONS.
- `RGC`: Register of Geographic Codes. Current geography-code reference from
  ONS.
- `PARNCP`: Parish and non-civil-parished area. MCP-Geo normalizes this to
  the public `PARISH` level, covering civil parishes, Welsh communities, and
  non-civil-parished areas while retaining raw source fields such as
  `PARNCP25CD`, `PARNCP25NM`, and `PARNCP25NW`.
- `House of Commons Library MSOA names`: optional non-official 2021 MSOA
  display labels. MCP-Geo stores them as `displayName` / `displayNameWelsh`
  sidecar values and keeps ONS/RGC `currentName` as the official name.
- `GSS code`: Geography code used across UK statistical geography products.
- `CKAN`: Open-source data catalogue software used by many government open-data
  portals, including data.gov.uk. See [CKAN](https://ckan.org/) and the
  [data.gov.uk API documentation](https://guidance.data.gov.uk/get_data/api_documentation/).
- `DCAT`: W3C data-catalogue vocabulary used for structured metadata exchange.
  See [W3C DCAT 3](https://www.w3.org/TR/vocab-dcat-3/).
- `OGC API - Records`: Standards-based search and discovery API for catalogue
  records. The ONS Open Geography Portal exposes this at its
  [Search API definition](https://geoportal.statistics.gov.uk/api/search/definition/).

## Source strategy

`mcp-geo` now uses a mixed-source model because no single catalog surface is
good enough for every job:

1. `OS AddressBase` publication schedule is the freshness truth for UPRN
   epochs. The repo pins that schedule in
   [resources/addressbase_epoch_schedule.json](/Users/crpage/repos/mcp-geo/resources/addressbase_epoch_schedule.json),
   derived from official OS AddressBase publication information and used by the
   live validator. Public product background is on the
   [OS AddressBase page](https://www.ordnancesurvey.co.uk/products/addressbase).
2. `data.gov.uk` CKAN is the primary dated-package history for `ONSUD`, `NSUL`,
   `CHD`, and `RGC`. It is strong for package identity and version history, but
   not enough on its own for freshness.
3. The `ONS Open Geography Portal` Records API is the best machine-readable
   discovery surface for the current portal dataset item. See the ONS Open
   Geography Portal [Search API definition](https://geoportal.statistics.gov.uk/api/search/definition/)
   and the live dataset-items endpoint
   [collections/dataset/items](https://geoportal.statistics.gov.uk/api/search/v1/collections/dataset/items?q=ONSUD&limit=5).
4. The `ONS Open Geography Portal` RSS feed is the operational notice surface
   for pauses, corrections, and release issues. See the
   [RSS feed](https://geoportal.statistics.gov.uk/api/feed/rss/2.0).
5. The `ONS Open Geography Portal` DCAT feed is useful for bulk catalog
   ingestion, but it is noisy for "pick the latest data package" because it
   includes user guides, metadata records, and older historical items. See the
   [DCAT-AP feed](https://geoportal.statistics.gov.uk/api/feed/dcat-ap/3.0.0.json).

## Why availability and freshness are separate

For `ONSUD` and `NSUL`, the important questions are different:

- What is the newest public ONS package we can resolve from the catalogs?
- Is that package current against the latest published AddressBase epoch?

Those can diverge. As of April 9, 2026:

- the repo's tracked AddressBase schedule says the latest published epoch is
  `126` on `2026-04-02`
- the newest resolvable public `ONSUD` and `NSUL` packages still resolve to
  `Epoch 123`
- the Open Geography Portal RSS feed carries UPRN-product pause/correction
  notices from February and March 2026

That means `Epoch 123` is "latest currently resolvable from the public ONS
catalogs" but still `lagging` against the authoritative AddressBase publication
schedule.

## What `ons_geo.release_audit` does

Use `ons_geo.release_audit` when you need the operational truth rather than
just a cache lookup. It combines:

- the tracked AddressBase epoch schedule
- current ONS Open Geography Portal RSS notices
- current ONS Open Geography Portal dataset discovery
- current package resolution from the configured manifest

The output is designed to answer:

- what package was resolved
- what epoch it contains
- what the latest published AddressBase epoch is
- how many epochs behind the resolved package is
- whether the lag is likely explained by current publisher notices

## Why CHD and RGC are separate support datasets

`CHD` and `RGC` are not interchangeable:

- `RGC` tells us what the current valid geography-code universe is
- `CHD` tells us how historical codes changed, split, merged, or were replaced

`mcp-geo` uses both so year-suffixed schema changes and retired codes can be
normalized into stable semantic geography families instead of silently falling
out of the lookup path.

## Parish/PARNCP and MSOA display-name semantics

`PARISH` is the public level name used by `ons_geo.*` and `admin_lookup.*`.
It maps to ONS parish and non-civil-parished area sources, currently including
`PARNCP_MAY_2025_EW_BGC` for generalized England/Wales boundary fallback.
Use `PARISH` in requests such as `admin_lookup.find_by_name` and
`ons_geo.area_summary`; preserve `PARNCP25CD`, `PARNCP25NM`, and `PARNCP25NW`
when inspecting raw rows or source manifests.

House of Commons Library 2021 MSOA names are ingested from
`https://houseofcommonslibrary.github.io/msoanames/MSOA-Names-Latest2.csv`
as display-name sidecar metadata. The current configured source is version
`2.3`, published `2026-02-13`, under the Open Parliament Licence. These labels
are suitable for readable display but are not official ONS replacements:
`currentName` remains the ONS/RGC name, while `displayName`,
`displayNameWelsh`, and `displayNameSource` carry the Library label and
provenance. If this optional sidecar is unavailable during refresh, core
postcode/UPRN geography readiness is not degraded; the affected MSOA display
labels are simply absent.

## Practical guidance

- Use `ons_geo.by_postcode` and `ons_geo.by_uprn` for lookups against the local
  normalized cache.
- Use `normalizedGeographies.parish` when the cache source contains PARNCP
  fields and a parish/community/non-civil-parished area is needed.
- Use `normalizedGeographies.msoa.displayName` only as a display label; keep
  `normalizedGeographies.msoa.currentName` for official ONS/RGC naming.
- When adding another geography level or display-name sidecar, start with the
  shared contract in `docs/agent_context/geography-extension-contract.md` and
  the registry in `server/geography_levels.py`; do not patch one surface only.
- Use `ons_geo.cache_status` to check whether the cache is populated and
  whether primary/support datasets are degraded.
- Use `ons_geo.release_audit` when you need to know whether the published ONS
  UPRN products are behind the current AddressBase schedule, or whether a
  correction/pause notice is active.
- Prefer epoch numbers over month labels when comparing UPRN products. Month
  names are not reliable enough on their own.

## Current refresh limitations and planned redesign

The current `scripts/ons_geo_cache_refresh.py` workflow is still a
whole-cache-oriented operator path:

- source acquisition is sequential rather than parallel
- raw acquisition and SQLite ingest are coupled in one long-running loop
- the workflow assumes a broad refresh even when only one dataset changed or
  one source is paused by ONS
- operators do not yet have a cheap metadata-only way to confirm whether the
  local on-disk copy still matches the upstream release state

The next refactor should preserve the current normalization/freshness model but
change the refresh contract:

- parallelize raw acquisition only, with ingest remaining sequential
- make per-dataset refresh first-class so `ONSPD`, `NSPL`, `ONSUD`, `NSUL`,
  `CHD`, and `RGC` can be refreshed independently
- persist enough per-dataset remote/local provenance to validate on-disk
  holdings against upstream metadata without re-downloading the full artifact
- keep that provenance attached to raw artifacts so a later local-only rebuild
  from `static_file` inputs does not drop `resolvedSourceUrl`, retrieved-at, or
  equivalent upstream identifiers from the rebuilt cache index
- use source-appropriate validation signals such as CKAN package metadata,
  ArcGIS hosted-table metadata plus record counts, and HTTP validators like
  `ETag` / `Last-Modified` where available
- separate compact runtime state from bulky raw artifacts so optional mounted
  data roots such as `/Volumes/ExtSSD-Data/Data` can be searched or mirrored
  without disrupting the current local defaults; bulky caches like ONS raw
  downloads and boundary-run source folders should be able to live on those
  external roots when available while the active SQLite/index state remains
  local by default
