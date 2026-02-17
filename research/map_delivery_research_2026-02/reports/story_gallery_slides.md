---
marp: true
paginate: true
theme: default
title: MCP Geo - Map Story Gallery
---

# MCP Geo Map Story Gallery

Real-world layered map stories for Wednesday presentation

- Scenario pack version: `2026-02-16`
- Evidence source: `research/map_delivery_research_2026-02/evidence/screenshots/`
- Delivery source: `research/map_delivery_research_2026-02/reports/story_gallery_report.md`

---

## 1) Coventry election boundary change impact

![Coventry election boundary change impact](../evidence/screenshots/chromium-desktop-story-1-coventry-boundary-change.png)

- Persona: Election planning analyst
- Question: How do proposed 2026 ward boundaries change campaign focus around CV1 3HB?
- Decision: Shift canvassing and polling logistics toward Spon End edge streets where boundary movement changes local representation.

**Speaker notes**
Use this to show boundary-led operational change, not just visual change: `os_maps.render` baseline, then `admin_lookup.containing_areas`, `admin_lookup.area_geometry`, and `os_apps.render_boundary_explorer` for interactive validation.

---

## 2) Village Hotel Coventry service catchment

![Village Hotel Coventry service catchment](../evidence/screenshots/chromium-desktop-story-2-village-hotel-catchment.png)

- Persona: Local service operations manager
- Question: Which nearby postcode clusters fall within practical service coverage of Village Hotel Coventry?
- Decision: Prioritize staffing and delivery windows for the business park and Spon End edge using multi-ring catchment overlap.

**Speaker notes**
Tell the story from address intelligence to service planning: `os_places.by_postcode`, `os_places.radius`, and `os_map.inventory` layered on the same map; then geography selector for rapid area checks.

---

## 3) Coventry multi-route reliability planning

![Coventry multi-route reliability planning](../evidence/screenshots/chromium-desktop-story-3-coventry-route-layering.png)

- Persona: Transport network coordinator
- Question: Which route alignment best balances reliability and accessibility between station and civic destinations?
- Decision: Operate the preferred corridor day-to-day and retain a Spon End alternate for disruption windows.

**Speaker notes**
Emphasize layered route alternatives and interchange points. Mention `os_vector_tiles.descriptor` plus `os_apps.render_route_planner` as the handoff from static story frame to richer interactive planning.

---

## 4) Bristol flood resilience response map

![Bristol flood resilience response map](../evidence/screenshots/chromium-desktop-story-4-bristol-flood-layer-stack.png)

- Persona: Local resilience forum planner
- Question: Which critical facilities are exposed when flood zones and evacuation corridors are viewed together?
- Decision: Prioritize flood barrier deployment near river-adjacent facilities and pre-stage diversion signage on the route spine.

**Speaker notes**
Position this as resilience-grade stack assembly: capability discovery (`os_maps.wmts_capabilities`, `os_features.wfs_capabilities`) then operational tile/layer consumption (`os_maps.raster_tile`) into one decision frame.

---

## 5) Manchester development inventory and export

![Manchester development inventory and export](../evidence/screenshots/chromium-desktop-story-5-manchester-inventory-export.png)

- Persona: Urban growth programme lead
- Question: Can we evidence building intensity, street connectivity, and address points in one exportable planning snapshot?
- Decision: Approve phased data-pack export for committee review, prioritizing mixed-use corridor investment.

**Speaker notes**
Call out end-to-end governance flow: inventory composition (`os_map.inventory`), drill-down (`os_features.query` + feature inspector), then audit-friendly export lifecycle (`os_map.export`).

---

## 6) Westminster policy briefing with layered indicators

![Westminster policy briefing with layered indicators](../evidence/screenshots/chromium-desktop-story-6-westminster-policy-layering.png)

- Persona: Policy and analytics adviser
- Question: How do ward boundaries, active travel corridors, and environmental indicators combine for cabinet-level decisions?
- Decision: Target investment to corridor-adjacent wards where transport upgrades and air-quality improvements align.

**Speaker notes**
Use this as the cross-domain close: map + indicator workflows. Mention statistics dashboard and geography selector, and note UI probe usage to verify host capability before live demos.

---

## Appendix: Files for the presentation pack

- Story report: `research/map_delivery_research_2026-02/reports/story_gallery_report.md`
- Slide deck: `research/map_delivery_research_2026-02/reports/story_gallery_slides.md`
- Evidence images: `research/map_delivery_research_2026-02/evidence/screenshots/`
- Trial observations: `research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl`
