# LandIS LEACS Access Probe - 2026-05-13

## Summary

This probe checked whether the LandIS LEACS data needed for wider pipe-risk coverage can be downloaded from the available public and authenticated routes.

Result: LEACS is not currently available as a downloadable payload through the routes available to MCP-Geo. Public metadata exists, but it points only to generic LandIS website HTML. The authenticated LandIS ArcGIS portal was reachable after a fresh Atlas sign-in, but direct searches and a full catalog/service/table field scan found no LEACS, corrosivity, shrink-swell, `CORR_FE`, `CORR_ZN`, or `SHRINK_SWELL` item/table/field.

The machine-readable probe record is:

`research/landis-data-source/landis_leacs_access_probe_2026-05-13.json`

## Routes Checked

### Public CKAN/data.gov.uk

Checked live CKAN backend package metadata:

- `https://ckan.publishing.service.gov.uk/api/3/action/package_show?id=soil-series-leacs1`
- `https://ckan.publishing.service.gov.uk/api/3/action/package_show?id=leacs-by-soil-association1`

Findings:

- `Soil Series LEACS`
  - GUID: `CU-LANDIS-SOILSERIESLEACS`
  - Notes: shrink-swell and corrosivity of soil to Fe and Zn
  - `isopen`: `false`
  - Resource count: `1`
  - Only resource: `LandIS website`, format `HTML`, URL `http://www.landis.org.uk/`

- `LEACS by Soil Association`
  - GUID: `CU-LANDIS-MAPUNIT_LEACS`
  - Notes: dominant shrink-swell and corrosivity class by soil association
  - `isopen`: `false`
  - Resource count: `1`
  - Only resource: `LandIS website`, format `HTML`, URL `http://www.landis.org.uk/`

Both packages carry Cranfield-specific licensing/access constraints rather than a direct open data file.

### Archived Public Release

The existing full release archive already captured the public LEACS pages and package pages:

- `Series Leacs`
  - URL: `https://www.landis.org.uk/data/ssleacs.cfm`
  - Archive path: `[EXTSSD_DATA_ROOT]/landis_full_release_archive_2026-04-05/public_site/Series_Leacs/page.html`
  - SHA-256: `4fc57b8086f717c95433d007ddcd41aa738f2dc6fc6e694f2ad8db2a1cc1c52b`

- `Leacs`
  - URL: `https://www.landis.org.uk/services/leacs.cfm`
  - Archive path: `[EXTSSD_DATA_ROOT]/landis_full_release_archive_2026-04-05/public_site/Leacs/page.html`
  - SHA-256: `e1163fd7de8dec227b2ab83c905dccf70174fc32242d23a41438e192bf7e0229`

- `LEACS by Soil Association`
  - Archive path: `[EXTSSD_DATA_ROOT]/landis_full_release_archive_2026-04-05/data_gov/leacs-by-soil-association1/package_page.html`
  - SHA-256: `c0e3bb11e70c3caff07573f86ce0fa3e13afd9749d6fa4e6ffd25d90f84f38c1`

- `Soil Series LEACS`
  - Archive path: `[EXTSSD_DATA_ROOT]/landis_full_release_archive_2026-04-05/data_gov/soil-series-leacs1/package_page.html`
  - SHA-256: `036e2f455266c1e0a678f5bca7ac2fd2970f22b0368bcdeb50bf19988cb3cfb2`

These archived pages are useful provenance, but they are not the LEACS data table.

### Authenticated LandIS ArcGIS Portal

The user signed into the LandIS portal in ChatGPT Atlas with an authenticated portal account. The existing repository helper discovered a fresh ArcGIS token from Atlas history for live queries only. The token was not printed or persisted.

Direct protected portal searches returned zero results for:

- `LEACS`
- `SOILSERIESLEACS`
- `MAPUNIT_LEACS`
- `SOIL_SERIES_LEACS`
- `corrosivity shrink`
- `shrink swell`
- `CORR_FE`
- `SHRINK_SWELL`

A deeper scan then enumerated `108` accessible protected portal catalog items and inspected Feature Service metadata, layers, tables, field names, and field aliases for:

- `leacs`
- `corros`
- `shrink`
- `swell`
- `corr_fe`
- `corr_zn`
- `shrink_swell`
- `soilseriesleacs`
- `mapunit_leacs`

Matches: `0`.

The protected portal does expose the base `SOILSERIES` table:

- Item ID: `5f54467246a1484f8e17c1b8ba2218d8`
- Service URL: `https://services-eu1.arcgis.com/BsCa1SurMySYByZ3/arcgis/rest/services/SOILSERIES/FeatureServer`
- Table: `Soil Series`
- Archived record count: `1343`
- Fields: `OBJECTID`, `SERIES`, `SERIESNAME`, `SUBGROUP`, `MODDEFN`, `STATE`

That table does not contain LEACS attributes.

## Current Warehouse Implication

The current local `landis.pipe_risk_polygons` table remains the Warwickshire validation layer:

- Dataset version: `2026-warwickshire-validation`
- Feature count: `1192`
- Nottinghamshire intersections: `0`
- Only local pipe-risk file found: `[EXTSSD_DATA_ROOT]/landis_warwickshire_validation/official/landis_official_pipe_risk_warwickshire.geojson`

## Future Decision Rules

Treat LEACS as not available for automated download unless one of these changes:

- A protected portal item/table appears with LEACS, corrosivity, shrink-swell, `CORR_FE`, `CORR_ZN`, or `SHRINK_SWELL` in its title, metadata, table name, or fields.
- A CKAN/data.gov.uk LEACS package gains a non-HTML resource such as CSV, XLSX, GeoJSON, GDB, SHP, or an ArcGIS service URL.
- Cranfield supplies a licensed extract directly.

If a licensed extract is supplied, expected useful fields are:

- `SHRINK_SWELL`
- `CORR_FE`
- `CORR_ZN`
- a join key to soil series, soil association, or NATMAP map unit

Until then, any Nottinghamshire pipe-risk expansion should be labelled as a proxy model, not LEACS-derived pipe risk.
