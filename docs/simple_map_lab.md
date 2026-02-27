# Simple Map Lab: Auth and PMTiles Trials

This note tracks a minimal map-delivery exploration path for the `codex/simple-map` branch.

## Goal

Deliver maps to clients with the smallest possible runtime surface:

1. Prefer browser session auth (`Authorization: Bearer ...`) when available.
2. Fall back to server-side `OS_API_KEY` when browser auth is absent.
3. Compare OS Vector proxy delivery against PMTiles browser rendering behavior.

## What changed

- Added browser-auth-first proxy auth resolution to `GET /maps/vector/{path}`:
  - Bearer token in request header is forwarded upstream.
  - If no bearer token is present, proxy uses `key` query/header, then server
    `OS_API_KEY`.
- Added a minimal UI lab at `ui://mcp-geo/simple-map-lab` backed by
  [`ui/simple_map.html`](../ui/simple_map.html).
  - OS Vector proxy mode (style + tile path through `/maps/vector/*`).
  - OS Style dropdown with pre-populated OS and OS Open style presets.
  - PMTiles mode (browser-side `pmtiles://` source with generic vector layer rendering).
  - Basic timing telemetry (`styleDataMs`, `sourceDataMs`, `firstIdleMs`) and
    a deterministic pan benchmark loop.

## How to run

1. Start the server:

   ```bash
   uvicorn server.main:app --reload
   ```

2. Open the lab resource:
   - `GET /resources/read?uri=ui://mcp-geo/simple-map-lab`
   - Direct HTML route: `GET /ui/simple-map-lab`
   - Short route redirect: `GET /simple-map-lab`
   - Or load in an MCP-Apps-compatible host that can render `ui://` resources.

3. OS Vector auth trial matrix:
   - Browser bearer path: set token in "Browser Bearer Token", leave API key override blank.
   - Header/query key path: set "API key override", clear token.
   - Server fallback path: clear both fields, set `OS_API_KEY` in env.

4. PMTiles trial:
   - Select `PMTiles (browser direct)`.
   - Provide a PMTiles URL.
   - Load map and run pan benchmark.

## OS style options in the UI

The `OS Style` dropdown in the lab offers these groups:

- `OS Styles`: Light, Dark, Road, Outdoor, Greyscale, No Labels, Black and White, ESRI, 3D
- `OS Open Styles`: Open Light, Open Dark, Open Road, Open Outdoor, Open Greyscale, Open Black and White

Simple guide:

- `Light` or `Open Light`: best first choice for most users.
- `Road` or `Open Road`: best for transport and street-focused maps.
- `Outdoor` or `Open Outdoor`: better for terrain and countryside context.
- `Dark` or `Open Dark`: lower glare for darker workspaces.
- `Greyscale` or `Black and White`: quieter background behind overlays.
- `No Labels`: removes map labels so your own labels are clearer.
- `ESRI` and `3D`: specialist styles for visual comparison.

## Notes on PMTiles benchmark interpretation

- This lab is a quick rendering/interaction smoke test, not a full scientific
  benchmark harness.
- For stronger evidence, run repeated tests on the same dataset, viewport, zoom
  ladder, and hardware profile, then compare:
  - first idle latency
  - average pan step time
  - error rate at target zooms

## Relevant external references

- OS API auth options and OAuth technical details:
  - <https://docs.os.uk/os-apis/getting-started/authentication>
  - <https://docs.os.uk/os-apis/getting-started/authentication/oauth2-technical-specification>
- PMTiles concepts and browser usage:
  - <https://docs.protomaps.com/pmtiles>
  - <https://docs.protomaps.com/pmtiles/cloud-storage>
