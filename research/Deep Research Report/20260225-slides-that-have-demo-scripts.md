# 2026-02-25 Slides With Demo Scripts

This file adds live demo scripts you can run alongside:
`research/Deep Research Report/Apps_to_Answers_MCP_Government_Alignment_Slides.md`.

## Quick Links (Browser Tabs)
- [Slides deck](./Apps_to_Answers_MCP_Government_Alignment_Slides.md)
- [Research brief](./Research%20Apps%20to%20Answers_%20Connecting%20Public%20Sector%20Data%20to%20AI%20with%20MCP.md)
- [Government guidance (UK)](https://www.gov.uk/government/publications/making-government-datasets-ready-for-ai/guidelines-and-best-practices-for-making-government-datasets-ready-for-ai)
- [Local API docs](http://127.0.0.1:8000/docs)

## Readiness Check (Run First)
1. Check ONS geo cache readiness:
   ```bash
   curl -s -X POST "http://127.0.0.1:8000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{"tool":"ons_geo.cache_status"}' | jq
   ```
2. If `available` is `false`, use the default demo paths below (they still work).
3. Only run `ons_geo.by_postcode` / `ons_geo.by_uprn` when `available` is `true`.

## Demo 1 - Access Layer Interoperability
Slides:
- [Slides deck](./Apps_to_Answers_MCP_Government_Alignment_Slides.md) section:
  `Practical map: Government guidance -> delivery capability`

Message:
- Show MCP discovery and governed invocation as the bridge from apps to answers.

Operator script:
1. Start the server locally.
   ```bash
   uvicorn server.main:app --reload
   ```
2. Show capability discovery.
   ```bash
   curl -s "http://127.0.0.1:8000/tools/list?limit=10" | jq
   ```
3. Show scoped tool contract.
   ```bash
   curl -s "http://127.0.0.1:8000/tools/describe?name=admin_lookup.containing_areas" | jq
   ```
4. Run a bounded access call that works without ONS cache.
   ```bash
   curl -s -X POST "http://127.0.0.1:8000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{"tool":"admin_lookup.containing_areas","lat":52.4073,"lon":-1.5095}' | jq
   ```
5. Browser quick links (if server is running):
   - [tools/list](http://127.0.0.1:8000/tools/list?limit=10)
   - [tools/describe (admin_lookup.containing_areas)](http://127.0.0.1:8000/tools/describe?name=admin_lookup.containing_areas)
6. Optional extension when ONS cache is ready:
   ```bash
   curl -s -X POST "http://127.0.0.1:8000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{"tool":"ons_geo.by_postcode","postcode":"SW1A 1AA","derivationMode":"exact"}' | jq
   ```

What to point out:
- Capability is discoverable before invocation.
- Input/output schema is explicit.
- Output is evidence-bearing, not free-form generation.

## Demo 2 - Case Workflow (Peatland Style)
Slides:
- [Slides deck](./Apps_to_Answers_MCP_Government_Alignment_Slides.md) section:
  `Case example: peatland survey answers workflow`
- [Research brief case study section](./Research%20Apps%20to%20Answers_%20Connecting%20Public%20Sector%20Data%20to%20AI%20with%20MCP.md#case-study-deep-dive---mcp-geo-and-a-peatland-survey-episode)

Message:
- Demonstrate orchestration from location intent to bounded evidence with caveats.

Operator script:
1. Route a natural-language request to the right tool family.
   ```bash
   curl -s -X POST "http://127.0.0.1:8000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{"tool":"os_mcp.route_query","query":"For this area, show restoration evidence and boundaries"}' | jq
   ```
2. Resolve area candidates.
   ```bash
   curl -s -X POST "http://127.0.0.1:8000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{"tool":"admin_lookup.find_by_name","text":"Sherbourne","level":"WARD"}' | jq
   ```
3. Open boundary-focused interactive view (if using MCP-Apps host).
   - Prompt in host:
     `Run boundary explorer, show Sherbourne ward boundary`

What to point out:
- Discovery failure and boundary mismatch are controlled with explicit tool calls.
- The model is orchestrating verified interfaces, not inventing data paths.

## Demo 3 - Provenance by Default
Slides:
- [Slides deck](./Apps_to_Answers_MCP_Government_Alignment_Slides.md) sections:
  `Practical map: Government guidance -> delivery capability`,
  `Success metrics for Apps -> Answers`

Message:
- Every answer should be traceable to tool calls, parameters, and source identity.

Operator script:
1. Execute a deterministic lookup.
   ```bash
   curl -s -X POST "http://127.0.0.1:8000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{"tool":"admin_lookup.area_geometry","id":"E05001229"}' | jq
   ```
2. Show status/provenance metadata resource:
   ```bash
   curl -s -G "http://127.0.0.1:8000/resources/read" \
     --data-urlencode "uri=resource://mcp-geo/boundary-cache-status" | jq
   ```
3. Optional extension when ONS cache is ready:
   ```bash
   curl -s -X POST "http://127.0.0.1:8000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{"tool":"ons_geo.by_uprn","uprn":"100023336959","derivationMode":"exact","includeRaw":true}' | jq
   ```
4. Highlight evidence fields:
   - `id`, `bbox`, `meta.source`, `meta.geometryFormat`
   - `contents[0].uri`, `contents[0]._meta.generatedAt`
   - (optional `ons_geo`) `lookup.*`, `query.*`

What to point out:
- Answer includes reproducibility context.
- This supports assurance and audit conversations.

## Demo 4 - Safe Degradation (No Fabrication)
Slides:
- [Slides deck](./Apps_to_Answers_MCP_Government_Alignment_Slides.md) sections:
  `30-day thin-slice pilot (recommended)`,
  `Success metrics for Apps -> Answers`
- [Research brief pilot acceptance tests](./Research%20Apps%20to%20Answers_%20Connecting%20Public%20Sector%20Data%20to%20AI%20with%20MCP.md#30-day-thin-slice-pilot-plan-required)

Message:
- When dependencies fail, the system must refuse over-assertion and return safe status.

Operator script:
1. Simulate unavailable cache (run with empty/missing ONS cache path).
2. Run the ONS lookup call:
   ```bash
   curl -s -X POST "http://127.0.0.1:8000/tools/call" \
     -H "Content-Type: application/json" \
     -d '{"tool":"ons_geo.by_postcode","postcode":"SW1A 1AA","derivationMode":"exact"}' | jq
   ```
3. Show expected operational error shape (`CACHE_UNAVAILABLE` or `CACHE_READ_ERROR`, status `503`).

What to point out:
- Failure is explicit and machine-readable.
- No invented value is returned.
- This is the expected control behavior for public-sector trust.

## Demo 5 - Pilot Acceptance Gate
Slides:
- [Slides deck](./Apps_to_Answers_MCP_Government_Alignment_Slides.md) sections:
  `30-day thin-slice pilot (recommended)`,
  `Success metrics for Apps -> Answers`
- [Research brief demo narrative and acceptance tests](./Research%20Apps%20to%20Answers_%20Connecting%20Public%20Sector%20Data%20to%20AI%20with%20MCP.md#30-day-thin-slice-pilot-plan-required)

Message:
- Show that progression is evidence-gated, not opinion-gated.

Operator script:
1. Run targeted quality checks.
   ```bash
   ./.venv/bin/pytest -q --no-cov tests/test_tools_describe.py tests/test_os_map_tools.py tests/test_ons_geo.py tests/test_ons_geo_cache.py
   npm --prefix playground run test -- boundary_explorer_host_harness.spec.js
   ```
2. Present pass/fail summary under:
   - Accuracy and contract adherence
   - Provenance completeness
   - Safe degradation behavior
   - Operational stability baseline

What to point out:
- The pilot exit gate can be measured.
- Metrics map directly to leadership decision points in the deck.

## Presenter Notes (Short)
- Keep each demo to 2-4 minutes.
- Always show one success path and one degraded path.
- Use the same question phrasing before/after failure injection to prove behavior change is dependency-driven, not prompt-driven.
