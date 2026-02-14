# Map Delivery Fallback Contracts Appendix

This appendix defines stable compatibility skeletons for map delivery across
full-UI, partial-UI, and no-UI MCP hosts.

## Contract ordering

Map responses should degrade in this fixed order:

1. Full UI (`os_apps.render_*` + `ui://` resource)
2. `map_card`
3. `overlay_bundle`
4. `export_handoff`

## `map_card`

Use when the host cannot render MCP-Apps widgets but can display static map
content and metadata.

Required fields:

- `type` (`"map_card"`)
- `title`
- `render.imageUrl` (or equivalent URL from `os_maps.render`)
- `bbox`
- `guidance.widgetUnsupported` (`true` for non-UI hosts)

Optional fields:

- `zoom`
- `legend`
- `actions` (for retry/open/download controls)
- `accessibility.altText`

## `overlay_bundle`

Use to ship map overlays as deterministic GeoJSON-like payloads, independent of
host UI capability.

Required fields:

- `type` (`"overlay_bundle"`)
- `layers[]` with `id`, `name`, `kind`, `featureCollection`
- `source` metadata with provenance

Optional fields:

- `styleHints`
- `selection`
- `nextPageToken` by layer

## `export_handoff`

Use when payloads exceed practical inline limits or a workflow needs explicit
handoff to resource-backed artifacts.

Required fields:

- `type` (`"export_handoff"`)
- `resourceUri`
- `format` (`json`, `geojson`, `gpkg`, `pmtiles`, `mbtiles`, etc.)
- `generatedAt`
- `hash`

Optional fields:

- `expiresAt`
- `sizeBytes`
- `compression`

## Compatibility guidance fields

Non-UI fallback payloads should expose explicit, stable guidance:

- `widgetUnsupported`: boolean
- `widgetUnsupportedReason`: machine-readable reason code
- `degradationMode`: `full_ui`, `partial_ui`, or `no_ui`
- `preferredNextTools[]`: deterministic tool-call order for host recovery

## Author conformance checklist

- Keep `map_card`, `overlay_bundle`, and `export_handoff` keys stable.
- Return the same guidance keys for STDIO and HTTP transports.
- Include provenance metadata for every export/resource URI.
- Keep fallback payloads deterministic for identical inputs.
- Ensure examples in docs/tutorials match runtime payload keys.
