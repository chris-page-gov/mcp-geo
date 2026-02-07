# ONS dataset selection at scale for MCP Geo (MCP-Apps UI + DataPack + graph cross-linking)
Version: 1.0.0  
Generated (UTC): 2026-02-07T08:11:25Z  
Scope: **B** (statistical + derived indicators; excludes text-only bulletins and methodology PDFs as selectable datasets)
Origin: Adapted from SeeLinks research outputs; updated for MCP Geo.

## Executive summary

This design proposes a **hybrid adaptive selection model** for ONS datasets in MCP Geo:
1. **Question-first elicitation** for ambiguous user intent,
2. **Standards-first structural checks** (dataset/edition/version/dimensions/options),
3. **Thematic familiarity** for trust and browseability,
4. **Explainable ranking** with explicit “why this dataset / why not others”.

The recommended interaction is:
- **Tile**: intent/question entry point,
- **Data card**: concise interpretation + caveats + comparability checks,
- **Graph**: related dataset pathways (derived, complementary, geography/time variants, quality context).

---

## 1) Landscape scan (ONS-first, comparator second)

### 1.1 ONS structures to support selection

From ONS developer documentation, datasets are organised as **dataset → edition → version → dimensions → options → observations** and are discoverable via API catalogue endpoints.  
This strongly supports a model where user intent is converted into dimension selections and validated before observation retrieval.

Observed implications:
- Selection must be dimension-aware, not title-only.
- Revision/version metadata is essential for safe comparison.
- API changes/deprecations require resilient abstraction in MCP Geo metadata.

### 1.2 ONS publication patterns relevant to selection

Observed patterns across ONS dataset pages:
- Release date and next release date are often visible,
- Historical versions may be exposed,
- Quality/revision notes can materially change interpretation,
- Some dataset families are available through multiple channels (ONS + Nomis, especially Census topic summaries).

### 1.3 International comparators

- **Eurostat**: strong SDMX structure and structure-query ergonomics.
- **OECD**: SDMX foundation plus improved search-oriented discovery in OECD Data Explorer.
- **UN SDG**: goal-target-indicator hierarchy and metadata API useful for elicitation patterns.
- **Statistics Canada**: stronger public-facing standards/methods framing for interpretation.

---

## 2) Comparative analysis of selection/discovery approaches (>=12)

Scoring scale: 1 (low) to 5 (high)

| # | Approach | Speed (novice) | Correctness | Explainability | AI-interoperability | Notes |
|---|---|---:|---:|---:|---:|---|
| 1 | ONS topical browse tree | 4 | 3 | 2 | 2 | Familiar, but can misroute cross-domain questions |
| 2 | ONS site keyword search | 5 | 2 | 1 | 1 | Fast, but often returns narrative first |
| 3 | ONS API catalogue browse (/datasets) | 3 | 4 | 3 | 5 | Strong machine compatibility |
| 4 | ONS dimension-option drill-down | 2 | 5 | 4 | 5 | Highest structural precision |
| 5 | ONS release-led navigation | 3 | 4 | 3 | 3 | Good for freshness-aware users |
| 6 | Nomis query + SDMX dimensions | 3 | 4 | 3 | 5 | Good for labour/census workflows |
| 7 | Eurostat SDMX structure-first | 2 | 5 | 4 | 5 | Excellent standards fidelity |
| 8 | OECD search-led + SDMX backend | 4 | 4 | 3 | 4 | Good hybrid usability |
| 9 | UN SDG goal-target-indicator tree | 4 | 3 | 4 | 4 | Strong elicitation scaffold |
| 10 | Question-first elicitation tree | 5 | 4 | 5 | 4 | Best novice performance |
| 11 | Faceted narrowing with dynamic ranking | 4 | 5 | 4 | 5 | Strong for exploratory analysis |
| 12 | Explainable recommendation ranking | 4 | 5 | 5 | 5 | Best for “why this / why not others” |
| 13 | Persona-specific quick paths | 5 | 3 | 3 | 2 | Helpful shortcuts, risk of oversimplification |

**Conclusion**: the highest-performing pattern is a **hybrid** of #10 + #11 + #12 with structural checks from #4.

---

## 3) Taxonomy engineering (3 competing schemes + trade-offs)

See `taxonomy_options.json` for full machine-readable definitions.

### Option A: Thematic official ONS tree
- Best for familiarity and trust.
- Risk: ambiguity on cross-cutting questions.

### Option B: Standards-first SDMX concept scheme
- Best for precision and interoperability.
- Risk: steep learning curve for non-specialists.

### Option C: Question-first elicitation tree
- Best for novice correctness and explainability.
- Risk: requires careful ranking calibration.

### Recommended Option D (hybrid adaptive)
- Multi-entry (question/theme/advanced structure),
- Weighted ranking with comparability risk penalty,
- Mandatory explanation and caveat outputs.

---

## 4) Flow design: ambiguous query to justified dataset

### End-to-end example (mandatory)

**Vague query**  
“Is housing getting worse where I live?”

**Elicitation sequence**  
1. Which place? (LA / ward / region / nation)  
2. Which housing pressure? (affordability, rent, overcrowding, homelessness risk proxy)  
3. Which period? (last 12 months / 5 years / since 2019)  
4. Which lens? (trend only / compare to peers / inequality split)

**Dataset choice (ranked)**  
1. House price-to-earnings ratio (primary)  
2. Private rental prices index (context)  
3. Census overcrowding indicators (structural context)

**Data card output**  
- Why selected: direct fit to affordability intent, local geography availability, stable release cycle.  
- Why not others: alternative datasets not comparable in geography/frequency or concept.  
- Caveats: ratio denominator sensitivity, revisions, and concept differences.

**Graph paths**  
- affordability ratio → earnings denominator (`methodological_dependency`)  
- affordability ratio → rental index (`complementary_context`)  
- affordability ratio → overcrowding (`complementary_context`, non-causal)

---

## 5) Schema and DataPack design

Implemented in:
- `ons_datapack_schema.json`
- `sample_datapacks/*.json` (11 files)

Design features:
- Enforced provenance fields on all data-bearing objects,
- Mandatory recommendation-quality fields:
  - `fitness_for_use_score` (0–100)
  - `confidence` (`high|medium|low`)
  - `explainability_note`
  - `known_limitations`
  - `comparability_warnings`
- AI-safe controls:
  - comparability checks,
  - revision/release visibility,
  - prohibition of unqualified ranking.

---

## 6) Link model for graph exploration

Implemented in `linking_rules.md` with:
- deterministic rule order,
- comparability safety gate,
- typed edges (derived, complementary, methodological dependency, quality context, etc.),
- link scoring and explainability templates,
- accessibility and governance controls.

---

## 7) Explicit answers to the 10 research questions

### Q1. What dataset families exist and what question types does each answer?
Families include economy, labour market, prices/inflation, population/migration, housing, health outcomes, crime, productivity, and census-derived indicators.  
Each family maps to standard question intents such as trend, comparison, distribution, and pressure/risk context.

### Q2. Which metadata fields most improve correct dataset selection?
Top fields: concept/intent tags, geography coverage, time coverage/granularity, revision status, latest/next release dates, comparability warnings, and quality notes.

### Q3. What are common selection failure modes and how can UI reduce them?
Failure modes: wrong concept, wrong geography level, incompatible time basis, provisional vs final confusion, and causality overclaiming.  
Mitigations: elicitation questions, structured comparability checks, “why not others”, and mandatory caveat display.

### Q4. Which grouping model(s) optimise speed and correctness for different users?
- Novice: question-first + faceted narrowing
- Expert/AI: standards-first structure
- Mixed audience: hybrid adaptive model (recommended)

### Q5. What elicitation sequence converts vague intent to precise dataset choice?
A 4–6 step sequence: intent → place → period → measure type → comparison need → ranked candidates with explanations.

### Q6. Which graph/linking patterns are most useful for exploration?
Most useful: derived-from, complementary-context, same-measure-different-geography/time, quality/revision context, methodological dependency.

### Q7. How should tiles map to cards, chart templates, and related datasets?
Tiles represent intent; cards provide justifications + caveats; chart templates are pre-bound to safe axes/fields; graph links expose related datasets with reasons.

### Q8. What safeguards prevent misuse/misinterpretation by humans and AI?
Mandatory comparability checks, explicit uncertainty and revisions, confidence/fitness scoring, non-causal language guardrails, and provenance visibility.

### Q9. What minimal DataPack fields enable interoperability and future-proofing?
Stable IDs, semantic versioning, timestamps, structural metadata pointers, provenance block, comparability flags, and explainability fields.

### Q10. What evaluation metrics prove the approach works?
Task success, time-to-correct-dataset, top-1/3 selection accuracy, comparability-error rate, caveat visibility compliance, accessibility pass rate, and governance audit completeness.

---

## 8) Recommendations (traceable)

- **rec-01** Build canonical ONS/Nomis catalogue ingestion with structural metadata.
- **rec-02** Treat dataset/edition/version as first-class IDs.
- **rec-03** Implement SDMX-style dimension and codelist abstraction.
- **rec-04** Query observations only after dimension completeness checks.
- **rec-05** Use question-first elicitation + dynamic facets.
- **rec-06** Implement rate-limit-aware caching and release-window scheduling.
- **rec-07** Enforce accessible chart + text alternatives by default.
- **rec-08** Expose quality, revision, and uncertainty on every card.
- **rec-09** Enforce AI-safe guardrails and caveat rendering.
- **rec-10** Version all DataPacks and keep endpoint deprecation map.
- **rec-11** Add governance telemetry and periodic quality reviews.
- **rec-12** Use comparator patterns (Eurostat/OECD/UN/StatCan) selectively, not wholesale.

Each recommendation is cross-referenced in `evidence_register.csv`.

---

## 9) Risks and mitigations

1. **Metadata drift** → nightly schema checks + alerting  
2. **Endpoint retirement** → deprecation registry and fallback mappings  
3. **Comparability misuse** → hard validation gates + visible warnings  
4. **Accessibility regressions** → CI checks against WCAG criteria  
5. **Ranking opacity** → exposed score components + audit logs

---

## 10) Deliverable checklist status (this run)

- report.md ✅  
- evidence_register.csv ✅  
- taxonomy_options.json ✅  
- ons_datapack_schema.json ✅  
- sample_datapacks/ (>=10) ✅ (11)  
- linking_rules.md ✅  
- roadmap.md ✅  
- evaluation_plan.md ✅  
- completion.json ✅ (generated with required marker)
