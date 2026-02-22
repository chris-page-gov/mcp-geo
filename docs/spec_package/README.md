# MCP Geo - Full Specification Package (Prototype)

This package documents the current MCP Geo prototype as a reasoned, end-to-end specification.
It is designed for test readiness: it captures goals, scope, architecture, API contracts,
operational behaviors, and the user experience expected from MCP tools and MCP-Apps UI.

## Contents

1. Aims & objectives: `docs/spec_package/01_aims_objectives.md`
2. Personas & user stories: `docs/spec_package/02_personas_user_stories.md`
3. System architecture: `docs/spec_package/03_architecture.md`
4. Detailed design (components): `docs/spec_package/04_system_design.md`
5. Data flows & cache pipeline: `docs/spec_package/05_data_flow_and_cache.md`
6. API contracts & protocol: `docs/spec_package/06_api_contracts.md`
6a. Map delivery fallback contracts appendix:
   `docs/spec_package/06a_map_delivery_fallback_contracts.md`
7. Security & privacy: `docs/spec_package/07_security_privacy.md`
8. Observability & operations: `docs/spec_package/08_observability_ops.md`
9. Testing & quality: `docs/spec_package/09_testing_quality.md`
10. MCP-Apps UI & interactive tools: `docs/spec_package/10_mcp_apps_ui.md`
11. Scenario walkthroughs: `docs/spec_package/11_walkthroughs.md`
12. Backlog & completion plan: `docs/spec_package/12_backlog_and_plan.md`
13. Screenshots & capture checklist: `docs/spec_package/screenshots.md`
14. Sequence diagrams: `docs/spec_package/13_sequence_diagrams.md`
15. Tool operability specification (Gherkin):
    `docs/spec_package/14_tool_operability.feature`
16. Tool operability coverage metrics:
    `docs/spec_package/14_tool_operability_coverage.md`
17. Export instructions: `docs/spec_package/export.md`

## Current scope snapshot (prototype)

- MCP server with HTTP (/mcp) and STDIO transports.
- Tool catalog for OS Places, OS Names, OS NGD features, linked identifiers, maps,
  admin lookup (PostGIS cache), ONS live datasets, and MCP-Apps UI rendering.
- Boundary cache pipeline for ingesting and validating UK administrative boundaries.
- MCP-Apps UI resources (geography selector, route planner, feature inspector,
  statistics dashboard) delivered via `ui://` resources.

## How to use this package

- Read in order for a full specification.
- Use `12_backlog_and_plan.md` as the roadmap to reach production-grade completeness.
- Use `screenshots.md` to capture missing images when running the UI and inspector.
- Use `export.md` to produce a DOCX/PDF deliverable.
