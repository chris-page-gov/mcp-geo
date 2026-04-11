# Audit: `ons_from_postcode`

Source trace: [ons_from_postcode.md](/Users/crpage/repos/mcp-geo/examples/ons_from_postcode.md)  
Audit date: 2026-04-11  
Client: Claude Code v2.1.101

## Executive Summary

This was a mostly successful Claude Code session using MCP-Geo to move from a
postcode to an Output Area profile and then to a small demographic summary.
The core geography lookup worked well, the follow-up OA questions were answered
with plausible use of `admin_lookup`, `nomis_query`, and raw ONSPD fields, and
the final narrative answer was useful to a human reader.

The main weakness was not correctness at the start of the flow. It was tool
selection and payload sizing in the middle of the flow:

- Claude made some unnecessary intermediate calls.
- It used `os_map_inventory` too broadly for a conversational summary.
- That inventory response overflowed the client token budget and was written to
  a local file instead of staying in-band.
- The workflow depended on Claude composing several low-level tools rather than
  using a single area-summary/profile surface.

In short: the trace shows that MCP-Geo can answer the question set, but the
current tool surface still makes the client do too much orchestration for a
simple "tell me about this OA" task.

## Session Walkthrough

### 1. Postcode to key geographies

User prompt:

`What geographies are in the CV3 1HB postcode`

Claude called:

- `ons_geo_by_postcode(postcode="CV3 1HB")`

Observed outcome:

- Successful.
- Claude extracted the main geography stack cleanly:
  - Country: `E92000001` England
  - Region: `E12000005` West Midlands
  - Local authority: `E08000026` Coventry
  - Ward: `E05001226` Lower Stoke
  - MSOA: `E02001984` Coventry 027
  - LSOA: `E01009617` Coventry 027C
  - Output Area: `E00048678`
- Claude also surfaced additional codes such as the 2024 Westminster
  constituency, ICB, NHS England region, police force area, TTWA, and built-up
  area.

Assessment:

- Good tool choice.
- Good answer structure.
- This is the strongest part of the trace.

### 2. Follow-up question: "What do you know about that OA"

Claude then called:

- `admin_lookup_find_by_name(text="E00048678")`
- `ons_geo_cache_status()`
- `admin_lookup_area_geometry(id="E00048678", includeGeometry=false)`
- `os_map_inventory(bbox=..., layers=["buildings","uprns"])`
- `nomis_query(dataset="NM_2021_1", params={"geography":"E00048678","variable":"1","measures":"20100"})`

Observed outcome:

- `admin_lookup_find_by_name` returned the OA as a named admin lookup hit.
- `ons_geo_cache_status` showed the ONS geo cache was available but degraded.
- `admin_lookup_area_geometry` returned the OA bbox.
- `os_map_inventory` exceeded the client token budget and was redirected to a
  Claude local file.
- `nomis_query` returned Census 2021 population for the OA.
- Claude produced a compact summary:
  - OA location
  - Usual residents: `292`
  - Approximate built environment: around `100` UPRNs/buildings
  - Small-area caveat about perturbation

Assessment:

- The answer was still useful.
- The tool chain was heavier than necessary.
- `ons_geo_cache_status` was not needed for the user question.
- `os_map_inventory` was a poor fit for the conversational need because Claude
  only needed a small count or a brief descriptive summary, not a large raw
  payload.

### 3. Follow-up question: demographic detail

User prompt:

`yes`

Claude called several `nomis_query` datasets:

- `NM_2041_1`
- `NM_2072_1`
- `NM_2028_1`
- `NM_2024_1`

Observed outcome:

- Successful.
- Claude converted the tabular results into a readable profile covering:
  - Sex
  - Ethnicity
  - Country of birth
  - Tenure
- Claude then added a short interpretive summary.

Assessment:

- Good synthesis.
- This is a strong example of client-side narration over low-level statistical
  outputs.
- The main weakness is discoverability: the user sees a set of opaque NOMIS
  dataset IDs rather than a high-level "OA demographic profile" capability.

### 4. Follow-up question: OA classification

User prompt:

`can you see the OA Classification?`

Claude called:

- `ons_geo_by_postcode(postcode="CV3 1HB", includeRaw=true)`

Observed outcome:

- Successful.
- Claude found raw ONSPD fields:
  - `oac01ind = 6C1`
  - `oac11ind = 4C1`
- Claude then interpreted the OAC hierarchy and explained the 2001 to 2011
  shift in classification.

Assessment:

- Good tool choice.
- Good use of `includeRaw=true`.
- This is a strong example of the value of preserving authoritative raw source
  fields in the response surface.

## What Worked Well

### Tool coverage was sufficient

The server had enough connected surfaces for Claude to complete the end-to-end
task:

- `ons_geo_by_postcode` for authoritative geography lookup
- `admin_lookup_area_geometry` for bbox geometry context
- `nomis_query` for Census profile facts
- `ons_geo_by_postcode(includeRaw=true)` for OAC codes

### Claude gave a readable answer

Claude did not just dump tool payloads. It:

- extracted the important fields
- grouped them into a logical geography stack
- turned statistical outputs into short summaries
- added appropriate caveats about small-area perturbation

### Raw ONSPD access materially improved the answer

Without `includeRaw=true`, Claude would not have had direct access to the OAC
code fields. That part of the tool design paid off.

## What Went Wrong or Was Inefficient

### 1. Unnecessary tool calls

The follow-up OA answer did not require:

- `ons_geo_cache_status`
- `admin_lookup_find_by_name`

Once the prior step had already returned `E00048678` as the OA, the client
could have gone straight to one of:

- an OA summary/profile tool
- `admin_lookup_area_geometry`
- `nomis_query`

This is a routing/orchestration inefficiency rather than a hard failure.

### 2. `os_map_inventory` was overkill for the question

The trace shows the main practical failure:

- `os_map_inventory` returned `133,188` characters
- Claude could not keep that in-band
- the result was written to a local tool-results file

That is poor ergonomics for a chat workflow whose real need was probably one of:

- count UPRNs
- count buildings
- classify the built form at a high level
- generate a compact OA built-environment summary

This is the clearest product gap exposed by the trace.

### 3. Too much orchestration was pushed onto the client

The server can answer the question, but the client had to infer the workflow:

1. postcode to OA
2. OA to bbox
3. bbox to buildings/uprns
4. OA to NOMIS facts
5. postcode raw row to OAC codes

That is workable for a strong model, but it is not the simplest possible
surface for users or weaker clients.

### 4. Dataset IDs were not user-legible

`NM_2021_1`, `NM_2041_1`, `NM_2072_1`, `NM_2028_1`, and `NM_2024_1` are useful
server-side identifiers, but they are not naturally understandable to users.
Claude papered over this by describing the content categories, but the tool
surface itself is still technical.

## Accuracy and Interpretation Notes

### Population and household counts

Claude reported:

- usual residents: `292`
- households: `110`

Those are plausible and consistent with the NOMIS-based workflow in the trace.
The small-area perturbation caveat was appropriate.

### "About 100 UPRNs and buildings"

This statement was derived after the `os_map_inventory` overflow event rather
than from a compact explicit count surface. The statement may be directionally
correct, but the route to it was weak. This is exactly the kind of answer that
should come from a server-side summary tool instead of a large raw inventory.

### OAC interpretation

Claude’s 2001/2011 OAC interpretation was reasonable. The trace note about a
2021 OAC not being present in the February 2026 ONSPD release is also a fair
statement in the context of ONSPD field availability, but it should be read as
"not present in this lookup surface" rather than a broad claim about all OAC
availability everywhere.

## Product Lessons for MCP-Geo

### Highest-value gap: add an OA profile surface

This trace strongly supports a high-level tool such as:

- `ons_geo.profile_area`
- `oa_profile.get`
- `small_area.profile`

That tool could return, in one compact payload:

- parent geographies
- population
- households
- OAC codes and labels
- a compact built-environment summary
- selected demographic headline facts

That would remove most of the client-side orchestration seen here.

### Add compact summary modes for inventory-heavy tools

`os_map_inventory` needs a mode that answers:

- counts only
- layer summary only
- capped top-N examples

For a conversational client, that matters more than returning every matching
record.

### Improve router hints for follow-up geography questions

The user asked "What do you know about that OA". A good router should infer:

- the user wants a profile, not a raw feature dump
- the OA id is already known from the previous turn
- the next best tools are summary/statistics-oriented, not cache-status or
  large inventory endpoints

### Keep raw fields accessible where they carry analytical value

The OAC success shows that `includeRaw=true` is worth preserving. It enables
useful analytical follow-ups without requiring separate niche tools.

## Suggested Remediation Backlog

### Priority 1

- Add a compact OA/small-area profile tool or resource.
- Add summary/count-only modes to `os_map_inventory`.
- Improve route selection for follow-up prompts such as "that OA", "that LSOA",
  and "tell me about this postcode area".

### Priority 2

- Add human-readable dataset labels or summary metadata on top of `nomis_query`
  workflows.
- Consider a server-side helper that maps common profile categories
  (`population`, `tenure`, `ethnicity`, `country_of_birth`) to curated NOMIS
  datasets.

### Priority 3

- Add a reusable area-summary prompt pattern/example for AI clients.
- Add an evaluation trace that asserts the client avoids large raw inventory
  calls when the user only asked for a summary.

## Bottom Line

The trace is a good demonstration of MCP-Geo’s underlying capability, but also
an equally good demonstration of why higher-level profile surfaces matter.

Claude got to a useful answer. It just had to work too hard in the middle, and
the `os_map_inventory` overflow was avoidable. The right lesson is not that the
session failed. The lesson is that the current low-level toolset still needs
one or two task-shaped summary surfaces to make this kind of enquiry routine,
cheap, and robust.
