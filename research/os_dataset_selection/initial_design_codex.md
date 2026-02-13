**Proposed Exemplar: “Boundary Explorer” Map Wizard (Local-First)**

**User journey (what “simplest questions” becomes)**
1. User asks: “Show me everything in this ward/postcode” or “What buildings/roads are within this boundary?”
2. Assistant calls `os_mcp.route_query` and gets back: `intent=boundary_explorer` (new) + recommends `os_apps.render_boundary_explorer`.
3. The Boundary Explorer opens (MCP-App):
- Step A: choose area (search postcode/name, pick admin level, or draw)
- Step B: pick “detail pack” (UPRNs, buildings, road links, path links)
- Step C: preview map immediately + a sidebar “Inventory” list
- Step D: click any object to see its hierarchy (UPRN -> linked IDs -> building TOIDs/USRNs where available) and export data

---

## Core design choices (what prevents the model “getting lost”)

**1) A constrained “map recipe” contract**
Everything is translated into a small schema the UI + server can execute reliably:

- `aoi`: `{type: postcode|admin_area|bbox|polygon|viewport, value: ...}`
- `baseline`: `{provider: os|osm, style: light|road|outdoor|3d|nodata}`
- `layers`: `boundary`, `uprns`, `buildings`, `road_links`, `path_links`, `custom_file_*`
- `inventoryMode`: `viewport|boundary|selection` (default `viewport` for scale)
- `budgets`: max features per layer, paging strategy, sampling rules
- `exports`: `geojson`, `csv`, `mcp-geo recipe json`

The assistant never tries to “pick datasets” directly; it fills the recipe, then the server/UI executes.

**2) Progressive disclosure (zoom + scope)**
You cannot realistically list *all* UPRNs/buildings/links for a whole local authority in one go. The UX should default to:
- show boundary outline immediately
- show counts + samples at large extents
- switch to full feature loading only when zoomed in or when the user explicitly chooses “boundary-wide export”

This matches how modern web mapping tools stay usable while still giving access to underlying data.

---

## What to build on in `mcp-geo` (you already have the primitives)

- UI pattern: `ui://mcp-geo/geography-selector` already does “search + select + map + layers”.
- OS basemap plumbing: `server/maps_proxy.py` already proxies OS vector tiles and rewrites styles.
- Data tools:
- `admin_lookup.area_geometry` (bbox + optional geometry)
- `os_places.*` (UPRNs / addresses)
- `os_features.query` (NGD features by bbox + collection)
- `os_linked_ids.get` (UPRN/USRN/TOID relationships)

So Boundary Explorer is mainly “composition + UX + budgets + key handling”.

---

## Boundary Explorer: the specific recipe you asked for

**Area sources**
- OA / LSOA / MSOA / Ward / District / Local Authority / Region / Nation: from `admin_lookup.*` + (extend) cache pipeline
- Parliamentary constituencies: add as an `admin_lookup` source (or via boundary cache dataset) so it’s first-class in the selector

**Layer packs**
1. **Boundary layer**
- Always on: the chosen area polygon (or bbox fallback)
2. **UPRN inventory layer**
- From `os_places.within` for viewport/bbox
- For postcode-mode: `os_places.by_postcode`
- Inventory list groups by (optional): classification / custodian / street / etc
3. **Buildings (polygons / 3D-ish)**
- Two distinct concepts:
- Visual basemap buildings: OS VTS style (e.g., 3D style) for immediate context
- Queryable building features: `os_features.query` for the relevant NGD collection(s) in the current viewport
- Inventory list shows building IDs + key attributes (and supports click-to-highlight)
4. **Road links + path links**
- Queryable: `os_features.query` collections for roads/paths in viewport
- Inventory list supports “show connected” relationships when possible
5. **Hierarchy view (lazy, click-driven)**
- For a selected UPRN: call `os_linked_ids.get` once, then show:
- linked USRN (street)
- linked TOIDs (where present)
- optionally follow-up queries to fetch the geometry for those linked IDs (best-effort)

The important scaling trick: don’t try to resolve linked IDs for thousands of UPRNs up-front. Do it on-demand for selected items.

---

## Local file layers (drag/drop or load)

**MVP (no server dependency)**
- UI supports drag/drop of:
- GeoJSON (`.geojson`, `.json`)
- CSV with lat/lon columns (simple heuristic + prompt)
- Added as local-only MapLibre sources (never uploaded unless user clicks “Upload to server”)

**Nice-to-have**
- Shapefile zip (`.zip`) via a small in-browser parser (or a server-side converter later)
- Styling wizard: point/line/polygon auto-style + legend

This is exactly the “Add layer from file” affordance users expect from ArcGIS Online/QGIS/etc, but kept local-first.

---

## OS API key handling (secure, local-first, minimal friction)

You have two complementary “good” paths. I’d implement both.

**A) Recommended default: configure once in Claude Desktop config**
This keeps the key out of chat, out of URLs, and ensures tools *and* basemaps work everywhere (not just in the widget).
- In Claude Desktop’s `claude_desktop_config.json`, set `OS_API_KEY` for the `mcp-geo` server process environment.

**B) In-app “Connect OS” flow (session/ephemeral)**
For users who won’t edit config:
1. Boundary Explorer shows “Connect Ordnance Survey” when OS-backed layers are selected and the key is missing.
2. Clicking opens a dedicated widget panel (password input, no copy/cut) and posts the key directly to a **non-tool HTTP endpoint** on the local server (so it doesn’t flow through the LLM/tool transcript).
3. Server stores it in memory for the session and updates:
- map proxy access (so vector tiles work)
- tool client access (so `os_places`, `os_features`, `os_linked_ids` work)

**Critical security detail**
- Avoid embedding the key in tile/style URLs (query params are easy to leak via logs, screenshots, copy/paste, browser history).
- Prefer: server holds the key; UI calls `/maps/vector/...` without a key; proxy injects upstream key server-side.

This is the “right” local-first security posture: easy for users, minimal key exposure, and it works with MapLibre.

---

## A small set of concrete additions (tooling + resources)

**New UI**
- `os_apps.render_boundary_explorer` -> `ui://mcp-geo/boundary-explorer`

**New “layer catalog” resource (prevents dataset confusion)**
- `resource://mcp-geo/layers-catalog`
- Maps human intents to:
- NGD collection IDs
- geometry type
- typical zoom thresholds
- default styling hints
- quotas/budgets

**Optional new helper tools**
- `os_features.collections` (list NGD collections from the upstream OGC API so the catalog stays correct)
- `os_map.inventory` (server-side “counts + samples + paging tokens” across multiple layers, so UI doesn’t reinvent orchestration)
- `os_map.export` (exports current selection/viewport/boundary as GeoJSON/CSV bundle + the recipe JSON)

---

## Suggested next steps (so this becomes shippable fast)

1. Define the Boundary Explorer “map recipe” JSON schema + layer catalog (one page spec).
2. Implement the UI as a fork/evolution of `ui/geography_selector.html` (it already has the OS key password field and MapLibre wiring).
3. Implement the secure key onboarding path:
- config-first docs + “Connect OS” widget endpoint for ephemeral sessions
- remove key from style/tile URLs in the widget by relying on the server-side proxy
4. Add viewport-scoped inventory with budgets, then add exports.
5. Extend admin sources to include Parliamentary constituencies (and align naming/levels across UI + tools).

If you want, I can turn this into a concrete checklist aligned to `docs/spec_package/10_mcp_apps_ui.md` and the existing tool taxonomy, including exact tool/resource names and the minimal server endpoints needed for the secure connect flow.