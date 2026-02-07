# Phase 1 - Landscape scan (summary)
Version: 1.0.0  
Generated (UTC): 2026-02-07T08:11:25Z

## Purpose
Document ONS dataset discovery surfaces, selection failure modes, and comparator
patterns to inform MCP Geo dataset selection design.

## 1) ONS statistical output landscape (scope B)

### 1.1 What ONS publishes (dataset-relevant)

Primary statistical families:
- Economic statistics (GDP, GVA, productivity, trade, prices)
- Labour market (employment, unemployment, earnings, vacancies)
- Population and demography (estimates, migration, births/deaths, life expectancy)
- Census outputs (aggregated Census 2021 tables, topic summaries, small-area data)
- Health and social care (mortality, legacy indicators)
- Housing and planning (stock, affordability, construction)
- Crime and justice (Crime Survey for England and Wales)
- Environment and climate (emissions, land use)
- Education and skills (attainment, participation)
- Public finance (spending, taxation aggregates)

Derived indicators:
- Headline indices (CPIH, GDP chained volume measures)
- Composite measures and dashboards that aggregate multiple base datasets

Key observation:
ONS does not publish a single uniform "dataset type". Instead, it publishes
families of related statistical series across time series APIs, dataset landing
pages, XLS downloads, and interactive explorers. This fragmentation is the core
selection problem MCP Geo can solve.

### 1.2 ONS discovery mechanisms (pain points)

| Mechanism | Strength | Failure mode |
| --- | --- | --- |
| ONS website search | Broad coverage | Returns bulletins before data |
| Time series explorer | Precise | Requires prior knowledge |
| Dataset landing pages | Rich metadata | Inconsistent structure |
| APIs | Machine-usable | Poor discoverability |
| Census tools | Topic-led | Separate mental model |

Selection failure modes observed:
- Users pick a bulletin instead of a dataset
- Users mix incomparable vintages
- Users confuse provisional versus final releases
- Users choose national series when sub-national exists
- Users miss related datasets needed for context

## 2) Metadata standards and structures (ONS-first)

ONS uses SDMX-inspired concepts (dimensions, measures, attributes), a geography
hierarchy (OA → LSOA → MSOA → LA → Region → Nation), and revision flags. These are
not surfaced consistently or expressed as a unified concept scheme. This is a key
opportunity for a MCP Geo DataPack abstraction.

## 3) International comparators (selection and discovery)

- Eurostat: strong SDMX concept schemes, explicit dataset family grouping
- OECD: topic → indicator → dataset flow, strong narrative linkage
- UN Data/SDG: goal → target → indicator hierarchy (excellent elicitation scaffold)
- Statistics Canada: question-led landing pages and plain-language metadata

The best systems separate selection, interpretation, and analysis. ONS currently
mixes these surfaces.

## 4) Implications for MCP Geo (Phase 1 output)

Tiles should represent:
- Questions ("How has employment changed locally?")
- Decisions ("Is housing affordability worsening?")
- Indicators ("Inflation", "Net migration")

Cards must surface:
- Geography coverage
- Time coverage
- Revision status
- Comparability warnings
- "Why this dataset" explanation

Graphs should link:
- Base series ↔ derived indicators
- National ↔ sub-national
- Time series ↔ cross-sectional snapshots

## Evidence register
Stored at `research/ons_dataset_selection/evidence_register.csv`.

```csv
evidence_id,source_name,source_url,evidence_type,summary,relevance,notes
ons-site-structure,Office for National Statistics,https://www.ons.gov.uk,official_portal,Primary publication platform for UK official statistics,high,Search prioritises bulletins over datasets
ons-timeseries-api,ONS Time Series API,https://api.ons.gov.uk,tapi,Machine-accessible statistical series,high,Requires prior series knowledge
ons-census-2021,ONS Census 2021,https://www.ons.gov.uk/census,official_statistics,Aggregated census outputs and topic summaries,high,Separate interaction model from core ONS datasets
eurostat-discovery,Eurostat,https://ec.europa.eu/eurostat,international_comparator,SDMX-aligned dataset families and navigation,high,Strong related-dataset linking
oecd-data,OECD Data,https://data.oecd.org,international_comparator,Indicator-led statistical discovery,medium,Limited geography depth
un-sdg,UN SDG Data,https://sdgs.un.org/goals,elicitation_model,Goal-target-indicator hierarchy,medium,Excellent intent capture
statcan,Statistics Canada,https://www.statcan.gc.ca,international_comparator,Question-led statistical navigation,high,Strong plain-language metadata
sdmx-standard,SDMX,https://sdmx.org,standard,International statistical metadata standard,high,Complex but foundational
hci-stat-selection,HCI Statistical Selection Research,various,academic,Research on faceted and task-led data discovery,medium,Supports elicitation flows
misuse-official-stats,UK Code of Practice for Statistics,https://code.statisticsauthority.gov.uk,governance,Guidance on correct statistical use,high,Key for AI safeguards
```

## Status
Phase 1 complete.
