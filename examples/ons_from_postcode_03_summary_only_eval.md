# Evaluation Trace: Summary-Only OA Follow-Up

Source family: [ons_from_postcode.md](/Users/crpage/repos/mcp-geo/examples/ons_from_postcode.md)
Date: 2026-04-11

## Goal

Assert that MCP-Geo now supports the "What do you know about that OA" follow-up
without forcing the client into a large raw `os_map.inventory` call.

## Prompt

`What do you know about that OA`

## Expected Tooling

Primary tool:

- `ons_geo.area_summary`

Expected shape:

- reuse prior OA/LSOA/MSOA/postcode/UPRN context when the host preserves it
- otherwise pass the explicit area code, postcode, or UPRN to
  `ons_geo.area_summary`
- keep `inventoryResponseMode` at `summary` or `counts`

## Forbidden / Regressive Patterns

- `os_map.inventory` with default or explicit `responseMode=full`
- `admin_lookup.find_by_name` against an already-known area code
- `ons_geo.cache_status` as part of the user-answering path

## Pass Criteria

- the client can stay in-band without a large tool-result file handoff
- the answer includes compact area identity, hierarchy, and counts
- deeper NOMIS follow-up is offered via curated `profileDatasets`
- raw inventory detail is only fetched if the user later asks for it
