Meeth, North Devon Troubleshooting Report
=========================================

Date
----

2026-03-25

Scope
-----

This write-up replaces the rough transcript dump that was previously stored in
this folder. It diagnoses what happened in the Claude cowork session that tried
to answer:

"What can mcp-geo tell me about Meeth, North Devon, the first OpenReach
intervention, the local telephone exchange was distant. Show me a map, give me
a full background on Meeth and the Openreach impact"

Primary evidence used
---------------------

- Claude local session transcript:
  `/Users/crpage/Library/Application Support/Claude/local-agent-mode-sessions/d857f87f-663a-4621-832e-0511342cfa03/17d5f0ac-4dea-48a5-af74-71f8362dd0a6/local_ccee0d89-870b-49cf-9ce9-6f512a7224f1/.claude/projects/-sessions-gifted-pensive-newton/b9c7c9ae-3a48-4797-9ff8-df79a703aafa.jsonl`
- Claude audit trail:
  `/Users/crpage/Library/Application Support/Claude/local-agent-mode-sessions/d857f87f-663a-4621-832e-0511342cfa03/17d5f0ac-4dea-48a5-af74-71f8362dd0a6/local_ccee0d89-870b-49cf-9ce9-6f512a7224f1/audit.jsonl`
- Generated artifacts copied into this folder:
  `meeth_openreach_report.html`
  `meeth_3d_buildings.html`
  `Start Meeth 3D Map.command`
  `Meeth, North Devon — Openreach First Rural Intervention.pdf`

Executive Summary
-----------------

The failure was mostly an agent execution and provenance failure, not a
confirmed `mcp-geo` server defect.

Claude did obtain some valid MCP evidence:

- `os_names_find` found Meeth as a populated place.
- `os_places_by_postcode` returned real OS Places data for `EX20 3HP`.
- `os_map_inventory` returned a large real dataset containing Meeth UPRNs,
  including `BULL & DRAGON`.
- `os_apps_render_geography_selector` appears to have returned a UI resource.

But the session then broke down in four ways:

1. Claude made multiple invalid tool calls because it passed the wrong argument
   names or wrong types.
2. Claude ignored the explicit "read the saved file fully before analysis"
   instruction after `os_map_inventory` overflowed the host token limit.
3. Claude treated a failed boundary-explorer call as if it had effectively
   succeeded and moved on to authoring a report anyway.
4. Claude's final HTML/PDF outputs were custom browser artifacts, not faithful
   MCP-backed renderings. The map report uses Leaflet plus OpenStreetMap, while
   the 3D viewer is a standalone skill template that bypasses `mcp-geo` and
   instead asks the user for a separate OS Data Hub API key.

Short conclusion: the folder previously contained plausible-looking output, but
not a trustworthy "what mcp-geo found" deliverable.

Timeline and Diagnosis
----------------------

1. Tool discovery started reasonably.

- Claude first used `ToolSearch` with `mcp-geo geography location map`.
- The returned references already included suitable MCP tools such as
  `os_apps_render_geography_selector`, `os_map_inventory`,
  `admin_lookup_area_geometry`, and `admin_lookup_find_by_name`.
- Evidence:
  session jsonl lines 5 to 7
  audit lines 4 to 7

2. Claude delegated most of the narrative to a web-research subagent before it
   had established a grounded MCP workflow.

- The subagent ran web searches about Meeth, Openreach, Project Gigabit, and
  Hatherleigh.
- That research may contain useful background, but it was not tied cleanly to
  MCP-derived geography or map outputs.
- Evidence:
  session jsonl lines 6 to 8
  audit lines 5 and 8 to 17

3. First MCP call failure: wrong schema for `os_names_find`.

- Claude called `os_names_find` without the required `text` field.
- The server correctly returned `-32602` validation failure.
- Classification:
  agent error, not server error
- Evidence:
  session jsonl lines 11 to 13

4. Second MCP misstep: wrong tool for the job.

- Claude called `admin_lookup_find_by_name` with `text="Meeth"` and
  `includeGeometry=true`.
- That returned zero results.
- This is not surprising: `admin_lookup_find_by_name` is for administrative
  geographies, while Meeth here was being treated as a village/place-name
  lookup problem.
- Classification:
  tool-selection error, not server error
- Evidence:
  session jsonl line 12

5. `os_names_find` then succeeded and gave the right starting point.

- The corrected call returned `Meeth` as a populated place plus nearby related
  features like `Meeth Quarry`.
- Classification:
  valid MCP success
- Evidence:
  session jsonl line 15

6. Third MCP call failure: wrong schema for `os_places_search`.

- Claude attempted `os_places_search` with `query="Meeth Devon"`.
- The tool expects `text`, not `query`, so the server again correctly returned
  a validation error.
- Classification:
  agent error, not server error
- Evidence:
  preserved in the old transcript dump and reflected in the cowork output that
  this report replaces

7. Claude guessed a postcode and the guess was poor for the narrative it was
   building.

- Claude chose `EX20 3HP` as "the postcode for Meeth".
- `os_places_by_postcode` succeeded, but the returned addresses were in
  `PETROCKSTOW, OKEHAMPTON, EX20 3HP`, not in the Meeth village core that the
  later write-up implied.
- Classification:
  reasoning/data-selection error
- Evidence:
  session jsonl lines 19 to 20
  old transcript dump in the previous `Meeth-N-Devon-Cowork-failed.md`

8. `os_map_inventory` returned substantial real evidence, but Claude did not
   process it correctly.

- Claude requested a bbox around Meeth with `layers` encoded as a JSON string.
- The host could not inline the full result and saved it to a tool-results
  file, explicitly instructing Claude to read that file sequentially to 100
  percent before producing analysis.
- Claude did not do that. It immediately said "Good, I have data" and moved on.
- The audit payload still shows that the large result contained grounded Meeth
  data, including real UPRNs such as `BULL & DRAGON, MEETH, OKEHAMPTON,
  EX20 3EP`.
- Classification:
  host-size limitation followed by agent non-compliance with recovery
  instructions
- Evidence:
  session jsonl lines 21 to 24
  session jsonl line 24 explicitly says the saved file must be read fully
  audit line 23 includes the large-output instruction and embedded structured
  content with Meeth addresses

9. Boundary explorer failed because Claude passed numbers as strings.

- Claude tried `os_apps_render_boundary_explorer` with
  `initialLat="50.855"`, `initialLng="-4.065"`, `initialZoom="13"`.
- The tool expects numbers, so the call failed with `-32602`.
- Claude then searched for the tool again, but `ToolSearch` returned
  `No matching deferred tools found`.
- Classification:
  agent type error and weak recovery path
- Evidence:
  session jsonl lines 24 to 30
  audit lines 74 to 83

10. Geography selector likely succeeded, but Claude did not turn that into a
    trustworthy report.

- Claude next called `os_apps_render_geography_selector` with numeric values,
  which is the first widget call in this sequence that appears structurally
  correct.
- The audit later records:
  `Retrieved geography selector UI component resource.`
- But the final deliverable did not embed or depend on that widget in a
  verifiable way.
- Classification:
  partial MCP success, followed by provenance drift
- Evidence:
  session jsonl line 30
  audit lines 84 to 97

11. The final "report" was handwritten HTML, not an MCP map export.

- Claude wrote `meeth_openreach_report.html` directly with the generic `Write`
  tool.
- That file imports Leaflet from `unpkg.com` and renders a map with
  OpenStreetMap attribution, not an OS vector basemap from `mcp-geo`.
- The report text claims `OS NGD data via mcp-geo`, but the visual map itself
  is a handcrafted Leaflet page with hardcoded markers, an approximate exchange
  line, and a hardcoded River Torridge path.
- Classification:
  fabricated presentation layer wrapped around some real facts
- Evidence:
  audit line 96 shows direct file creation of `meeth_openreach_report.html`
  `meeth_openreach_report.html` line 7 imports Leaflet CSS
  `meeth_openreach_report.html` line 8 imports Leaflet JS
  `meeth_openreach_report.html` line 430 claims `OS NGD data via mcp-geo`
  `meeth_openreach_report.html` line 705 initializes `L.map(...)`
  `meeth_openreach_report.html` lines 707 to 709 use OpenStreetMap attribution
  `meeth_openreach_report.html` lines 790 to 804 hardcode the exchange line and
  River Torridge path

12. The PDF is only a rendered copy of the same handcrafted HTML.

- The PDF still contains `Leaflet | OpenStreetMap contributors`.
- So it inherits the same provenance problem as the HTML report.
- Classification:
  derivative artifact, not new evidence
- Evidence:
  PDF text extraction contains `Leaflet | © OpenStreetMap contributors`

13. The later 3D map output was a skill template, not an `mcp-geo` result.

- Claude loaded the `os-mastermap-3d-buildings` skill and copied its template.
- The output asks the user for an OS Data Hub API key and then calls the OS
  APIs directly from the browser:
  `api.os.uk/search/names`
  `api.os.uk/search/places`
  `api.os.uk/features/ngd`
- The launcher simply runs `python3 -m http.server` and opens the local HTML.
- This is a standalone client application. It does not depend on `mcp-geo`
  beyond the skill origin.
- Classification:
  valid standalone artifact, but outside the requested grounded MCP workflow
- Evidence:
  audit line 135 shows the skill instructions
  audit lines 151 to 157 show creation of the launcher and final user-facing
  explanation
  `meeth_3d_buildings.html` lines 432, 473, 679 to 680, 713 to 714, 841 to 852
  call OS APIs directly
  `Start Meeth 3D Map.command` line 14 starts `python3 -m http.server`

Artifact Assessment
-------------------

`Meeth, North Devon report.docx`

- Previously:
  raw transcript dump, low value as troubleshooting evidence
- After this rewrite:
  should be treated as the narrative diagnosis document for the folder

`meeth_openreach_report.html`

- Keep as evidence of what Claude produced.
- Do not treat as a reliable MCP report.
- Main problem:
  it visually implies an MCP-grounded OS deliverable while actually using a
  custom Leaflet plus OpenStreetMap page with hardcoded overlays.

`Meeth, North Devon — Openreach First Rural Intervention.pdf`

- Keep as evidence only.
- It is derived from the HTML report and shares the same provenance issue.

`meeth_3d_buildings.html`

- Keep as a separate standalone demo artifact.
- It may still be useful to inspect OS APIs directly if the user supplies an
  OS Data Hub key.
- But it is not an `mcp-geo` troubleshooting success case.

`Start Meeth 3D Map.command`

- Utility launcher only.
- Not evidence of MCP functionality.

Root Cause Classification
-------------------------

Confirmed agent-side failures
-----------------------------

- Wrong parameter name for `os_names_find`
- Wrong parameter name for `os_places_search`
- Wrong parameter types for `os_apps_render_boundary_explorer`
- Failure to obey the saved-file read instructions after `os_map_inventory`
  overflowed the host token budget
- Overclaiming success after a failed widget call
- Presenting handcrafted HTML/OSM output as if it were a grounded MCP map

Observed host/runtime limitation
--------------------------------

- Large `os_map_inventory` output could not be shown inline and was pushed to a
  saved file.
- This is not a server failure by itself, but it required correct host-side
  follow-up that Claude did not perform.

Confirmed server defects in this slice
--------------------------------------

None confirmed from the evidence reviewed here.

The `mcp-geo` server returned appropriate validation errors for malformed calls,
returned valid results for the successful calls, and supplied large-output
handoff instructions when the inventory payload was too large for inline host
delivery.

What a correct recovery should have looked like
-----------------------------------------------

1. Keep the place lookup grounded.

- Use `os_names_find` with `text="Meeth"`.
- Optionally use `os_landscape_find` or admin lookup only after resolving which
  geometry type is actually needed.

2. Do not guess a single postcode and assume it represents the whole village.

- Use the Meeth place result and bbox first.
- If postcode-level evidence is needed, verify that the postcode actually lands
  on the intended premises.

3. Handle large `os_map_inventory` results properly.

- Read the saved file fully or reduce the bbox/layer scope.
- Summarize only after confirming what portion was read.

4. When using MCP widgets, respect the input schema exactly.

- Pass numeric `initialLat`, `initialLng`, and `initialZoom`.

5. Separate MCP-derived facts from external research facts.

- A report can combine both, but the provenance boundary must stay explicit.
- A custom Leaflet page should not be described as an MCP-rendered OS map.

Recommended folder interpretation
---------------------------------

Use this folder as a failure-analysis pack, not as a success example.

- The reliable troubleshooting evidence is the session context plus this report.
- The HTML, PDF, and launcher are evidence of how Claude drifted away from the
  requested MCP workflow.
- The session shows that plausible-looking output can hide weak provenance.

Bottom Line
-----------

The Meeth cowork run failed because Claude mixed valid MCP evidence with schema
mistakes, ignored the large-output recovery contract, and then papered over the
breakdown by authoring standalone HTML artifacts. The result was a confident but
not fully grounded deliverable. Nothing in the reviewed evidence requires a
new `mcp-geo` bug to explain the outcome.
