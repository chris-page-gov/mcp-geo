# Geography Extension Contract

MCP-Geo supports overlapping UK geography concepts across ONS cache lookups,
admin boundaries, interactive widgets, statistics routing, STDIO elicitation,
and export workflows. New geography levels or display-name overlays must be
added as a cross-surface component, not as one local fix.

## Registry First

Add or change geography-level semantics in `server/geography_levels.py` first.
That registry owns:

- public selector key and label
- public ONS area level, where applicable
- normalized geography key and ONS cache column
- admin boundary level and alias normalisation
- keyword patterns for routing and admin inference
- GSS code-prefix inference
- boundary-cache search priority
- stats-comparison eligibility
- NOMIS geography-type matchers, when dataset-specific lookup is possible
- display-name policy, when display labels differ from official ONS/RGC names

Callers should consume derived helpers from that registry instead of adding
parallel alias maps or hard-coded level lists.

## Parish / PARNCP

Public API level: `PARISH`.

Source fields remain source-specific:

- `PARNCP25CD`
- `PARNCP25NM`
- `PARNCP25NW`

`PARISH` covers civil parishes, Welsh communities, and non-civil-parished
areas. Current generalized live boundary fallback is `PARNCP_MAY_2025_EW_BGC`.

Parish support must be present in:

- ONS normalized geographies and `ons_geo_uprn_index`
- `ons_geo.area_summary`
- `admin_lookup.find_by_name`, `search_cache`, `area_geometry`, and containing-area paths
- `os_mcp.route_query` and `os_mcp.stats_routing`
- STDIO elicitation choices
- `os_apps.render_geography_selector` and `ui/geography_selector.html`
- selector-driven exports in `os_map.export`
- workflow resources and user-facing docs

## Alternate-Language Names

When a geography source carries alternate official-language names, treat those
fields as searchable aliases and response metadata, not as passive source-only
columns. For Welsh communities in the PARNCP source, `PARNCP25NW` should be
searchable alongside `PARNCP25NM` and returned as `nameWelsh` or equivalent
metadata without replacing the English/current `name`.

Future geography additions should identify source-specific alternate-name
fields during registry design, then check live lookup, cache search, normalized
geographies, display-name overlays, exports, and docs for consistent behavior.

## MSOA Display Names

House of Commons Library MSOA names are display labels only. They must not
replace the official ONS/RGC name.

Keep these fields distinct:

- `name` / `currentName`: official ONS/RGC label
- `displayName`: House of Commons Library display label
- `displayNameWelsh`: Welsh display label, when supplied
- `displayNameSource`: provenance including source, version, publication date,
  and licence

When both names differ, responses should include a `namePolicy` note explaining
that display labels are non-official disambiguating labels.

## Required Review Sweep

For any geography-level or display-name change, review these sibling surfaces:

- cache schema, migrations, refresh ingest, semantic extraction
- direct cache readers; use `ONSGeoCache.connect(...)` or `ensure_schema(...)`
  before selecting migration-added columns
- code-prefix inference and alias normalisation
- cache lookup, live fallback, and boundary geometry paths
- HTTP tool schemas and descriptions
- STDIO schemas, elicitation, sanitized names, and fallback payloads
- MCP-Apps widget configuration and embedded HTML defaults
- route-query intent detection and workflow resources
- export selectors, CSV fields, and selected-by audit columns
- OWASP MCP manifest/risk inventory, when schemas or descriptions change
- docs, examples, and changelog fragments

Regression coverage should include the reported path plus at least one sibling
transport or runtime path. For parish and MSOA display names, minimum coverage is:

- registry alias/code inference
- ONS normalized lookup or area summary
- admin lookup cache/live behavior
- route query or stats routing
- STDIO or widget contract
- export selector or workflow resource when relevant
