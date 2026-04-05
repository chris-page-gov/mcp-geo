# LandIS Release Surface Reconciliation

Date: 2026-04-05

## Objective

Check whether the completed authenticated LandIS portal mirror is the full
released LandIS data surface, or whether the current release still includes
additional public/open or separately distributed datasets outside the portal.

## Short Answer

No: the authenticated portal mirror is complete for the current ArcGIS portal
route, but it is not the full LandIS universe.

What we have completely mirrored:

- `106` portal items
- `33` feature-service datasets
- `73` non-feature items
- `0` manifest errors in the local archive

What remains outside that mirror:

- dataset families and services still listed on the public LandIS website but
  not present in the current portal inventory
- legacy data.gov metadata pages that still point to LandIS datasets and make
  clear that at least some products remain licensed rather than open bulk
  downloads

Machine-readable manifest generated from the same reconciliation pass:

- `research/landis-data-source/landis_release_reconciliation_2026-04-05.json`

Supplementary archive and no-touch verification outputs generated from the
same workstream:

- `research/landis-data-source/landis_full_release_manifest_2026-04-05.json`
- `/Volumes/ExtSSD-Data/Data/landis_full_release_archive_2026-04-05/full_release_manifest.json`
- `/Volumes/ExtSSD-Data/Data/landis_full_release_archive_2026-04-05/verification_manifest.json`

The authenticated portal mirror and the supplementary public/data.gov archive
together now give a complete locally mirrored release surface for the routes
we could validate on 2026-04-05. The portal component remains the large
authenticated archive (`106` items, `0` errors), while the supplementary
archive covers the non-portal release slice (`13` public-site items, `59`
`data.gov.uk` packages, `165` verification checks, `0` failures).

## Source Surfaces Checked

### 1. Authenticated ArcGIS portal route

Primary source already captured in the repo:

- `docs/reports/landis_portal_inventory_2026-04-04.md`
- `research/landis-data-source/landis_portal_inventory_2026-04-04.json`

This route currently exposes `33` machine-readable feature services.

### 2. Public LandIS website dataset menus

Official public pages checked:

- <https://www.landis.org.uk/data/datafamilies.cfm>
- <https://www.landis.org.uk/soilscapes/>

These pages are important because they still advertise the broader LandIS data
and service catalogue, not just the ArcGIS portal slice.

### 3. Legacy data.gov publisher metadata

Official metadata page checked:

- <https://www.data.gov.uk/dataset/ea1442bf-ba77-42cc-80e7-2ea339ccb28a/natmap-national-soil-map1>

This confirms that at least some LandIS datasets are still described through
government metadata with a non-open licence and a download link that points
back to the LandIS website rather than to a public bulk file.

## What The Portal Mirror Clearly Covers

The mirrored portal inventory contains the current ArcGIS-hosted release set
for these main families:

- NATMAP polygon products:
  `NationalSoilMap`, `NATMAPsoilscapes`, `NATMAP1000`, `NATMAP2000`,
  `NATMAP5000`, `NATMAPcarbon`, `NATMAPtopsoiltexture`,
  `NATMAPsubsoiltexture`, `NATMAPsubstratetexture`,
  `NATMAPavailablewater`, `NATMAPwrb2006`, `NATMAPregions`
- NATMAP support tables:
  `NATMAPassociations`, `NATMAPlegend`, `SOILSERIES`,
  `HORIZONfundamentals`, `HORIZONhydraulics`
- NSI family:
  `NSIsite`, `NSIprofile`, `NSItexture`, `NSItopsoil1`, `NSItopsoil2`,
  `NSIfeatures`, `NSImagnetic`
- AUGER family:
  `AUGERsite`, `AUGERprofile`
- Soil catalogue / reference coverage layers:
  `SoilCatalogue_100k`, `SoilCatalogue_25k`, `SoilCatalogue_50k`,
  `SoilCatalogue_63k`, `SoilCatalogue_FarmSurveys`,
  `SoilCatalogue_RabbitSurveys_sites`

This means the portal route is already strong for NATMAP, NSI, AUGER, and the
current ArcGIS-facing catalogue layers.

## What The Public LandIS Site Still Lists Outside The Portal Mirror

The public LandIS dataset and service menus list additional products and
services that do not currently appear in the captured `33`-service ArcGIS
inventory.

### Additional dataset families still listed publicly

From the public LandIS menus:

- `NATMAP HOST`
- `NATMAP wetness`
- `Series Hydrology`
- `Series Agronomy`
- `Series Pesticides`
- `Series Leacs`
- `Lowland Peat`

These are all visible on the public LandIS navigation, but they are not
present as titles in the current portal inventory snapshot.

### Additional public service surfaces still listed

The same public menus also still advertise:

- `Soilscapes Viewer`
- `Soils Guide`
- `Soil Alerts`
- `CatchIS`
- `Leacs`
- `Treefit`

These are important because some are user-facing data services rather than
simple dataset pages, and they may expose information or downloadable outputs
outside the current portal slice.

## Open Data Versus Publicly Listed But Licensed

The current release is not a single clean “all open data” release.

### Evidence that some portal items are intended as public/open data

Portal item metadata captured in the local inventory includes fields such as:

- `licenseInfo`: “Public Data, subject to the Open Licence”
- downloadable export formats such as `csv`, `shapefile`, `geojson`,
  `filegdb`, `geoPackage`, and `sqlite`

This is visible for current portal items such as `NATMAPsoilscapes`.

### Evidence that at least some LandIS datasets remain licensed

The `data.gov.uk` metadata page for `NATMAP - National Soil Map` states:

- publisher: Cranfield University
- licence: `Other Licence`
- licence text: use is subject to a specific licensing agreement, with pricing
  varying by user status

That means the broader LandIS release surface still includes datasets that are
described publicly but not simply available as anonymous open bulk downloads.

## Important Access Caveat

A spot check on 2026-04-05 against representative ArcGIS service URLs showed a
mixed result:

- public item pages are reachable anonymously
- service home pages are reachable anonymously
- direct ArcGIS REST JSON queries such as `?f=pjson` return `499 Token
  Required` for sampled services including `NATMAPsoilscapes` and `NSIsite`

So “publicly listed” and even “open-licensed in metadata” does not currently
mean “fully anonymous machine-queryable REST endpoint”.

For MCP-Geo this matters because:

- the portal archive remains valuable as a stable local mirror
- future ingestion should not assume anonymous REST access is sufficient
- some “open” portal items may still need token-backed extraction or portal
  download flow rather than direct unauthenticated API calls

## Approximate Size Findings For Missing Public-Menu Datasets

Where the public LandIS page is clearly dataset-like, the reconciliation
manifest now records a conservative approximate size estimate using current
portal analogues as the basis.

- `NATMAP HOST`: inferred `10^4` polygons, using current portal NATMAP polygon
  analogues (`NATMAPtopsoiltexture` `38,102`; `NationalSoilMap` `42,603`)
- `NATMAP wetness`: inferred `10^4` polygons, using the same NATMAP polygon
  analogue range
- `Series Hydrology`: inferred `10^3` rows, bounded by current portal
  `SOILSERIES` `1,343` and `HORIZONhydraulics` `6,591`
- `Series Agronomy`: inferred `10^3` rows, using `SOILSERIES` `1,343` as the
  nearest series-level analogue
- `Series Pesticides`: inferred `10^3` rows, using `SOILSERIES` `1,343` as the
  nearest series-level analogue
- `Series Leacs`: inferred `10^3` rows, using `SOILSERIES` `1,343` as the
  nearest series-level analogue
- `Lowland Peat`: still unknown from the currently probed public pages

These are explicit inferences, not direct source-record counts, and should be
treated as sizing guidance only until a machine-readable release surface is
confirmed.

## Conclusion

The authenticated portal archive is complete for the current portal route, but
it is not the full released LandIS surface.

Today the LandIS release landscape appears to have three layers:

1. ArcGIS portal datasets we have fully mirrored locally
2. Public LandIS website data families and services that are still advertised
   but are not present in the portal inventory
3. Legacy/licensed LandIS datasets described in `data.gov.uk` metadata that
   point back to LandIS/Cranfield access routes rather than offering a simple
   open bulk download

## Recommended Next Steps

1. Treat the current archive state as the reproducible baseline:
   - authenticated portal archive:
     `/Volumes/ExtSSD-Data/Data/landis_portal_archive_2026-04-04`
   - supplementary public/data.gov archive:
     `/Volumes/ExtSSD-Data/Data/landis_full_release_archive_2026-04-05`
   - completion check:
     `/Volumes/ExtSSD-Data/Data/landis_full_release_archive_2026-04-05/verification_manifest.json`
2. Probe every missing public-menu family (`HOST`, `wetness`, `Series
   Hydrology`, `Series Agronomy`, `Series Pesticides`, `Series Leacs`,
   `Lowland Peat`) to determine whether each one is:
   - present under a different title
   - a public viewer/service only
   - licensed but not open
   - deprecated but still linked
3. Turn the current reconciliation/archive outputs into the next machine-readable
   triage manifest so the question becomes “what should be surfaced through MCP
   next?” rather than “what is still missing from disk?”.
