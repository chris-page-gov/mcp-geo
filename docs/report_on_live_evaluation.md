## MCP-Geo evaluation report (live run)

### Scope and evidence used

* This report is based on the **live evaluation outputs** you provided: `evaluation_results_live.json` and `evaluation_results_live.audit.txt`. 
* I attempted to open the GitHub branch you referenced, but it was not accessible from my side (returned “Page not found”), so anything about the repo structure beyond what’s captured in the audit/skills output is necessarily limited to those artefacts.

---

## 1) What the MCP-Geo server does

### Observed capabilities (from the server’s own “skills” and “descriptor” outputs)

The server positions itself as a UK geospatial + ONS statistics MCP server providing:

* **OS Places** address lookups (postcodes, UPRNs, nearest addresses). 
* **OS Names** gazetteer searches for named features. 
* **OS NGD features** queries (topographic datasets by collection + bbox). 
* **ONS dataset discovery and observation queries**, with a live dataset search capability.
* **Administrative area lookups**, described as coming from live ONS geography via ArcGIS with fallback.
* **MCP-Apps UI widgets** (geography selector, statistics dashboard, feature inspector, route planner) exposed as UI resources with `ui://...` URIs.
* **Tool search metadata** for large tool catalogues (`tools/search`) and a “skills” guide available via `resources/read`.

### Tooling layout (as exposed by `os_mcp.descriptor`)

The live run shows the server reporting **version 0.2.5**, and a toolset of **30 tools**, with some marked “always loaded” and others “deferred” to reduce context/tool-loading overhead.

---

## 2) How the evaluation works (two steps: stubbed vs live)

### Step A — “offline / stubbed” mode (monkeypatched external calls)

**Strategy (as implied by the server’s own tool descriptions):**

* Some tools are explicitly designed to **use bundled sample data unless live mode is enabled**, e.g. `ons_data.query` is described as using the live ONS API only when a live flag is enabled *and* dataset identifiers are provided, otherwise it queries a bundled sample dataset.
* Similarly, admin lookups are described as having a live source with fallback. 

This is where monkeypatching (stubs) is most valuable: deterministic, repeatable tests that validate **routing + parameter formation + response shaping** without depending on upstream availability or drift.

### Step B — “live” mode (real upstream calls)

The “live” run you provided shows evidence of live upstream interaction, for example `admin_lookup.area_geometry` responses include `live: true` and a source marker. 

### What is actually being scored

Each question is scored across dimensions like:

* intent recognition
* tool selection
* efficiency (number of tool calls)
* response quality
* error handling

You can see these dimensions per question in the JSON output. 

---

## 3) What the live evaluation run revealed

### Headline results (facts)

* **41 questions**, total score **3666**, overall **89.41%**. 
* Overall effectiveness: **pass rate 92.68%** with a pass threshold of **75**. 
* Performance by difficulty (average %): basic **89.64**, intermediate **87.5**, advanced **86.25**, edge **92.75**, ambiguous **100.0**. 
* Performance by intent (average %):

  * address_lookup **96.67**
  * boundary_fetch **98.5**
  * interactive_selection **100.0**
  * route_planning **100.0**
  * vector_tiles **100.0**
  * statistics **84.5**
  * feature_search **87.5**
  * linked_ids **75.0**

### Tool coverage and runtime behaviour

* The harness made **46 tool calls**, touching **31 unique tools**; it believes **30 tools are registered**, so reported tool coverage is **96.67%**, with `os_mcp.route_query` listed as “missing” from the registered tool list. 

  * Interpretation: your router is central to the workflow, but it may not be discoverable via tool search/registry in the way the harness expects (worth aligning, because `route_query` is “the front door” per your skills doc).

### Concrete strengths demonstrated in the live run

* **OS Places** looks strong in live mode: successful postcode → UPRNs, UPRN → address, and nearest-address queries (e.g., SW1A 1AA, a specific UPRN, and nearest-to-coordinate).
* **Administrative geography** workflows worked end-to-end, including interactive selection + boundary fetch for Westminster OAs, with live geometry metadata.
* **MCP-Apps widgets** are clearly wired: the run successfully returned `ui://...` resources for the geography selector and feature inspector.
* **ONS dataset discovery (search)** succeeded and returned live dataset results for “GDP”. 

### Failures and gaps the live run exposed

These are the most important “drift/interpretation” checks you said you care about:

1. **ONS observation API drift / retirement surfaced immediately**

* `ons_data.dimensions` failed with an explicit upstream message indicating the API is **decommissioned/retired (25/11/2024)**.
* One statistics test (“Show two ONS observations for UK GDPV”) scored **45 (poor)** and recorded `ONS_API_ERROR`.

2. **OS Names parameter mismatch (`output_srs`)**

* Both `os_names.find` and `os_names.nearest` failed with `OS_API_ERROR`, explicitly complaining that `output_srs` is not a valid parameter.
  This is exactly the kind of thing the live run is meant to catch: your implementation diverges from the live API contract.

3. **OS NGD features query failed**

* `os_features.query` returned `OS_API_ERROR` and an XML exception response in the audit trail.

4. **Linked IDs capability looks not yet proven end-to-end**

* The linked-IDs test (`I006`) scored **75** largely because tooling was invoked, but intent recognition was wrong (expected `linked_ids`, detected `address_lookup`). 
* More importantly, `os_linked_ids.get` returned what looks like the **OS API “welcome” document** rather than an identifier resolution payload, which strongly suggests the call path/endpoint wiring is not yet correct. 

---

## 4) How well the live run demonstrates the server’s capability

### What the live run *does* demonstrate well (fact + judgement)

* **Fact:** High scores and perfect intent averages for interactive selection, route planning and vector tiles show the “MCP-Apps + routing + UI resource” part of the system is functioning reliably under test.
* **Judgement:** For “core user journeys” (find an area, get a boundary/bbox, look up addresses/UIPRNs, open widgets), this live run is a strong demonstration.

### What it does *not* yet demonstrate (because the live calls are failing or ambiguous)

* **ONS observation retrieval against live endpoints** is not currently demonstrated (and the errors indicate the endpoint set you coded to has been retired).
* **OS Names** and **OS NGD features** are not demonstrated end-to-end because the live calls are failing with contract/format issues.
* **Linked identifiers** are not demonstrated end-to-end because the “linked IDs” tool appears to be hitting a non-resolution endpoint (welcome document) and the router mislabels the intent.

---

## 5) Recommendations to tighten the “stubs vs live” strategy (so you can trust both)

### Immediate fixes suggested by the live run

* **OS Names:** remove or correct the `output_srs` parameter in `os_names.find` / `os_names.nearest` to match the live API contract.
* **ONS data:** revisit the implementation behind `ons_data.dimensions`, `ons_data.get_observation`, and live observation querying to target the currently supported ONS API surface (your harness is currently tripping the retirement message).
* **Linked IDs:** confirm `os_linked_ids.get` is calling the intended resolution endpoint and returning identifier mappings, not the API root document. 
* **Router intent:** add/strengthen rules so “resolve linked IDs” routes to `linked_ids` intent. 

### Testing approach (opinion, but grounded in what failed)

* Keep the **monkeypatched stub run** as your fast, deterministic “does the agent pick the right tools and shape the right parameters?” gate.
* Add a small set of **contract tests** per upstream (OS Places, OS Names, OS NGD, ONS) that:

  * run live on a schedule,
  * store request/response pairs (sanitised) as fixtures,
  * fail loudly on drift (exactly like the `output_srs` and ONS retirement issues you’ve just uncovered).

If you want, paste the harness entrypoint/config (or the relevant test runner script) and I’ll suggest a concrete split of: *unit (pure stub)* vs *contract (live)* vs *end-to-end (host + proxy + server)*—but even from this run alone, you already have a clear list of which upstream integrations need attention first.
