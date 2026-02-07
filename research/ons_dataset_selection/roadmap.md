# Roadmap
Version: 1.0.0  
Generated (UTC): 2026-02-07T08:11:25Z

## Objective
Deploy a production-ready MCP Geo selection layer for ONS statistical and derived indicator discovery with tile-card-graph UX and AI-safe controls.

## Phase 0: Foundation (Weeks 1–2)
- Create canonical catalogue ingestion:
  - ONS dataset catalogue
  - ONS dimensions/options metadata
  - Nomis dataset metadata
- Build metadata normalisation map:
  - geography levels
  - time granularity
  - measure/indicator type
- Outputs:
  - `catalog_snapshot_v1`
  - `normalisation_rules_v1`

## Phase 1: Taxonomy + Elicitation (Weeks 3–5)
- Implement hybrid taxonomy entry:
  - thematic tiles
  - question-first entry
  - advanced structure filters
- Implement elicitation sequence engine (intent/place/period/measure/comparison)
- Outputs:
  - `taxonomy_engine_v1`
  - `elicitation_flow_v1`

## Phase 2: Data cards + Ranking (Weeks 6–8)
- Implement ranking service with weighted scoring and comparability penalties
- Generate explainable cards (`why_this` / `why_not`)
- Outputs:
  - `ranking_service_v1`
  - `data_card_renderer_v1`

## Phase 3: Graph linking (Weeks 9–10)
- Implement deterministic link rules (from `linking_rules.md`)
- Add edge scoring, link reason templates, and audit log
- Outputs:
  - `graph_linker_v1`
  - `related_dataset_api_v1`

## Phase 4: Accessibility + Governance hardening (Weeks 11–12)
- Enforce accessibility checks:
  - text alternatives
  - keyboard navigation
  - chart fallback tables
- Enforce AI-safe policies and guardrails
- Outputs:
  - `a11y_test_pack_v1`
  - `governance_controls_v1`

## Phase 5: Pilot and iterate (Weeks 13–16)
- Pilot with mixed personas:
  - novice policy users
  - analysts
  - AI-agent workflows
- Collect metrics and tune ranking weights
- Outputs:
  - `pilot_report_v1`
  - `weight_tuning_v1`

## Milestones
- M1: End-to-end prototype with 10+ DataPacks (done in research outputs)
- M2: API-backed live catalogue selection
- M3: A11y and governance gate pass in CI
- M4: Pilot success threshold met (see evaluation plan)

## Decision points
- D1: Confirm weight set for ranking formula
- D2: Confirm fallback behaviour for missing comparability metadata
- D3: Confirm publication model for AI-facing endpoint
