# UK Public Sector AI Community Documentation Set (MCP Geo)

## Purpose

This documentation set explains what was discovered and delivered in `mcp-geo`, in language suitable for:

- novice users
- apprentices with early-stage coding knowledge (approximately GCSE level)
- technical reviewers and delivery leads

This set is descriptive and evidence-based. It focuses on this repository and excludes implementation details from git submodules.

## How To Read This Set

1. Start with [01_overview_for_novices.md](01_overview_for_novices.md)
2. Read [02_origin_story_and_acknowledgements.md](02_origin_story_and_acknowledgements.md)
3. Use [03_architecture_and_components.md](03_architecture_and_components.md)
4. Walk through [04_detailed_timeline_repo_and_ecosystem.md](04_detailed_timeline_repo_and_ecosystem.md)
5. Use [14_evidence_and_report_index.md](14_evidence_and_report_index.md) when you need source artifacts

```mermaid
flowchart LR
    A["Audience"] --> B["Plain-language overview"]
    B --> C["Origins and timeline"]
    C --> D["System and standards"]
    D --> E["Harness and troubleshooting"]
    E --> F["Evaluation and next-stage planning"]
```

## Document Map

- [00_delivery_plan.md](00_delivery_plan.md)
- [01_overview_for_novices.md](01_overview_for_novices.md)
- [02_origin_story_and_acknowledgements.md](02_origin_story_and_acknowledgements.md)
- [03_architecture_and_components.md](03_architecture_and_components.md)
- [04_detailed_timeline_repo_and_ecosystem.md](04_detailed_timeline_repo_and_ecosystem.md)
- [05_reproducible_development_environment.md](05_reproducible_development_environment.md)
- [06_standards_clients_and_tooling_evolution.md](06_standards_clients_and_tooling_evolution.md)
- [07_harness_permissions_and_debugging_journey.md](07_harness_permissions_and_debugging_journey.md)
- [08_user_question_patterns_and_solution_progress.md](08_user_question_patterns_and_solution_progress.md)
- [09_effectiveness_evaluation.md](09_effectiveness_evaluation.md)
- [10_codex_usage_time_and_token_statistics.md](10_codex_usage_time_and_token_statistics.md)
- [11_bduk_pilot_extension_requirements.md](11_bduk_pilot_extension_requirements.md)
- [12_data_expansion_rbac_abac_and_governance.md](12_data_expansion_rbac_abac_and_governance.md)
- [13_future_direction_for_mcp_in_uk_public_sector.md](13_future_direction_for_mcp_in_uk_public_sector.md)
- [14_evidence_and_report_index.md](14_evidence_and_report_index.md)

## Publication Output

Prism-ready LaTeX output is provided in:

- [prism/main.tex](prism/main.tex)
- [prism/references.bib](prism/references.bib)
- [prism/sections/](prism/sections/)

## Scope Boundaries

- Included: this repository's code, docs, tests, reports, troubleshooting records, release history
- Excluded: submodule implementation internals
- External events included: MCP standards evolution and selected host/client release milestones that materially affected delivery
