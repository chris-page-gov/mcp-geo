---
aliases: [MCP resources, prompt templates, LandIS resources]
tags: [mcp, resources, prompts, templates, landis]
---

# Resources and Prompts

## MCP Resources

MCP resources expose **static but essential context** — schema, glossaries, provenance, and licensing — that can be retrieved without side effects. They are the "reference library" of the LandIS MCP server.

### Core Resource URIs

| Resource URI | Content |
|---|---|
| `landis://catalog/products` | Product list and coverage — all available layers |
| `landis://docs/soil-data-structures` | Join guidance — the MUSID → series → horizon chain |
| `landis://docs/soil-classification` | Soil classification guide |
| `landis://docs/soil-information-policy` | Licensing and governance context |
| `landis://docs/soilscapes-applications` | Soilscapes use cases + metadata brochure |
| `landis://schemas/natmapvector` | Field definitions: MUSID, legend fields |
| `landis://schemas/horizon-fundamentals` | Field dictionary and QA semantics |
| `landis://schemas/horizon-hydraulics` | Field dictionary and QA semantics |
| `landis://licence/current` | Pointer to the open access licence at portal.landis.org.uk |

### Why Resources Matter

Resources enable AI systems to:
- Understand field meanings before querying (reducing hallucination risk)
- Cite authoritative schema definitions in outputs
- Reference licence terms directly
- Load classification guides for code → description translation

See [[Glossary]] for a human-readable version of key terms.

---

## MCP Prompts

MCP prompts are **discoverable prompt templates** exposed by the server. They encode best practice into reusable, structured queries — ensuring that critical caveats (scale limitations, field verification requirements) are always present.

### Prompt Templates

#### Route Constraint Screening
```
"Given a polyline, summarise soil-related construction constraints
and generate a verification checklist."
```
**Embeds:** Wetness, HOST, corrosion, shrink-swell layers; Soilscapes limitation warning; "not a substitute for ground investigation" statement.
**Primary users:** [[Stakeholders#🔧 Utilities and Infrastructure Planners|Utility planners]], telecoms engineers

---

#### Local Planning Evidence Pack
```
"Given an administrative area, produce a soil constraints briefing
with map-layer summaries and caveats."
```
**Embeds:** NATMAP thematic summaries; scale limitation; "not for site-level decisions" warning; ALC wetness context.
**Primary users:** [[Stakeholders#🏗️ Local Authority Planners and Engineers|Local authority planners]]

---

#### Farm Advisory Summary
```
"Given a holding boundary, summarise soilscape types, drainage/wetness
risks, and crop-available-water implications."
```
**Embeds:** Soilscapes breakdown; drainage class; CAW values; workdays context; plain-language framing.
**Primary users:** [[Stakeholders#🌾 Agricultural Advisors and Land Managers|Agricultural advisors]]

---

#### Catchment Vulnerability Assessment
```
"Given a catchment polygon, summarise HOST, drainage, wetness,
and pesticide leaching indicators."
```
**Embeds:** HOST distribution; wetness class; pesticide leaching vulnerability; NSI monitoring context; appropriate uncertainty statements.
**Primary users:** [[Stakeholders#💧 Hydrology and Flood Teams|Catchment managers]], EA flood teams

---

#### Soil Education Explainer
```
"Explain local soils for a non-specialist audience, highlighting
uncertainty and what field checks are needed."
```
**Embeds:** Soilscapes plain-language class description; habitat associations; "what your soil means for your garden/land"; "this is a generalised map — local conditions may vary" statement.
**Primary users:** [[Stakeholders#🏫 Education and Public|Public, schools, NGOs]]

---

#### Carbon and Climate Screening
```
"Given a land parcel, screen for high-carbon soils and potential
peatland requiring protection."
```
**Embeds:** NATMAP Carbon stock by depth; wetness class (wet soils = higher carbon retention); peat flag; GHG Inventory context; "verify with peat depth survey" caveat.
**Primary users:** [[Stakeholders#🏛️ Government and Policy Teams|Defra policy teams]], land managers

---

## Embedding Best Practice

> [!important] Caveat Embedding Rule
> Every prompt template automatically includes the Soilscapes limitation wording and a "not a substitute for field investigation" warning where applicable. This is not optional — it is hardcoded into the prompt structure.

This design means users do not need to learn LandIS's limitations the hard way. The system teaches responsible use through its outputs.

---

## App Patterns

The combination of tools + resources + prompts supports these application patterns:

- **Map-based exploration** with geography selector and soil card view
- **Route analysis workbench** for linear infrastructure
- **"Soil knowledge card" views** (soilscape / association / series)
- **Dashboard summaries** for a selected administrative area
- **Report generator** with explicit provenance fields and caveats

---
*← [[00 - Home|Home]]  |  See also: [[MCP Overview]], [[Primitive Tools]], [[Derived Semantic Tools]], [[Stakeholders]]*
