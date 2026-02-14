# ChatGPT MCP Setup (Lean Startup)

Use this setup when connecting MCP Geo from ChatGPT or similar MCP hosts.

## 1) Keep initialize lightweight

Set startup discovery to the curated `starter` toolset:

- `MCP_TOOLS_DEFAULT_TOOLSET=starter`

This avoids large `tools/list` payloads during initialize and keeps early
sessions responsive.

## 2) Canonical map path

Start all map interactions with `os_maps.render` (static baseline). Only move
to widget tools (`os_apps.render_*`) after the host confirms MCP-Apps UI
support.

Fallback order:

1. `map_card`
2. `overlay_bundle`
3. `export_handoff`

See:
- `docs/spec_package/06_api_contracts.md`
- `docs/spec_package/06a_map_delivery_fallback_contracts.md`
- `docs/map_delivery_support_matrix.md`

## 3) Post-init discovery expansion (opt-in)

After the first successful initialize/list round, explicitly expand scope:

```json
{"toolset":"maps_tiles"}
```

or:

```json
{"includeToolsets":["maps_tiles","apps_ui","admin_boundaries"]}
```

Keep heavy discovery as a deliberate, post-init step.
