# MCP-Apps Small-Window Figma Handoff

This folder contains a Figma-importable wireframe file designed for the strictest cross-host inline budget.

## Design budget

- Base frame: `320 x 500`
- Secondary frame: `360 x 500`
- Fullscreen is optional enhancement only

## Files

- `mcp_apps_small_window_wireframes.svg`
- `compact_ui_proposals.html`
- `compact_ui_proposals_native.html`
- `mcp_figma_setup_and_capture_runbook.md`

## Import into Figma

1. Open Figma.
2. Create or open a design file.
3. Drag `mcp_apps_small_window_wireframes.svg` onto the canvas.
4. Run `Ungroup` until each frame is independently editable.
5. Convert repeated blocks into components:
   - Header bar
   - Status strip
   - Primary action bar
   - Map/visual viewport
   - Collapsible section row

## Included wireframes

- Boundary Explorer (compact)
- Geography Selector (compact)
- Statistics Dashboard (compact)
- Simple Map Lab (compact)
- Feature Inspector (compact)
- Route Planner (compact)

## Notes

- These are structural wireframes, not final visual design.
- Use auto-layout and component variants for production design passes.
- If text fidelity is degraded after capture, prefer `compact_ui_proposals_native.html`
  for recapture (native HTML blocks, no embedded SVG text).
