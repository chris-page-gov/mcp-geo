# MCP Geo Skills

This document describes how to use the MCP Geo server for UK geospatial, ONS,
and NOMIS statistics workflows. It is intended for MCP clients and agents as a
quick, reliable guide to tool selection.

## What This Server Provides

- OS Places address lookups (postcodes, UPRNs, nearest addresses).
- OS Names gazetteer searches for named features.
- OS NGD feature queries for topographic datasets.
- ONS dataset discovery and observation queries (live dataset search).
- NOMIS labour/census statistics (deep local geographies).
- Administrative area lookups from live ONS geography (ArcGIS).
- MCP-Apps widgets for interactive selection and inspection.
- Tool search metadata for large tool catalogs.

## Start Here: os_mcp.route_query

For any natural language request, call `os_mcp.route_query` first. It returns
the intent, a recommended tool, and suggested workflow steps.

Example:
```
{ "tool": "os_mcp.route_query", "query": "Find Westminster ward boundaries" }
```

Use `recommended_tool`, `recommended_parameters`, and `workflow_steps` to pick
the next tool calls. When the intent is unclear, fall back to `os_mcp.descriptor`
or `/tools/search`.

If you need to understand whether a statistics query will route to ONS or NOMIS,
use `os_mcp.stats_routing`.

## Quick Tool Selection

Addresses and postcodes:
- Use `os_places.search` for free text address search.
- Use `os_places.by_postcode` for UPRNs and addresses by postcode.
- Use `os_places.by_uprn` for a single address record.

Named places and features:
- Use `os_names.find` to search named features.
- Use `os_names.nearest` for nearest named features to a point.

Administrative areas:
- Use `admin_lookup.find_by_name` to locate areas by name (pass `level`/`levels` to reduce noisy matches).
- Use `admin_lookup.containing_areas` to find which areas contain a point.
- Use `admin_lookup.reverse_hierarchy` for ancestor chains.

Statistics:
- Use `ons_select.search` to rank ONS datasets with explainable scoring.
- Use `ons_search.query` for raw live ONS dataset search.
- Use `ons_data.query` to fetch live ONS observations.
- Use `ons_data.dimensions` to list ONS dimension ids and options.
- Use `nomis.datasets` to discover NOMIS datasets for labour/census.
- Use `nomis.query` for NOMIS observations (JSON-stat/SDMX).

Tips for admin lookups:
- For towns that collide with larger areas (e.g., "Warwick" vs "North Warwickshire"), pass `level: "WARD"` or `levels: ["WARD"]`.
- Use `match: "starts_with"` or `match: "exact"` when you know the prefix.
- `admin_lookup.search_cache` accepts `fallbackLive` to automatically use live ArcGIS when cache is disabled.

OS NGD features and links:
- Use `os_features.query` for feature searches by collection + bbox.
- Use `os_linked_ids.get` to resolve UPRN/USRN/TOID relationships.

Route planning:
- Use `os_route.descriptor` to check graph readiness, supported profiles, and stop limits.
- Use `os_route.get` for deterministic routing with `stops`, optional `via`, `profile`,
  and `constraints`.
- Use `os_apps.render_route_planner` only when an interactive MCP-Apps host is available;
  it is the companion UI for `os_route.get`, not the authoritative solver.
- For free-text prompts such as "best emergency route from ... to ... avoid ... if
  possible", start with `os_mcp.route_query` and then follow its
  `recommended_parameters`.

Maps and tiles:
- Use `os_maps.render` for static map image URLs (served by MCP Geo proxy).
- Use `os_vector_tiles.descriptor` for vector tile style metadata.

## MCP-Apps Widgets

Interactive UI widgets are exposed as MCP resources. Use the `os_apps.*` tools
to open them inside MCP-Apps compatible hosts.

- `os_apps.render_geography_selector` -> `ui://mcp-geo/geography-selector`
- `os_apps.render_statistics_dashboard` -> `ui://mcp-geo/statistics-dashboard`
- `os_apps.render_feature_inspector` -> `ui://mcp-geo/feature-inspector`
- `os_apps.render_route_planner` -> `ui://mcp-geo/route-planner`

UI tools are linked via tool metadata (`_meta.ui.resourceUri`). Hosts should load
the UI resource from `/resources/list` or `/resources/read` and use tool results
for status/config/instructions. The route planner widget accepts the same
`stops` / `via` / `profile` / `constraints` shape as `os_route.get`, while
remaining backward-compatible with the legacy coordinate prefill fields.

## Tool Search

If you have a large tool catalog, use `/tools/search` (HTTP) or `tools/search`
(stdio JSON-RPC) to discover tools by keyword or regex. The tool
`os_mcp.descriptor` returns tool search configuration and recommended defaults,
including `deferLoading` hints for MCP tool search integrations.

## Resources

Use `/resources/list` or `/resources/describe` to discover available resources.
Fetch content with `/resources/read` using `uri`. If a client cannot call the
protocol-level resource method directly, use the `os_resources.get` tool as the
portable fallback. Example:

- `skills://mcp-geo/getting-started` (this document)
- `ui://mcp-geo/geography-selector` (UI widget HTML)
- `resource://mcp-geo/boundary-manifest` (boundary dataset manifest)
- `resource://mcp-geo/boundary-latest-report` (latest pipeline report)
- `resource://mcp-geo/ons-catalog` (ONS dataset catalog index)
- `resource://mcp-geo/os-catalog` (Ordnance Survey API and downloads catalog index)
- `resource://mcp-geo/layers-catalog` (human-friendly layer catalog for OS NGD collections)

## Error Model

Errors follow this shape:
```
{ "isError": true, "code": "<CODE>", "message": "..." }
```

Common codes: `INVALID_INPUT`, `UNKNOWN_TOOL`, `NO_API_KEY`,
`LIVE_DISABLED`, `OS_API_ERROR`, `ONS_API_ERROR`, `NOMIS_API_ERROR`,
`ADMIN_LOOKUP_API_ERROR`, `ROUTE_GRAPH_NOT_READY`, `NO_ROUTE`,
`AMBIGUOUS_STOP`, `STOP_NOT_FOUND`, `UPSTREAM_CONNECT_ERROR`, `RATE_LIMITED`.
