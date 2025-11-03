# MCP Server Description

## Prompt

I want to use Codex to create the MCP server described in the documents [Mapping Ordnance Survey & ONS APIs to the Model Context Protocol (MCP)](<Mapping Ordnance Survey & ONS APIs to the Model Context Protocol (MCP).docx>) + [Documentation collection task](<Documentation collection task.docx>) and ensure coverage of all the data described in the documentation collection.

It seems that I need to break this down into tasks, like feature requests. Can you create a complete set of these that I can use Codex to create the application or is there a better way for me to use an agent to create it

## Response

Great idea. Here’s a clean, “drop‑in to Codex” backlog you can paste into an issue tracker (or hand to an agent) to build the MCP server end‑to‑end, plus a quick note on when a higher‑level “builder agent” is better than plain feature tickets.

## Recommended approach

* **If you want maximum control:** use the ticket set below with Codex (or your fav code agent) and run sprint‑by‑sprint.
* **If you want fastest path to working scaffolding:** kick off a “Builder Agent” that first generates the full server skeleton (MCP handshake, tool/router, auth, tests, docs) and then consumes the tickets below one by one. I’ve included a ready‑made *Bootstrapping Task 0* to do exactly that.

---

## Backlog (Epics → Stories with acceptance criteria)

### EPIC A — Core MCP server & playground

#### **A0. Bootstrap MCP server skeleton**

* **Goal:** Scaffolding for an MCP server with tools, resources, and a small playground chat (CLI or minimal web).
* **Deliverables:**

  * Repo layout (`/server`, `/tools`, `/resources`, `/playground`, `/tests`, `/infra`).
  * MCP protocol handshake, `tools/list`, `tools/call`, `resources/list`, structured outputs.
  * `.env.example` for keys; typed config loader; Dockerfile + devcontainer.
* **Acceptance:** `npm run dev` (or `uv run`/`poetry run`) starts server; `/healthz` returns OK; `tools/list` shows a placeholder tool.

#### **A1. Observability & DX**

* Structured logging, request/response tracing (with PII‑safe redaction), per‑tool latency counters; simple “tool call transcript” panel in playground.
* **Acceptance:** Logs include correlation ID; test proves redaction; playground can show last N tool calls.

#### **A2. Error model & pagination**

* Normalize errors to `{ isError: true, code, message }`.
* Support paging/limits consistently across tools; return `nextPageToken` where applicable.
* **Acceptance:** Contract tests verify uniform error shape and paging across tools.

---

### EPIC B — Ordnance Survey (OS) tools (enriched)

#### **B1. `os_places.*` (AddressBase geocoder)**

* **Subtools:**

  * `os_places.search(text)`
  * `os_places.by_postcode(postcode)`
  * `os_places.by_uprn(uprn)`
  * `os_places.nearest(lat, lon)`
  * `os_places.within(polygon|bbox|radius)`
* **I/O:** Return **structured JSON**: `{ uprn, address, lat, lon, classification, local_custodian_code, … }`.
* **Acceptance:** Given known inputs (incl. SW1A 2AA), returns UPRNs plus enrichment fields (`classificationDescription`, `localCustodianName`); rate‑limit handling; no secrets leak.

#### **B2. `os_linked_ids.get(identifier)`**

* Input can be UPRN/USRN/TOID; auto‑detect or `type` param.
* Output: `{ input: {...}, links: { uprns:[…], usrns:[…], toids:[…] } }`.
* **Acceptance:** Round‑trip tests: USRN → UPRNs and UPRN → USRN for a known street.

#### **B3. `os_features.query(collection, filters, geometry)`**

* Wrap OS NGD OGC Features.
* Support `bbox`, `polygon`, attribute filters, limit/offset; return **GeoJSON FeatureCollection** with trimmed properties.
* **Acceptance:** Query buildings/roads by bbox; returns valid GeoJSON; handles pagination; 100‑item default cap.

#### **B4. `os_names.*` (gazetteer)**

* `os_names.find(text)` and `os_names.nearest(lat, lon)` returning place name + coords.
* **Acceptance:** “Downing Street” returns sensible matches with coordinates.

#### **B5. `os_maps.render` & `os_vector_tiles.descriptor` (utility)**

* **Maps:** Static image render with optional overlays (points/lines/polygons/labels).
* **Vector:** Provide a ready‑to‑use style + source descriptor for client map displays.
* **Acceptance:** Render PNG for a bbox; vector style loads in a sample HTML viewer.

#### **B6. OS downloads & code lists (resources)**

* Ship small **static resources**: address classification codes, custodian code → LA name, a tiny sample of boundaries if helpful.
* **Acceptance:** `resources/list` shows code lists; tests reference them when interpreting `os_places` results.

---

### EPIC C — Administrative geography & lookups

#### **C1. `admin_lookup.containing_areas(lat, lon)`**

* Returns hierarchy (OA/LSOA/MSOA/Ward/District/County/Region/Nation) with names + codes.
* Implementation options: fast path via cached polygons or external lookup; unify outputs.
* **Acceptance:** Known point returns expected GSS codes; performance budget < 300ms with warm cache.

#### **C2. Boundary resources**

* Store key boundaries (e.g., Wards, Local Authorities) as static resources (compressed GeoJSON) with version tags and metadata.
* **Acceptance:** `resources/list` shows boundary packs with size, SRID, vintage; smoke test to load and spatially query.

---

### EPIC D — ONS Statistics (beta API) tools & discovery

#### **D1. `ons_data.get_observation(dataset, area_code, time, dims={})`**

* One‑shot observation fetch returning `{ value, unit, dataset, area, time, notes }`.
* **Acceptance:** Works for a canonical population dataset; returns numeric value and provenance.

#### **D2. `ons_data.create_filter(...)` + `ons_data.get_filter_output(filter_id, format)`**

* POST filter → poll → fetch CSV/XLSX/JSON; stream large results as a **resource**.
* **Acceptance:** Generates a small table (e.g., population by age bands for a ward) and exposes it as JSON (future: downloadable CSV/XLSX) while maintaining coverage tests.

#### **D3. Discovery helpers**

* `ons_search.query(term, type=dataset)`
* `ons_codes.list(id|dimension)` & `ons_codes.options(id, edition)`
* **Acceptance:** Searching “population estimates” surfaces the expected dataset; code‑list endpoints return valid options.

---

### EPIC E — Conversational normalization & examples

#### **E1. Normalization guide (prompt + server hints)**

* Provide a **server‑side guide** the model can read: how “list”, “map”, “compare”, “nearby” map to tool calls; when to summarize large results; how to join OS (geometry) with ONS (stats).
* **Acceptance:** Example conversations in `/examples` show the intended tool sequences.

#### **E2. Worked examples & golden tests**

* Scripts that assert:

  * “List UPRNs in SW1A 2AA and mark residential/commercial.”
  * “Which ward is this point in, and what’s its population?”
  * “Show a map of roads intersecting Oxford boundary.”
* **Acceptance:** Golden outputs updated via snapshot tests; maps rendered to `/artifacts`.

---

### EPIC F — Security, auth, and limits

#### **F1. Secrets management**

* Read OS keys from env/secret store; never echo in logs; signed outbound requests where required; optional OAuth2 path.
* **Acceptance:** Unit test proves keys redacted; secret scan (pre‑commit) blocks accidental commits.

#### **F2. Usage governance**

* Per‑tool rate limiting; circuit breakers; graceful degradation.
* **Acceptance:** Hammer tests show 429 throttling; server recovers cleanly.

---

### EPIC G — Packaging, CI, docs

#### **G1. CI/CD**

* Lint, type‑check, unit/integration tests, image build, SBOM; GitHub Actions badges.
* **Acceptance:** PR triggers full pipeline; release tags publish container image.

#### **G2. Developer docs**

* `/docs`: quickstart, environment, tool catalog (I/O schemas), example queries, troubleshooting.
* **Acceptance:** New dev can run the stack in <10 minutes.

---

## Ticket templates (ready to paste)

### Example tool ticket (B1 `os_places.by_postcode`)

**Summary:** Implement `os_places.by_postcode(postcode)` returning `{uprn, address, lat, lon, classification, local_custodian_code}`.
**Details:**

* Validate UK postcode; normalize spacing/case.
* Call OS Places postcode endpoint; map raw fields to our schema; include provenance (source name, timestamp).
* Redact keys; add retry with backoff; cap results to 200 + pagination token.
  **Acceptance Criteria:**

1. `by_postcode("SW1A 2AA")` returns ≥1 UPRN with coordinates.
2. Classification codes are present & documented via resource.
3. Error for invalid postcode (`isError=true, code="INVALID_INPUT"`).
4. Unit + contract tests pass.

#### Example ONS ticket (D1 `ons_data.get_observation`)

**Summary:** Implement one‑shot observation fetch.
**Details:**

* Inputs: `dataset`, `area_code`, `time`, optional dimension map.
* Resolve latest edition/version; build observation query; return `{value, unit, dataset, area, time, dims, notes}`.
* Helpful error messages when a code/time is invalid; include list of valid options in `hints`.
  **Acceptance:**

1. Population for a known ward/year returns numeric `value`.
2. Invalid area returns `isError=true` with `hints.options` populated.
3. Contract test snapshot updated.

---

## Bootstrapping Task 0 (for a Builder Agent)

> **Objective:** Generate a production‑ready MCP server scaffold with TypeScript (or Python) including handshake, tool router, resource registry, config, logging, tests, Docker, and a minimal playground UI. Create stubs for tools listed in Epics B–D and resources in C. Include CI workflow and `/docs` with a tool catalog and example conversations. Then iterate through the backlog, turning stubs into full implementations, keeping I/O **strictly typed** and **structured**.

---

## Suggested repo layout

```txt
/server
  /mcp           ## handshake, tool registry, resource registry
  /tools         ## os_places, os_linked_ids, os_features, os_names, os_maps, admin_lookup, ons_data, ons_search, ons_codes
  /resources     ## code lists, boundaries, samples (versioned)
/playground      ## tiny chat UI + call transcript
/tests           ## unit, contract, golden, hammer tests
/infra           ## Dockerfile, compose, k8s manifests (optional)
/docs            ## quickstart, tool catalog, examples
.env.example
```

---

## Definition of Done (project)

* All tools in Epics B–D implemented with typed inputs/outputs, pagination, enrichment (where applicable), and uniform error model.
* Static resources (code lists, boundaries) are versioned, documented, enriched with caching headers and provenance timestamps, and discoverable via `resources/list`.
* Golden scenarios in EPIC E pass, producing both textual answers and (where specified) map images.
* Secrets redaction, rate limiting, retry/backoff, and basic dashboards exist.
* CI green; a newcomer can run the stack locally in <10 minutes, and deploy via Docker.

---

### When to prefer a “builder agent” over plain tickets

* You want the skeleton, CI, docs, and stubs generated **immediately** so you can iterate inside a working shell.
* You’re happy to let the agent make opinionated choices (TypeScript vs Python, test framework, map renderer) that you’ll refine later.
* You expect lots of repetitive wrapper code (tool stubs, schema definitions, error adapters) that an agent can mass‑generate consistently.

If you’d like, I can also produce:

* A **Codex system prompt** that pins coding conventions and enforces strict I/O schemas for all tools.
* The **first three PRs** (A0, B1, D1) in code so you can start running the server straight away.
