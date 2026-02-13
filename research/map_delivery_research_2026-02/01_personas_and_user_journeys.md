# Personas and User Journeys

## Research framing

This persona set follows practical user-research conventions:

- Identify user segments by goals, context, and constraints (not job title only).
- Capture primary tasks, blockers, decision risk, and accessibility needs.
- Translate each persona into verifiable map-delivery requirements.

## Persona set

### Persona A: Public Resident (low technical confidence)

- Goal: find where they are, what area they belong to, and nearby services.
- Typical questions: “Which ward/borough am I in?”, “Show this postcode on a map.”
- Constraints: mobile-first, variable network, no API key knowledge.
- Critical requirements:
  - zero-config map display
  - readable labels on small screens
  - clear fallback when interactive map cannot load

### Persona B: Policy/Service Analyst (local authority)

- Goal: compare geography boundaries with ONS indicators and derive action areas.
- Typical questions: “Which LSOAs in this district have high unemployment pressure?”
- Constraints: reproducibility, auditability, governance sign-off.
- Critical requirements:
  - deterministic outputs (same query, same map)
  - exportable geometry/data references
  - metadata for provenance and dataset versions

### Persona C: Data Journalist / Civic Researcher

- Goal: rapidly explain place-based trends with clear visual evidence.
- Typical questions: “Show where this statistic concentrates and what boundaries matter.”
- Constraints: tight publication timelines, mixed devices/browsers.
- Critical requirements:
  - fast first render
  - static image fallback for embedding
  - direct links to data and methods

### Persona D: GIS Specialist (QGIS / ArcGIS user)

- Goal: blend MCP-delivered data with existing GIS workflows.
- Typical questions: “Can I load this tile profile in QGIS and style it quickly?”
- Constraints: CRS correctness, large datasets, desktop workflows.
- Critical requirements:
  - standards-compatible outputs (GeoJSON, vector/raster tiles, descriptors)
  - CRS and schema clarity
  - workflow descriptors for QGIS/GeoPackage

### Persona E: Product Engineer integrating MCP tools

- Goal: build robust map UX into MCP-capable apps and assistants.
- Typical questions: “What is the minimum reliable contract across clients?”
- Constraints: client variability (tool naming, UI support, payload limits).
- Critical requirements:
  - bounded payload contracts
  - predictable tool/resource behavior
  - composable map contracts (static + overlays + resource references)

### Persona F: Accessibility and Assisted-Tech user

- Goal: understand place outcomes without relying solely on visual interaction.
- Typical questions: “Summarize areas and relationships in plain language.”
- Constraints: screen readers, keyboard-only, cognitive load.
- Critical requirements:
  - non-visual fallback outputs
  - keyboard-operable widgets
  - descriptive alternative text and textual summaries

## Journey-to-requirement mapping

| Journey | Primary persona(s) | Must-have delivery mode | Failure fallback |
| --- | --- | --- | --- |
| Postcode to map | A, C | Static map URL + marker overlay | Text location summary + boundary names |
| Boundary exploration | B, D | Interactive MCP-App (MapLibre/OpenLayers style) | Exportable GeoJSON + feature list |
| Indicator comparison | B, C, F | Map + linked chart/tool output | Tabular summary with area codes |
| GIS handoff | D | QGIS profile/descriptor + resource URI | Download descriptor + clear manual steps |
| App integration | E | Tool-driven render contract (`imageUrl`, bbox, overlay collections) | Resource-backed payload with metadata |

## Acceptance criteria by persona

- Persona A/F: map task still completes with no API key and no UI widget support.
- Persona B/C: output includes provenance fields and repeatable area references.
- Persona D: CRS and layer semantics are explicit and GIS-importable.
- Persona E: cross-client payloads stay below practical transport limits and degrade safely.
