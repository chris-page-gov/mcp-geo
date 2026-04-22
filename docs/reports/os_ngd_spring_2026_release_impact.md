# OS NGD Spring 2026 Release Impact

Date: 2026-04-22

## Sources Checked

- [OS NGD product page](https://www.ordnancesurvey.co.uk/products/os-ngd)
- [OS NGD What's New](https://docs.os.uk/osngd/os-ngd-news/whats-new)
- [OS NGD API Features: data available](https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-features/what-data-is-available)
- [Postcode Unit Area](https://docs.os.uk/osngd/data-structure/administrative-and-statistical-units/gb-postcodes/postcode-unit-area)
- [Postcode Unit Point](https://docs.os.uk/osngd/data-structure/administrative-and-statistical-units/gb-postcodes/postcode-unit-point)
- [Functional Areas](https://docs.os.uk/osngd/data-structure/administrative-and-statistical-units/functional-areas)
- [NI Postcodes](https://docs.os.uk/osngd/data-structure/administrative-and-statistical-units/ni-postcodes)
- [OS API authentication](https://docs.os.uk/os-apis/core-concepts/authentication)

## Release Summary

The Spring 2026 OS NGD release adds GB postcode geometry to OS NGD API Features:
Postcode Unit Area and Postcode Unit Point are now part of the API Features data
availability table. The area feature type represents notional extents for
addresses sharing a postcode unit, derived from georeferenced Royal Mail PAF
delivery addresses. The point feature type represents a postcode as a point
calculated from average positions of addresses sharing the postcode.

Note: the individual GB postcode feature-type pages still carry early-insight
warnings from the pre-release period, while the What's New and API Features
availability pages present the Spring 2026 release as launched. MCP-Geo therefore
uses runtime `/collections` discovery and latest-version resolution so it can
adapt to the live API state instead of assuming a hard-coded version exists.

The release also adds new Functional Areas, initially retail-area feature types,
but the Functional Areas page states those data are available through OS
Select+Build and cannot be accessed through OS NGD API Features or OS NGD API
Tiles. NI Postcodes are similarly Select+Build-only for API purposes. They are
therefore not wired into the live API Features inventory in this change.

Transport impact is lower risk: OS now documents Bus Lane and Cycle Lane in the
Transport Network API Features table, and the What's New page states GB-wide
bus and cycle lane coverage was achieved by March 2026.

## MCP-Geo Impact

The existing `os_features.collections` and `os_features.query` path was already
mostly release-compliant because it discovers `/collections`, resolves latest
version suffixes by base collection id, and avoids hard-coding a single current
version. The misalignment was discoverability: friendly aliases, map inventory
layers, overlay metadata, and layer catalog entries did not include the new
postcode geometry and lane feature types.

Updated code paths:

- `tools/os_features.py`: added aliases for GB Postcode Unit Area, GB Postcode
  Unit Point, Bus Lane, and Cycle Lane collection bases.
- `tools/os_map.py`: added requested inventory layers
  `postcode_unit_areas`, `postcode_unit_points`, `bus_lanes`, and `cycle_lanes`,
  all resolved to the latest live collection version when the OS API exposes
  one.
- `tools/os_maps.py`: added overlay normalization for the same inventory layers.
- `resources/layers_catalog.json`: added catalog entries and caveats for the
  new layers.
- `tools/os_mcp.py`: route-query detection now recommends the new collection
  bases for postcode geometry and cycle/bus lane prompts.

## Authentication And Permission Check

OS still documents API-key authentication with a `key` query parameter or `key`
header, plus OAuth2 client credentials where a Project API Key and Project API
Secret are exchanged for short-lived bearer tokens. I found no evidence of a
Spring 2026-specific auth model replacing those methods.

MCP-Geo now supports all documented request-carrier modes:

- `OS_API_AUTH_MODE=query`: default, sends `OS_API_KEY` as query parameter.
- `OS_API_AUTH_MODE=header`: sends `OS_API_KEY` as the `key` header.
- `OS_API_AUTH_MODE=bearer`: sends `OS_API_ACCESS_TOKEN` as a bearer token.

MCP-Geo does not perform the OS OAuth2 token exchange itself. Deployments using
bearer mode must mint and refresh `OS_API_ACCESS_TOKEN` out of band. The OS Data
Hub project still needs the relevant product/API entitlement: GB postcode
geometry requires OS NGD API Features access, while Functional Areas and NI
Postcodes require OS Select+Build access instead of API Features.

## Compliance Status

- GB postcode unit areas and points: now exposed as API Features aliases, map
  inventory layers, render overlays, and catalog entries.
- Bus lanes and cycle lanes: now exposed as inventory/render/catalog layers.
- Functional Areas: documented as useful Spring 2026 data, but deliberately not
  mapped to API Features because OS says the supply mechanism is Select+Build
  only.
- NI Postcodes: documented as useful for UK coverage, but deliberately not
  mapped to API Features because OS says the supply mechanism is Select+Build
  only.
- Live API validation was run on 2026-04-22 with
  `MCP_GEO_RUN_LIVE_OS_NGD=1 OS_API_KEY_FILE=/Users/crpage/.secrets/os_api_key`
  against `tests/test_os_ngd_spring_2026_live.py` (`3 passed`). The run
  confirmed:
  - `/collections` exposes the existing bases used by MCP-Geo
    (`bld-fts-buildingpart`, `trn-ntwk-roadlink`, `trn-ntwk-pathlink`) and the
    Spring 2026 bases added here (`asu-gbpcd-postcodeunitarea`,
    `asu-gbpcd-postcodeunitpoint`, `trn-ntwk-buslane`, `trn-ntwk-cyclelane`).
  - `os_features.query` can resolve and call each existing and Spring 2026
    collection base through the live OS NGD API Features item endpoint.
  - Documented API-key header auth reaches the live `/collections` endpoint.

The live API also confirmed that OS NGD API Features item endpoints do not
accept an upstream `resultType` query parameter. MCP-Geo's `resultType` remains
an MCP response-shaping option; it is not forwarded to OS.
