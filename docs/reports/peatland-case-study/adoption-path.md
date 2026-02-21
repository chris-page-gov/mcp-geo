# adoption-path.md

## Safe-by-design adoption path for “Apps → Answers” (UK public sector)

This model is built to be usable by non-technical leaders. It assumes **capabilities are governed services** (with defined inputs/outputs, permissions, logging, and provenance), and that MCP provides the standard way an AI host discovers and calls those capabilities. ([Model Context Protocol][1])

### Stage 0 — Define the public value and the boundaries (pre-work)

**Goal:** a bounded “question family” you can answer safely (e.g., place + boundary + statistic).
**Gate:** written scope + owners + “what we will not do”.
**Outputs:**

* a capability inventory outline (what capabilities exist / will exist)
* a draft transparency artefact approach (ATRS where relevant) ([GOV.UK][15])

---

### Stage 1 — Open data only (prove the pattern)

**Data:** public/open datasets (e.g., published stats, open geographies). ([data.gov.uk][18])
**Main risks:** hallucinated interpretation, wrong joins, wrong boundary definitions.
**Mandatory controls (“middle layer”):**

* capability catalogue + dataset catalogue (DCAT-style thinking helps) ([w3.org][6])
* provenance for every derived output (PROV-O or equivalent) ([w3.org][7])
* automated evaluation harness for “known questions” (regression tests)

**Exit criteria (what “good” looks like):**

* answers include sources + confidence/assumptions
* repeatable results on the same question set

---

### Stage 2 — Controlled internal data (non-personal) (prove governance)

**Data:** internal operational datasets that are not personal/sensitive, but still controlled (commercial, security, policy sensitivity).
**Main risks:** leakage, over-broad access, unsafe tool invocation.
**Mandatory controls:**

* role/attribute-based access to capabilities
* audit logs: who asked, what capability ran, what data was accessed, what outputs returned
* “secure-by-default” lifecycle controls aligned to NCSC guidance (design→ops) ([NCSC][12])
* LLM risk controls aligned to common threat categories (e.g., prompt injection) ([owasp.org][17])

**Exit criteria:**

* red-team style misuse tests passed (prompt injection attempts, data exfiltration attempts)
* logs are reviewable and actually reviewed

---

### Stage 3 — Personal data (prove legality + privacy controls)

**Data:** personal data under UK GDPR / DPA regime.
**Main risks:** unlawfulness, excessive processing, disclosure through outputs, “data use creep”.
**Mandatory controls:**

* lawful basis + minimisation + purpose limitation considerations per ICO AI & data protection guidance ([ICO][11])
* DPIA/TRA process proportionate to risk (organisational)
* disclosure control (aggregation thresholds, suppression, redaction)
* apply **Five Safes** as the governance spine (Safe Projects/People/Settings/Data/Outputs) ([GOV.UK][16])
* stronger output checking (especially for free text summaries)

**Exit criteria:**

* demonstrable minimisation (only the minimum data needed for the question family)
* demonstrable safe outputs (no re-identification risk under expected use)

---

### Stage 4 — Sensitive / high-stakes use (prove assurance and accountability)

**Data:** special category data, highly sensitive operational data, or use affecting rights/services.
**Main risks:** harm, bias, loss of trust, legal challenge, security compromise.
**Mandatory controls:**

* explicit human accountability, review, and appeal routes
* formal transparency artefacts (ATRS where it fits; explainability expectations) ([GOV.UK][15])
* continuous monitoring + incident response (NCSC lifecycle) ([NCSC][19])
* stricter separation between “assistant” and “decision-maker”

**Exit criteria:**

* measurable reduction in risk compared to baseline process
* demonstrable oversight and audit readiness

---

### Minimal reference architecture (text description)

* **Data sources** (OS/ONS/etc.) →
* **Data stewardship layer** (quality, identifiers, versioning; FAIR mindset) ([Nature][4]) →
* **Semantic mediation / middle layer** (joins, boundary logic, vocab mapping, aggregation, disclosure control) →
* **Policy enforcement** (authZ, redaction, rate limits, sensitivity labels) →
* **Provenance + audit store** (PROV-style lineage + immutable logs) ([w3.org][7]) →
* **MCP server** (capability catalogue + tool execution boundary) ([Model Context Protocol][1]) →
* **AI host** (interprets question; selects tools; presents answer with sources)
