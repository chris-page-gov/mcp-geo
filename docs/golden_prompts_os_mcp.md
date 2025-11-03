# Golden Prompts — Model Evaluation with MCP Geo Server

**Facts (read first):**

- These prompts are designed to verify **MCP tool discovery**, **tool use**, **error handling**, and **result quality** across models (GPT‑5, GPT‑5 mini, Gemini 2.5 Pro) with **Copilot Coding Agent**.
- They assume your MCP server exposes tools with canonical names (subset): `os_places.by_postcode`, `os_places.search`, `os_places.nearest`, `os_names.find`, `os_features.query`, `os_maps.render`, `admin_lookup.containing_areas`, `admin_lookup.reverse_hierarchy`, `ons_data.query`, `ons_data.dimensions`, `ons_data.create_filter`, `ons_data.get_filter_output`, `ons_search.query`, `ons_codes.list`, `ons_codes.options`.
- Keep **web search ON** for freshness tests, but several sections **forbid web** to ensure the model uses MCP tools only.
- For governance validation, keep **Suggestions matching public code = Allow** (so you can see code referencing) during evaluation.

---

## 0) Environment check (run these first)

1. **Which model am I using?**  
   _Prompt:_ “Which model are you? Switch between **GPT‑5**, **GPT‑5 mini**, and **Gemini 2.5 Pro**, then summarise one difference in behaviour you expect for this task.”

2. **Confirm MCP connection**  
   _Prompt:_ “List the **MCP servers** available and the **tools** for server `os-mcp-stdio` (or `os-mcp-http`). For each tool, give: name, description, required/optional params, and a one‑line example call.”

3. **Policy sanity**  
   _Prompt:_ “Confirm that **web search is enabled**, **coding agent is enabled**, and **suggestions matching public code are allowed** in this workspace.”

---

## 1) Tool discovery & grounding (no web allowed)

> Say: “**Do not browse the web; use MCP tools only.**”

- _Prompt:_ “Explain in two sentences how you will answer geospatial questions **using only the MCP tools** you have. Then show a single **dry‑run** tool call for each of the following: UPRN lookup, USRN lookup, addresses by postcode, ward boundary geometry.”

- _Prompt:_ “Verify tool schemas by issuing **describe/introspect** calls if available. If not available, compile the schema from prior tool listing.”

**Expected:** The agent enumerates tools and produces parametrised, valid test calls without executing them (or executes with safe inputs, depending on client).

---

## 2) Core functional scenarios (prefer MCP tools; allow web only if MCP lacks data)

### A. Postcode & UPRN enrichment

Postcode to test: `SW1A1AA`  
_Prompt:_ “Return all addresses for SW1A 1AA via MCP tools. Output table: UPRN, address, classification, classificationDescription, localCustodianName, lat, lon. If a field absent use null.”

### B. Administrative containment

Point: `lat=51.5010, lon=-0.1416` (near Buckingham Palace)  
_Prompt:_ “List containing areas (smallest→largest) with id, level, name.”

### C. Street filtering within postcode

_Prompt:_ “List addresses in Gloucester Street, CV1 3BZ. If only postcode results available, filter client-side to those containing 'Gloucester Street'. Provide counts before/after.”

### D. Named place & nearby addresses

_Prompt:_ “Find named features near 51.5034,-0.1276 then list nearest addresses. Summarise top 5 names and number of addresses.”

### E. Ward boundary geometry

_Prompt:_ “Return Coventry ward boundaries as GeoJSON via MCP resources and summarise name + bbox per ward.”

### F. Static map descriptor

_Prompt:_ “Describe or render a static map for Downing Street (bbox around 51.503,-0.128) with address points. If rendering unsupported, supply descriptor and note limitation.”

**Expected:** Uses MCP tools, not web. Outputs structured tables/GeoJSON. States limitations explicitly.

---

## 3) Tool‑use enforcement (no web, must call tools)

- _Prompt:_ “**Do not browse the web.** Use MCP tools only. For **‘What addresses are in CV1 3BZ on Gloucester Street?’**, explain plan, perform calls and filtering.”

- _Prompt:_ “**Do not browse the web.** Use MCP tools only. ‘**Which administrative areas contain 51.5010,-0.1416?**’ Return ordered chain + confidence note.”

**Expected:** The agent calls road/USRN tools and avoids hallucination.

---

## 4) Error‑handling & robustness

- _Prompt:_ “Lookup postcode `ZZ99ZZ` (invalid). Provide graceful error + remediation suggestions (format validation, official sources).”

- _Prompt:_ “A tool returns **RATE_LIMITED**. Implement adaptive backoff in three bullet points.”

- _Prompt:_ “A tool returns a polygon with **SRID:27700** (BNG). Convert to **WGS84 (EPSG:4326)** and provide GeoJSON coordinates.”

---

## 5) ONS statistics (sample vs live)

- _Prompt:_ “List available ONS observation dimensions (sample). Then show first 2 observations for UK GDPV. Explain how live mode changes required parameters.”

## 6) Web‑freshness checks (web ON)

- _Prompt:_ “Using web search and MCP, list any recent changes to OS NGD or ONS Open Geography APIs in the last 30 days with citations.”
- _Prompt:_ “Cross‑check MCP result for Downing Street features with OS docs; explain mismatches (licensing, recency, generalisation).”

**Expected:** Provides citations and a short reconciliation.

---

## 6) Extensions (optional, if installed)

- _Prompt:_ “@Jira Create a ticket ‘OS‑MCP: add postcode → ward tool’ in project **DATA**, link it to repo `os-mcp`, and paste the prompt you used above.”

- _Prompt:_ “@Octopus or @Azure Trigger pipeline ‘os‑mcp‑deploy‑dev’ with variables `{ feature: 'ward_geojson' }`.”

**Expected:** Extension banner appears; the agent requests/uses the extension with the right scopes.

---

## 7) Acceptance rubric (score each model 1–5)

1. **Tool discovery** (lists tools & params correctly)  
2. **Correct tool use** (no hallucinated endpoints; valid params)  
3. **Result quality** (complete fields including enrichment, precise filtering)  
4. **Grounding** (admits unknowns; no fabrication)  
5. **Error handling** (clear recovery steps)  
6. **Governance** (no secret leakage; licensing caveats)  
7. **UX** (concise tables/GeoJSON; reproducible steps)

_Tip:_ Keep the same chat thread per model to compare behaviour; reset between sections to avoid cross‑contamination of context.
