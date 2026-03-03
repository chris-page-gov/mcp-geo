# MCP-Apps Window Constraints and Redesign Review (2026-03-01)

## Scope

This review answers four questions:

1. Do we have all MCP published and draft specs locally in submodules?
2. Is small/non-maximizable UI behavior a spec limit or a client implementation limit?
3. What explicit window budget should we design for across Claude and VS Code?
4. How does each current UI score against that budget, and what should be redesigned first?

## Specification Inventory (Local Submodules)

The `modelcontextprotocol` GitHub org currently exposes specification trees in only three public repos:

- `modelcontextprotocol` (`docs/specification/*` published + draft core MCP)
- `ext-apps` (`specification/2026-01-26` + `specification/draft`)
- `ext-auth` (`specification/draft`)

Local status in this repository:

- Present: `docs/vendor/mcp/repos/modelcontextprotocol`
- Present: `docs/vendor/mcp/repos/ext-apps`
- Added in this change: `docs/vendor/mcp/repos/ext-auth`

Conclusion: all currently published/draft MCP specification repositories are now vendored locally.

## Spec vs Host Implementation: Window Behavior

### What the spec says

From `ext-apps` spec (`2026-01-26`):

- Host provides `containerDimensions` (`height` or `maxHeight`, `width` or `maxWidth`).
- Host and view negotiate display modes (`inline`, `fullscreen`, `pip`).
- Host may decline a display-mode request and return current mode.

Implication: the specification does not guarantee fullscreen/maximize. It defines negotiation.

## What host docs say (current evidence)

- VS Code MCP docs explicitly state display modes are currently inline-only.
- Claude app design guidelines define inline card sizing guidance and state inline cards should not exceed 500px height.

Implication: inability to maximize in VS Code is implementation-level today, not a protocol violation.

## Cross-host explicit design budget

Use this as the design contract for all MCP-Apps UIs in this repo.

- `Primary target frame`: `320 x 500` (smallest reliable cross-host inline budget)
- `Comfort target frame`: `360 x 500`
- `Desktop inline target`: fluid width, but still assume `max-height: 500` visible without host scroll
- `Fullscreen`: progressive enhancement only, never required for core flow

Derived rules:

- No mandatory `min-height` above `320px` for map or chart areas in inline mode.
- No desktop-first multi-column layout as default under `900px` width.
- First actionable control must be visible in first `120px` vertical space.
- Primary action + status must remain visible without scrolling at `320 x 500`.

## Current UI Review (Redesign Readiness)

Scoring:

- `PASS`: usable at `320 x 500`
- `PARTIAL`: usable with friction or hidden primary actions
- `FAIL`: layout breaks or core action hidden/unusable

| UI | Host handshake | Small-window fit | Key issues | Status |
| --- | --- | --- | --- | --- |
| `ui/boundary_explorer.html` | Yes (`ui/initialize`, mode request, host-context changed) | Poor | 3-column desktop grid default; map `min-height: 720px`; heavy panel density | FAIL |
| `ui/geography_selector.html` | Yes | Poor | 2-column desktop default; map panel `min-height: 520px`; dense controls and chips | FAIL |
| `ui/statistics_dashboard.html` | Yes | Mixed | Better than explorer, but chart/card density still desktop-first; fixed chart heights | PARTIAL |
| `ui/simple_map.html` | No MCP-Apps handshake (lab page) | Poor in narrow panes | Fixed `360px` side panel + full-height map assumptions | FAIL |
| `ui/feature_inspector.html` | No MCP-Apps handshake | Poor | Static mock, `min-height: 100vh`, desktop split grid | FAIL |
| `ui/route_planner.html` | No MCP-Apps handshake | Poor | Static mock, `min-height: 100vh`, desktop split grid | FAIL |

## Redesign Priorities

1. Introduce a shared `inline-compact` layout contract in all six UIs.
2. Apply host `containerDimensions` when provided.
3. Make fullscreen optional enhancement only.
4. Move from multi-panel desktop compositions to staged, single-column flows under `900px`.

## Design Review Action Plan (Implementation-focused)

### Global requirements (all UIs)

- Add a shared compact CSS contract:
  - target frame `320 x 500`
  - default single-column layout below `900px`
  - no required panel above `320px` min-height in inline mode
- Keep top-of-frame sequence consistent:
  - title row
  - status/diagnostic strip
  - primary controls
  - visual pane
  - primary action
- Implement or normalize host context behavior:
  - consume `displayMode`, `availableDisplayModes`, and `containerDimensions`
  - treat fullscreen as optional enhancement only

### UI-specific redesign directives

1. `ui/boundary_explorer.html`

- Replace 3-column desktop grid with stacked compact flow at inline widths.
- Move advanced controls into collapsible sections.
- Reduce map default min-height from `720px` to compact range (`150-190px` inline).
- Keep current host handshake logic; add explicit container-dimension sizing.

2. `ui/geography_selector.html`

- Collapse 2-column structure into one compact column by default in inline mode.
- Reduce map panel and secondary panel min-heights (`520px` and `380px` currently).
- Prioritize selected area and confirm action in top viewport.
- Preserve handshake logic and add container-dimension sizing.

3. `ui/statistics_dashboard.html`

- Convert dashboard card/chart density into compact progressive sections.
- Replace fixed chart blocks with compact chart containers and optional expand affordance.
- Keep refresh action and error states visible without scroll at `320x500`.

4. `ui/simple_map.html`

- Keep as lab tool but add a compact host-friendly layout variant:
  - avoid fixed `360px` side rail in inline mode
  - make controls collapsible
  - keep “Load map” and status visible at all times

5. `ui/feature_inspector.html`

- Promote from static mock to MCP-Apps-capable view:
  - add `ui/initialize` and host-context handling
  - compact sequence: status -> geometry -> key properties -> action

6. `ui/route_planner.html`

- Promote from static mock to MCP-Apps-capable view:
  - add `ui/initialize` and host-context handling
  - compact flow: start/end -> map -> turn preview -> calculate button

### Execution order

1. Shared compact layout contract + host context utility
2. Boundary Explorer + Geography Selector
3. Statistics Dashboard + Simple Map Lab compact variant
4. Feature Inspector + Route Planner MCP-Apps handshake upgrade
5. Final compact-window acceptance run using review form

## UI Review Form (Use for redesign sign-off)

Use one copy per UI and per iteration.

- UI: `<name>`
- Revision date: `<YYYY-MM-DD>`
- Reviewer: `<name>`

Checklist:

- [ ] Works at `320 x 500` without horizontal scroll
- [ ] Primary action visible without scrolling
- [ ] Status/error area visible without scrolling
- [ ] No required control hidden behind collapsed sections
- [ ] Keyboard navigation complete
- [ ] `ui/initialize` implemented (for MCP-Apps views)
- [ ] Handles host `displayMode` + `availableDisplayModes`
- [ ] Handles host `containerDimensions`
- [ ] Fullscreen is optional, not required
- [ ] Empty/error/loading states readable at small size

Decision:

- [ ] Approve for release
- [ ] Approve with exceptions
- [ ] Reject and redesign required

Notes:

- Risks:
- Required fixes:
- Nice-to-have improvements:

## Figma Handoff Status

Figma MCP is now configured and authenticated in this environment.

What worked:

- direct capture into Figma file via `generate_figma_design`
- iterative recapture into existing file using `outputMode: existingFile`

What did not add strong design value:

- SVG-embedded text capture fidelity was inconsistent (broken glyphs in import)

Current practical approach:

- use native HTML capture pages for cleaner text/layer output
- keep this report as the primary design-decision artifact
- use Figma mainly for collaborative annotation after decisions are made

Related docs:

- `docs/design/figma/mcp_figma_setup_and_capture_runbook.md`
- `docs/design/figma/README.md`

## Source Links

- MCP Apps spec (local): `docs/vendor/mcp/repos/ext-apps/specification/2026-01-26/apps.mdx`
- VS Code MCP docs: https://code.visualstudio.com/docs/copilot/chat/mcp-servers
- Claude app design guidelines: https://www.claude.com/docs/claude-code/mcp-app-design-guidelines
