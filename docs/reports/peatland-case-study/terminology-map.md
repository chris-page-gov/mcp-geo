# terminology-map.md

[![Celebrating Claude Shannon - IEEE Spectrum](https://tse3.mm.bing.net/th/id/OIP.eRWbeEQpxp0xtz3vIhZJUAHaFj?pid=Api)](https://spectrum.ieee.org/celebrating-claude-shannon?utm_source=chatgpt.com)

## From Apps → Answers: a terminology map for connecting public-sector data to AI

### 1) The core idea in one paragraph (non-technical)

Public-sector organisations are **data rich**, but most of that value is locked behind specialist tooling, bespoke apps, and “ask the analyst” workflows. Your **Apps → Answers** framing is a move from building more interfaces to building a **governed middle layer** that turns raw datasets into reliable, reusable **information services**, and then exposes those services as **capabilities** that an intelligent system (human or AI) can discover and use. MCP is relevant because it standardises how an AI host “sees” and calls those capabilities. ([Model Context Protocol][1])

### 2) Important nuance: “information” means two different things

* In **Shannon information theory**, “information” is about **uncertainty reduction and transmission efficiency**, not semantic meaning. It’s foundational for digital systems, but it does not tell you how data becomes *meaningful* for a user’s question. ([people.math.harvard.edu][2])
* In your talk, “information” is closer to **meaningful, structured, contextualised data** that supports decisions and answers (the sort of “data-to-use” transformation Ackoff popularised in DIKW discussions). ([faculty.ung.edu][3])

### 3) A usable conceptual stack (observation → answers)

This stack gives you “academic-ish” labels without losing the room:

1. **Observation / measurement** (data capture)
   *Sensing, surveying, administrative recording, remote sensing, transactions*

2. **Data management & stewardship** (wrangling / quality)
   *ETL/ELT, cleaning, metadata, identifiers, versioning*
   → **FAIR** is a widely used stewardship lens, and explicitly emphasises machine use, not only human reuse. ([Nature][4])

3. **Semantic mediation / interoperability** (your “middle layer” heartland)
   *mapping concepts across datasets; aligning boundary definitions; joining; aggregating; unit conversions; canonical identifiers*
   → The “Semantic Web” vision is a classic reference point for “data meaningful to computers” via shared vocabularies/ontologies. ([Scientific American][5])
   → Catalog interoperability and discoverability are often framed through **DCAT** (data catalog vocabulary). ([w3.org][6])

4. **Provenance, audit, and trust infrastructure**
   *where did this come from; what transformation steps were applied; can we reproduce it*
   → W3C **PROV-O** is a standard way to represent and exchange provenance. ([w3.org][7])

5. **Capability interface layer** (how intelligence accesses the middle layer)
   *capability catalogue; tool descriptions; input/output contracts; limits; permissions; safe defaults*
   → MCP is explicitly an open protocol for connecting LLM apps to external tools and data sources. ([Model Context Protocol][1])

6. **Intelligence layer** (human + AI)
   *interpreting questions; selecting capabilities; verifying outputs; communicating uncertainty*

### 4) “Chris term” → “Academic/standards term(s)” mapping table

| Chris term                        | Closest academic / standards term(s)                                         | Why it fits                                                   | Common pitfall (good warning slide)                                                        |
| --------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| “Apps → Answers”                  | Question-answering / decision support; “data products”; information services | Shifts value from UI to reusable information capabilities     | Treating it as “chat UI” rather than governed services                                     |
| “Middle layer”                    | Semantic mediation; interoperability layer; semantic layer; data integration | It’s the transformation from data → interpretable information | Trying to solve semantics with only ETL/joins                                              |
| “Transform data into information” | DIKW-style transformation (contested but useful as a narrative device)       | Communicates value-add steps and increasing usefulness        | DIKW can imply a neat linear ladder; reality is iterative and messy ([faculty.ung.edu][3]) |
| “Capability catalogue”            | Data catalog + service registry; machine-readable API/tool descriptions      | Discoverability is required for automation                    | Catalogues rot unless tied to operations + ownership                                       |
| “Connect intelligence to data”    | Human–AI teaming; tool-augmented LLMs; RAG + tool use                        | Frames AI as a “user” of governed capabilities                | Over-trusting model outputs without provenance                                             |
| “Evidence-first answers”          | Provenance; reproducibility; auditability                                    | Core to public-sector trust                                   | Logging without meaningfully reviewable records                                            |
| “Boundaries & definitions”        | Ontologies/vocabularies; reference data; canonical identifiers               | Geo is full of semantic mismatches                            | Assuming “same label = same concept”                                                       |
| “Safe-by-design”                  | Secure-by-design; privacy-by-design; governance controls                     | Matches UK delivery expectations                              | Bolting on controls after the demo works                                                   |

### 5) A practical research question set (for your report and future prompts)

1. What is the minimum **semantic contract** a capability must publish (inputs, outputs, assumptions, limitations, provenance hooks)?
2. What are the smallest set of **interoperability patterns** needed for UK place-based questions (boundaries, addresses/UPRNs, statistical geographies)?
3. How do we represent and enforce **policy controls** at the capability boundary (permissions, redaction, aggregation, disclosure control)?
4. What is the most “auditable” representation of an answer: text only, or text + structured result + provenance bundle?
