# Golden Prompts — GPT‑5 / GPT‑5 mini / Gemini 2.5 Pro with OS‑MCP

**Facts (read first):**
- These prompts are designed to verify **MCP tool discovery**, **tool use**, **error handling**, and **result quality** across models (GPT‑5, GPT‑5 mini, Gemini 2.5 Pro) with **Copilot Coding Agent**.
- They assume your MCP server exposes tools broadly like: `os.uprn.lookup`, `os.usrn.lookup`, `os.address.by_postcode`, `os.boundary.ward_geojson`, `os.map.render` (rename in the prompts if your tool names differ).
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

**Expected:** The agent enumerates tools and produces parameterised, valid test calls without executing them (or executes with safe inputs, depending on client).

---

## 2) Core functional scenarios (prefer MCP tools; allow web only if MCP lacks data)

### A. UPRN lookups (exact IDs)
UPRNs to test: `100023336959, 100023338803, 100023338946, 100023371397`  
_Prompt:_ “Return the **full records** for these UPRNs via MCP tools. Output a concise table (UPRN, address, building type, coordinates, source). If a field is missing, state ‘null’ rather than guessing.”

### B. USRN lookups
USRNs to test: `20000185, 8400511, 20000002, 8400037, 48003642`  
_Prompt:_ “Look up each **USRN** and report: name, road class, authority, geometry type/length. Include a one‑sentence caveat about licensing where applicable.”

### C. Postcode and locality
_Prompt:_ “List all **addresses** in **Gloucester Street, CV1 3BZ**. Include UPRN, address line, and geo‑point. If your tool works by postcode, filter to the street in post‑processing.”

### D. Named place & buildings
_Prompt:_ “List **buildings on Downing Street, London** with UPRN (if available), building type, and polygon centroid. Give results only from MCP tools.”

### E. Boundary geometry as GeoJSON
_Prompt:_ “Return **Coventry ward boundaries** as **GeoJSON** via MCP and summarise the count, names, and bounding boxes.”

### F. Quick map artefact (if your server supports it)
_Prompt:_ “Render a simple **static map** of **Downing Street buildings** with outlines and labels. Return a PNG or an HTML tile URL. If not supported, state that clearly.”

**Expected:** Uses MCP tools, not web. Outputs structured tables/GeoJSON. States limitations explicitly.

---

## 3) Tool‑use enforcement (no web, must call tools)

- _Prompt:_ “**Do not browse the web.** Use MCP tools only. For **‘What roads are in CV1 3BZ?’**, explain the plan, then perform the calls. If a result requires a secondary filter, show it.”

- _Prompt:_ “**Do not browse the web.** Use MCP tools only. ‘**What is the USRN of Gloucester Street CV1 3BZ?**’ Return a single USRN and a confidence note.”

**Expected:** The agent calls road/USRN tools and avoids hallucination.

---

## 4) Error‑handling & robustness

- _Prompt:_ “Lookup UPRN `999999999999` (deliberately invalid). Provide a **graceful error** with remediation suggestions (e.g., ‘validate length’, ‘check dataset coverage’).”

- _Prompt:_ “The boundary service returns **HTTP 429**. Implement backoff and retry guidance for me in three bullet points.”

- _Prompt:_ “A tool returns a polygon with **SRID:27700** (BNG). Convert to **WGS84 (EPSG:4326)** and provide GeoJSON coordinates.”

---

## 5) Web‑freshness checks (web ON)

- _Prompt:_ “Using web search in addition to MCP, list any **recent changes** to **OS NGD** or **ONS Open Geography** APIs in the last 30 days and cite the sources.”

- _Prompt:_ “Cross‑check the MCP result for **Downing Street buildings** with any **official OS doc** you find. If there’s a mismatch, explain likely reasons (licensing, recency, generalisation).”

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
3. **Result quality** (complete fields, precise filtering)  
4. **Grounding** (admits unknowns; no fabrication)  
5. **Error handling** (clear recovery steps)  
6. **Governance** (no secret leakage; licensing caveats)  
7. **UX** (concise tables/GeoJSON; reproducible steps)

_Tip:_ Keep the same chat thread per model to compare behaviour; reset between sections to avoid cross‑contamination of context.
