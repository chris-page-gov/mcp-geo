---
name: mcp-geo-detailed-os-maps
description: Build or refine user-facing mcp-geo HTML maps with OS vector detail, label-safe overlays, browser-stored OS keys, and real-browser validation.
---

# MCP Geo Detailed OS Maps

Use this skill when a user-facing map in this repo needs precise Ordnance Survey
street or building context, especially for report HTML, accessibility mapping,
town-centre navigation, or slide-like static map outputs that still benefit from
interactive zoom.

## Default approach

- Prefer a MapLibre underlay with the OS vector Light style:
  `OS_VTS_3857_Light.json`.
- Keep your thematic overlay separate from the basemap. Do not bake route
  highlighting into the basemap.
- Treat the OS detail layer as progressive enhancement:
  - if a browser-held OS Maps API key is available, enable detailed context by default
  - if not, keep a simplified fallback view that still works offline or without secrets

## Overlay design rules

- Preserve OS labels. Use casing, outlines, or translucent edge emphasis instead
  of thick opaque fills when highlighting roads or paths.
- Match the geometry to the mapped object as closely as possible:
  - road access overlays should sit on the road segment or pavement edge
  - avoid bubbles or large markers that hide the exact segment being discussed
- Put long explanations in hover text, sidebars, or perimeter callouts, not on
  the centre of the map.
- If the map is for navigation, remove decorative labels before removing
  orientation cues such as north arrow, rail line, seafront, river edge, or
  major anchors.

## Browser key pattern

- Never hardcode OS keys into generated HTML.
- Store the browser-side key locally in browser storage only.
- Make the no-key path explicit and usable.
- When only the presentation layer changes, prefer regenerating from a saved
  export rather than refetching live OS data. For the wheelchair report
  generator, use `--reuse-export` with the existing dated JSON export.
- When switching styles in MapLibre, remember that style changes clear custom
  sources and layers; rehydrate overlays after `style.load` if you render them
  inside the MapLibre stack.

## Validation checklist

1. Open the generated HTML in a real browser.
2. Check default fit at desktop width with no clipping or hidden sidebars.
3. Check zoom in/out, mouse wheel zoom, drag pan, and reset behavior.
4. Check label readability with the detailed OS basemap enabled.
5. Check that fallback behavior is still clear and usable when no browser key is present.
6. If the map is intended for a static export, generate a screenshot after the
   final browser pass.

## Useful local references

- Generator: `scripts/generate_teignmouth_wheelchair_access_map.py`
- Simple MapLibre lab: `ui/simple_map.html`
- Boundary explorer: `ui/boundary_explorer.html`
- Map proxy/auth handling: `server/maps_proxy.py`
