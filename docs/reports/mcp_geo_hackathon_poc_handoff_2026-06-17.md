# MCP-Geo Hackathon PoC Handoff

Date: 2026-06-17
Purpose: implementation handoff for raising the AI in Action rubric score above
the previous 85/100 assessment.

## Summary

MCP-Geo now exposes a native stakeholder workflow surface through:

- `os_workflows.descriptor`
- `os_workflows.query`

The first workflow tranche covers the three highest-value hackathon PoC gaps:

1. `incident_impact` for affected premises and support-relevant counts.
2. `batch_address_match` for address-to-UPRN matching with review queues.
3. `planning_constraints` for site-constraint review and public-data connector gaps.

These workflows convert benchmark-only orchestration into product surface. They
return structured method steps, result tables, review queues, export contracts,
confidence caveats, next actions and provenance.

## Primary Users

| User | Workflow need | PoC value |
| --- | --- | --- |
| Emergency planning officer | Identify affected premises and support records from an incident area. | Faster situational awareness with explicit caveats and review queues. |
| Data quality or GIS analyst | Batch match free-text addresses to UPRNs. | Repeatable confidence bands, duplicate detection and exportable review work. |
| Planning officer or policy analyst | Summarise site constraints from public spatial layers. | Clear source-dependency map before planning.data/local-plan connectors are built. |

## Four-Week PoC Scope

### Week 1: Workflow Hardening

- Finalise `os_workflows.query` payload examples for SG01, SG02 and SG05.
- Add saved demo payloads for incident, address batch and planning site review.
- Confirm route-query phrasing lands on the new workflow IDs.
- Run targeted regression and OWASP manifest validation.

### Week 2: Live Data Runs

- Run SG01 and SG02 with a live OS Places key and record the workflow evidence.
- Compare native workflow output against the existing stakeholder benchmark
  reference outputs.
- Add acceptance thresholds for high-confidence, review and unmatched rows.

### Week 3: Planning/Flood Connector Spike

- Implement one connector-backed public layer for `planning_constraints`, starting
  with `flood-risk-zone`.
- Record source URL, publication/freshness metadata, geometry operation and
  licensing caveat in every result.
- Keep the workflow useful when connectors are unavailable by returning explicit
  `connector_needed` review rows.

### Week 4: User Evaluation

- Run a 30-minute desk exercise with one emergency planning/GIS user and one
  planning or data user.
- Measure time-to-first-reviewable-output, review burden, false confidence and
  export usefulness.
- Decide whether to continue based on the success measures below.

## Data And Systems

| Data/system | Use | Sensitivity and controls |
| --- | --- | --- |
| Ordnance Survey Places | Address search and UPRN resolution. | API key required; no keys in prompts, logs or screenshots. |
| Caller-supplied address/support records | Batch matching and incident support counts. | Treat as internal or sensitive; no storage by workflow tool; manual review required. |
| Incident geometry WKT | Point-in-polygon impact review. | Validate source and time validity before operational use. |
| planning.data.gov.uk layers | Planning/flood/heritage constraints. | Public data, but freshness and coverage must be shown per layer. |
| Admin lookup | Area context for affected records or sites. | Public boundary metadata; cache freshness should be reported. |

## MCP Contract

| Tool | Purpose | Stable MCP role |
| --- | --- | --- |
| `os_workflows.descriptor` | Lists workflow contracts, required inputs, primary tools and output contracts. | Tool for workflow discovery. |
| `os_workflows.query` | Runs the selected workflow ID and returns structured results. | Tool for deterministic workflow execution. |
| `os_mcp.route_query` | Routes natural-language stakeholder prompts to the workflow. | Tool router; now recommends `os_workflows.query`. |
| `os_places.search` | Optional address resolution when `resolveAddresses=true`. | Tool called by the workflow for live OS-backed matching. |
| `os_apps.render_boundary_explorer` | Companion map review when visual inspection is needed. | MCP Apps extension with fallback via structured output. |

The workflows keep draft-spec compatibility by returning explicit state in the
tool result. They do not depend on protocol sessions, and unresolved work is
represented as review rows or next actions rather than hidden server state.

## Safety And Governance

- Human review remains mandatory before emergency, planning or support decisions.
- `os_workflows.query` is read-only and side-effect free, but is marked
  `internal` in the OWASP tool risk inventory because caller-supplied records may
  contain operational or support data.
- The planning workflow returns connector gaps explicitly and does not fabricate
  constraints from memory.
- Review queues distinguish missing coordinates, missing UPRNs, duplicate rows
  and connector gaps.
- A future live deployment should complete DPIA/EIA screening and, if decision
  support is used in production workflows, an Algorithmic Transparency Record.

## Success Measures

| Measure | Four-week target |
| --- | ---: |
| SG01 native workflow evidence | Workflow runs from one `os_workflows.query` call plus optional map/admin lookup. |
| SG02 high-confidence/review/unmatched output | 100% of rows classified with exportable review queue. |
| SG05 connector transparency | Every missing public layer returned as a named connector gap with source URL. |
| Time to reviewable output | Under 5 minutes for the supplied SG01/SG02 fixtures. |
| Evidence quality | Every result includes method, tools/data, caveats, review queue and export contract. |
| Safety | No secrets or raw sensitive support notes in logs or screenshots. |

## Open Decisions

- Whether to rename the workflow surface into domain-specific tools once the
  contracts stabilise.
- Which public planning/flood layer to implement first for connector-backed
  intersections.
- Whether review queues should be exported by a later stateful export tool or
  kept as caller-managed structured output.
- What confidence thresholds local authorities want for operational address
  matching.
