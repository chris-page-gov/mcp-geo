# MCP Geo Skills

This document describes how to use the MCP Geo server for UK geospatial and ONS
statistics workflows. It is intended for MCP clients and agents as a quick,
reliable guide to tool selection.

## What This Server Provides

- OS Places address lookups (postcodes, UPRNs, nearest addresses).
- OS Names gazetteer searches for named features.
- OS NGD feature queries for topographic datasets.
- ONS dataset discovery and observation queries.
- Administrative area lookups from bundled boundary samples.
- MCP-Apps widgets for interactive selection and inspection.
- Tool search metadata for large tool catalogs.

## Quick Tool Selection

Addresses and postcodes:
- Use `os_places.search` for free text address search.
- Use `os_places.by_postcode` for UPRNs and addresses by postcode.
- Use `os_places.by_uprn` for a single address record.

Named places and features:
- Use `os_names.find` to search named features.
- Use `os_names.nearest` for nearest named features to a point.

Administrative areas:
- Use `admin_lookup.find_by_name` to locate areas by name.
- Use `admin_lookup.containing_areas` to find which areas contain a point.
- Use `admin_lookup.reverse_hierarchy` for ancestor chains.

ONS statistics:
- Use `ons_search.query` to discover datasets and dimensions.
- Use `ons_data.query` to fetch observations (sample or live mode).
- Use `ons_data.dimensions` to list dimension ids and options.

OS NGD features and links:
- Use `os_features.query` for feature searches by collection + bbox.
- Use `os_linked_ids.get` to resolve UPRN/USRN/TOID relationships.

Maps and tiles:
- Use `os_maps.render` for static map render descriptors.
- Use `os_vector_tiles.descriptor` for vector tile style metadata.

## MCP-Apps Widgets

Interactive UI widgets are exposed as MCP resources. Use the `os_apps.*` tools
to open them inside MCP-Apps compatible hosts.

- `os_apps.render_geography_selector` -> `ui://mcp-geo/geography-selector`
- `os_apps.render_statistics_dashboard` -> `ui://mcp-geo/statistics-dashboard`
- `os_apps.render_feature_inspector` -> `ui://mcp-geo/feature-inspector`
- `os_apps.render_route_planner` -> `ui://mcp-geo/route-planner`

Tool results include `uiResourceUris` so hosts can launch the right widget.

## Tool Search

If you have a large tool catalog, use `/tools/search` (HTTP) or `tools/search`
(stdio JSON-RPC) to discover tools by keyword or regex. The tool
`os_mcp.descriptor` returns tool search configuration and recommended defaults,
including `deferLoading` hints for MCP tool search integrations.

## Resources

Use `/resources/list` or `/resources/describe` to discover available datasets.
Fetch content with `/resources/get` using either `name` or `uri`. Example:

- `skills://mcp-geo/getting-started` (this document)
- `ui://mcp-geo/geography-selector` (UI widget HTML)
- `resource://mcp-geo/admin_boundaries` (sample boundary hierarchy)

## Error Model

Errors follow this shape:
```
{ "isError": true, "code": "<CODE>", "message": "..." }
```

Common codes: `INVALID_INPUT`, `UNKNOWN_TOOL`, `NO_API_KEY`,
`OS_API_ERROR`, `UPSTREAM_CONNECT_ERROR`, `RATE_LIMITED`.
