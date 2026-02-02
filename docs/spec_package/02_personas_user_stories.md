# Personas and User Stories

## Personas

### 1) Geo Analyst (Local Authority)
- Needs quick boundary lookup and area comparison.
- Works with UK administrative codes (LAD, OA, MSOA, etc.).
- Uses tools via MCP-enabled chat clients and dashboards.

### 2) Data Engineer (Platform)
- Maintains cache ingestion pipelines.
- Monitors data freshness and validation outcomes.
- Prefers structured metrics and automation.

### 3) App Developer (Civic Tech)
- Integrates the MCP server into a user-facing app.
- Wants stable APIs, predictable errors, and clear schemas.

### 4) Researcher (ONS/Policy)
- Queries ONS datasets and dimensions.
- Needs dataset discovery and codes lookup.

### 5) Product Manager (Prototype validation)
- Reviews capabilities, workflow coverage, and UI fidelity.
- Needs walkthroughs, screenshots, and design documentation.

## User stories

### Address and place lookup
- As a Geo Analyst, I can look up addresses by postcode and get coordinates to
  place points on a map.
- As a Developer, I can retrieve nearest addresses from a coordinate for UI
  typeahead and snapping.

### Administrative boundaries
- As a Geo Analyst, I can find containing areas for a point (lat/lon) using the
  cached boundary database.
- As a Data Engineer, I can see cache coverage and freshness statistics.

### ONS dataset discovery
- As a Researcher, I can search datasets, list dimensions, and retrieve codes.
- As a Researcher, I can query observations for a dataset/edition/version.

### UI workflows (MCP-Apps)
- As a user, I can open a geography selector to explore and choose areas.
- As a user, I can open the route planner to visualize start/end coordinates.
- As a user, I can open the feature inspector to explore NGD features.

### Operational quality
- As a Data Engineer, I can run the boundary pipeline end-to-end and see a
  ticker with progress and error counts.
- As a Product Manager, I can view a full specification package with diagrams
  and usage walkthroughs.

