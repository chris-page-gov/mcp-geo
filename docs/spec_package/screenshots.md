# Screenshots and Capture Checklist

This package references screenshots that should be captured during testing.
Existing images are included where available; missing captures are listed below.

## Existing images in repo

- Example OS map render (external):
  - `docs/MasterMap from Claude.png`
  - `docs/MasterMap from Claude.jpg`

## Recommended captures (to be added)

1. **MCP Inspector connected to MCP Geo**
   - Capture tools list and resources list.
2. **Geography selector UI (ui://)**
   - Show boundary overlay and selected area.
3. **Route planner UI (ui://)**
   - Show start/end pins and route payload panel.
4. **Feature inspector UI (ui://)**
   - Show feature properties panel.
5. **Statistics dashboard UI (ui://)**
   - Show ONS dataset selection and chart.
6. **Boundary pipeline status ticker**
   - Terminal output of `scripts/boundary_status_ticker.py`.

## Suggested filenames (place under docs/spec_package/images/)

- `inspector-tools-resources.png`
- `ui-geography-selector.png`
- `ui-route-planner.png`
- `ui-feature-inspector.png`
- `ui-statistics-dashboard.png`
- `boundary-status-ticker.png`

## Where to capture

1. **Claude Desktop (preferred)**: if the MCP-Apps UI opens in Claude Desktop,
   capture the widget view directly after calling `os_apps.render_*`.
2. **MCP Inspector (fallback)**: use the Inspector UI resource renderer. Capture
   the widget after selecting the MCP Geo server and loading the `ui://` resource.

## Capture instructions

- Use a 1440px wide window (or full screen) for consistency.
- Save files under `docs/spec_package/images/` with descriptive names.
- Update the markdown references in the spec files once captured.
