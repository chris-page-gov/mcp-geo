# MCP-Apps UI Redesign Review Form

Use this form during design review sessions. Duplicate one section per review cycle.

## Review metadata

- Date:
- Reviewer:
- Host tested: (`Claude` / `VS Code` / `Playground` / other)
- Viewport tested: (`320x500`, `360x500`, custom)
- UI file:

## Compact-window pass/fail checklist

- [ ] No horizontal scroll at `320x500`
- [ ] Primary action visible without scroll
- [ ] Status/error message visible without scroll
- [ ] Empty/loading/error states readable
- [ ] Keyboard-only flow works
- [ ] Touch targets are at least `40px` high
- [ ] Contrast is readable in host light/dark themes

## MCP-Apps protocol checklist (where applicable)

- [ ] Sends `ui/initialize`
- [ ] Consumes `ui/notifications/host-context-changed`
- [ ] Handles `availableDisplayModes`
- [ ] Handles `displayMode` changes cleanly
- [ ] Handles `containerDimensions` (height/width/max variants)
- [ ] Fullscreen is optional enhancement only

## Information architecture checklist

- [ ] Top bar has task title + one-line purpose
- [ ] Controls are grouped into 2-4 clear sections
- [ ] Visual pane (map/chart) remains visible during interaction
- [ ] Diagnostic text is plain-language and novice-safe
- [ ] Advanced options are collapsed by default

## Decision

- [ ] Approved
- [ ] Approved with follow-up
- [ ] Not approved

## Findings

- Critical issues:
- Major issues:
- Minor issues:
- Suggested redesign actions:

---

## Current baseline assessment snapshots (2026-03-01)

- `ui/boundary_explorer.html`: Not approved (desktop-first density; large min heights)
- `ui/geography_selector.html`: Not approved (desktop-first layout; large map min height)
- `ui/statistics_dashboard.html`: Approved with follow-up (compact pass needed)
- `ui/simple_map.html`: Not approved for inline-host usage (lab layout, fixed sidebar)
- `ui/feature_inspector.html`: Not approved (static mock, no MCP-Apps handshake)
- `ui/route_planner.html`: Not approved (static mock, no MCP-Apps handshake)
