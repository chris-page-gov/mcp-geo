# Logging Usage and Error Rate Report (Last 30 Days)

- Generated (UTC): 2026-02-19T15:40:59.438299+00:00
- Window (UTC): 2026-01-20T15:40:59.438299+00:00 to 2026-02-19T15:40:59.438299+00:00
- Files scanned: 11 JSONL files under `logs/`
- Files with in-window records: 8
- In-window record coverage: 2026-01-20T22:05:02.056351+00:00 to 2026-02-19T15:40:34.590582+00:00

## Executive Summary

- Usage (requests): **2,569**
- Responses observed: **2,152**
- Error responses: **75**
- Error rate by responses: **3.49%**
- Error rate by requests: **2.92%**
- Peak usage day (requests): **2026-02-19** with **427** requests

## Usage by Client (initialize calls)

| Client | Initialize Calls | Share |
|---|---:|---:|
| codex-mcp-client | 237 | 56.8% |
| claude-ai | 113 | 27.1% |
| Visual Studio Code | 56 | 13.4% |
| openai-mcp | 10 | 2.4% |
| mcp-ui-mode-probe | 1 | 0.2% |

## Usage by Method

| Method | Count | Share |
|---|---:|---:|
| tools/call | 667 | 26.0% |
| tools/list | 426 | 16.6% |
| initialize | 418 | 16.3% |
| notifications/initialized | 371 | 14.4% |
| resources/list | 302 | 11.8% |
| resources/templates/list | 207 | 8.1% |
| prompts/list | 120 | 4.7% |
| resources/read | 47 | 1.8% |
| GET | 4 | 0.2% |
| notifications/cancelled | 3 | 0.1% |
| shutdown | 2 | 0.1% |
| exit | 2 | 0.1% |

## Top Tool Usage (`tools/call`)

| Tool | Calls | Share |
|---|---:|---:|
| admin_lookup_find_by_name | 94 | 14.1% |
| nomis_datasets | 76 | 11.4% |
| nomis_query | 53 | 7.9% |
| os_places_by_postcode | 50 | 7.5% |
| admin_lookup_area_geometry | 45 | 6.7% |
| os_names_find | 43 | 6.4% |
| os_features_query | 32 | 4.8% |
| admin_lookup_containing_areas | 31 | 4.6% |
| os_maps_render | 28 | 4.2% |
| os_apps_render_geography_selector | 25 | 3.7% |
| os_places_search | 23 | 3.4% |
| ons_search_query | 17 | 2.5% |
| os_vector_tiles_descriptor | 13 | 1.9% |
| os_mcp_stats_routing | 12 | 1.8% |
| os_apps_log_event | 12 | 1.8% |
| os_apps_render_ui_probe | 10 | 1.5% |
| os_mcp_descriptor | 9 | 1.3% |
| os_places_within | 9 | 1.3% |
| os_apps_render_boundary_explorer | 9 | 1.3% |
| os_apps_render_statistics_dashboard | 8 | 1.2% |
| os_places_nearest | 7 | 1.0% |
| os_names_nearest | 6 | 0.9% |
| os_poi_search | 6 | 0.9% |
| ons_codes_list | 5 | 0.7% |
| ons_codes_options | 5 | 0.7% |

## Error Breakdown

| Error Code | Count | Share of Errors | Sample Message |
|---|---:|---:|---|
| OS_API_ERROR | 26 | 34.7% | OS API error: {
  "error" : {
    "statuscode" : 400,
    "message" : "Point must be a comma separated coordinate in British National Grid projection to 2 decimal places or less. Requested point was - |
| NOMIS_QUERY_ERROR | 24 | 32.0% | Query is incomplete |
| UPSTREAM_INVALID_RESPONSE | 7 | 9.3% | NOMIS API returned invalid JSON. |
| UPSTREAM_CONNECT_ERROR | 6 | 8.0% | HTTPSConnectionPool(host='www.nomisweb.co.uk', port=443): Read timed out. (read timeout=5) |
| ADMIN_LOOKUP_API_ERROR | 4 | 5.3% | Admin lookup live query failed. |
| INVALID_INPUT | 3 | 4.0% | Invalid UK postcode |
| BOUNDARY_CACHE_DISABLED | 2 | 2.7% | Boundary cache is not enabled. |
| BOUNDARY_CACHE_ERROR | 1 | 1.3% | Boundary cache search failed. |
| INTEGRATION_ERROR | 1 | 1.3% | Expecting value: line 1 column 1 (char 0) |
| NOMIS_API_ERROR | 1 | 1.3% | NOMIS API error: "{ \"error\" : \"Failed to convert Generic SDMX to JSON\" }" |

## High-Volume Method Error Rates (>=10 responses)

| Method/Tool | Responses | Errors | Error Rate |
|---|---:|---:|---:|
| tools/call::nomis_query | 53 | 25 | 47.17% |
| tools/call::os_features_query | 29 | 10 | 34.48% |
| tools/call::os_names_find | 42 | 5 | 11.90% |
| tools/call::nomis_datasets | 72 | 7 | 9.72% |
| tools/call::os_places_search | 23 | 2 | 8.70% |
| tools/call::ons_search_query | 17 | 1 | 5.88% |
| resources/read | 46 | 2 | 4.35% |
| tools/call::admin_lookup_area_geometry | 45 | 1 | 2.22% |
| tools/call::admin_lookup_find_by_name | 91 | 2 | 2.20% |
| tools/call::os_places_by_postcode | 49 | 1 | 2.04% |
| tools/list | 425 | 2 | 0.47% |
| initialize | 385 | 0 | 0.00% |
| resources/list | 302 | 0 | 0.00% |
| resources/templates/list | 207 | 0 | 0.00% |
| prompts/list | 120 | 0 | 0.00% |
| tools/call::admin_lookup_containing_areas | 30 | 0 | 0.00% |
| tools/call::os_maps_render | 28 | 0 | 0.00% |
| tools/call::os_apps_render_geography_selector | 25 | 0 | 0.00% |
| tools/call::os_vector_tiles_descriptor | 13 | 0 | 0.00% |
| tools/call::os_apps_log_event | 12 | 0 | 0.00% |
| tools/call::os_apps_render_ui_probe | 10 | 0 | 0.00% |
| tools/call::os_mcp_stats_routing | 10 | 0 | 0.00% |

## Daily Usage and Error Trend

| Date (UTC) | Requests | Responses | Errors | Error Rate (Responses) |
|---|---:|---:|---:|---:|
| 2026-01-20 | 4 | 8 | 0 | 0.00% |
| 2026-01-21 | 113 | 102 | 6 | 5.88% |
| 2026-01-22 | 28 | 26 | 2 | 7.69% |
| 2026-01-23 | 0 | 0 | 0 | 0.00% |
| 2026-01-24 | 65 | 60 | 1 | 1.67% |
| 2026-01-25 | 0 | 0 | 0 | 0.00% |
| 2026-01-26 | 0 | 0 | 0 | 0.00% |
| 2026-01-27 | 0 | 0 | 0 | 0.00% |
| 2026-01-28 | 12 | 11 | 1 | 9.09% |
| 2026-01-29 | 15 | 14 | 2 | 14.29% |
| 2026-01-30 | 8 | 6 | 0 | 0.00% |
| 2026-01-31 | 0 | 0 | 0 | 0.00% |
| 2026-02-01 | 29 | 24 | 1 | 4.17% |
| 2026-02-02 | 39 | 34 | 4 | 11.76% |
| 2026-02-03 | 29 | 24 | 3 | 12.50% |
| 2026-02-04 | 56 | 47 | 3 | 6.38% |
| 2026-02-05 | 72 | 64 | 4 | 6.25% |
| 2026-02-06 | 221 | 200 | 28 | 14.00% |
| 2026-02-07 | 64 | 58 | 1 | 1.72% |
| 2026-02-08 | 61 | 46 | 0 | 0.00% |
| 2026-02-09 | 30 | 25 | 0 | 0.00% |
| 2026-02-10 | 67 | 58 | 8 | 13.79% |
| 2026-02-11 | 62 | 54 | 0 | 0.00% |
| 2026-02-12 | 38 | 34 | 0 | 0.00% |
| 2026-02-13 | 77 | 63 | 1 | 1.59% |
| 2026-02-14 | 286 | 251 | 1 | 0.40% |
| 2026-02-15 | 23 | 18 | 0 | 0.00% |
| 2026-02-16 | 100 | 74 | 0 | 0.00% |
| 2026-02-17 | 272 | 216 | 0 | 0.00% |
| 2026-02-18 | 371 | 295 | 1 | 0.34% |
| 2026-02-19 | 427 | 340 | 8 | 2.35% |

## Source Files (In-Window Records)

| File | Records in Window | Requests | Responses | Errors | First Event (UTC) | Last Event (UTC) |
|---|---:|---:|---:|---:|---|---|
| `logs/_trace_proxy_smoke.jsonl` | 8 | 4 | 3 | 0 | 2026-02-10T08:59:32.094928+00:00 | 2026-02-10T08:59:32.326590+00:00 |
| `logs/claude-code-trace.jsonl` | 1,144 | 576 | 513 | 42 | 2026-01-20T23:46:27.993713+00:00 | 2026-02-06T13:40:13.022714+00:00 |
| `logs/claude-trace.jsonl` | 3,757 | 626 | 567 | 33 | 2026-02-06T13:53:04.703561+00:00 | 2026-02-19T15:29:59.648926+00:00 |
| `logs/codex-trace-pre-missing-build.jsonl` | 393 | 12 | 8 | 0 | 2026-02-14T17:05:11.098447+00:00 | 2026-02-14T17:13:36.550387+00:00 |
| `logs/codex-trace.jsonl` | 2,427 | 1,098 | 865 | 0 | 2026-02-14T17:14:22.324382+00:00 | 2026-02-19T15:38:43.136903+00:00 |
| `logs/mcp-http-trace.jsonl` | 35 | 18 | 17 | 0 | 2026-01-24T10:20:39.163593+00:00 | 2026-01-24T11:15:34.383553+00:00 |
| `logs/mcp-trace.jsonl` | 2 | 0 | 2 | 0 | 2026-01-20T22:05:02.056351+00:00 | 2026-01-20T22:05:02.056527+00:00 |
| `logs/vscode-mcp-trace.jsonl` | 780 | 235 | 177 | 0 | 2026-02-08T18:58:09.051921+00:00 | 2026-02-19T15:40:34.590582+00:00 |

## Notes and Assumptions

- This report is based on trace files currently present under `logs/`; it is not a centralized production log export.
- Error classification counts a response as error when JSON-RPC `error` is present, or MCP payload sets `isError=true`, or HTTP status is >= 400.
- Method-level error rates depend on matching request/response IDs within each file and may undercount when IDs are absent or reused across disconnected sessions.
- Stderr diagnostic lines are included in source coverage but do not count as requests/responses unless they carry request/response direction metadata.
