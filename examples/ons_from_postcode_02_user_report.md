# Report: postcode to OA profile in Claude Code

Source trace: [ons_from_postcode.md](/Users/crpage/repos/mcp-geo/examples/ons_from_postcode.md)  
Companion technical audit: [ons_from_postcode_01_audit.md](/Users/crpage/repos/mcp-geo/examples/ons_from_postcode_01_audit.md)

## What happened

Claude Code used MCP-Geo to answer a simple chain of questions:

1. find the geographies for postcode `CV3 1HB`
2. identify the Output Area for that postcode
3. describe that Output Area
4. pull a small demographic profile
5. check the Output Area Classification

The session was mostly successful. Claude got to the right OA and gave a useful
small-area summary for `E00048678`.

## What Claude found

For postcode `CV3 1HB`, Claude correctly identified:

- Output Area: `E00048678`
- LSOA: `E01009617` `Coventry 027C`
- MSOA: `E02001984` `Coventry 027`
- Ward: `E05001226` `Lower Stoke`
- Local authority: `E08000026` `Coventry`
- Region: `E12000005` `West Midlands`
- Country: `E92000001` `England`

It then pulled a short Census 2021-style profile for the OA, including:

- usual residents: `292`
- households: `110`
- equal male/female split
- a mixed ethnic profile with a relatively high Indian and wider South Asian
  presence
- predominantly owner-occupied housing, with a substantial private-rented
  share

Claude also found the OAC codes from raw ONSPD fields:

- 2001 OAC: `6C1`
- 2011 OAC: `4C1`

## What worked well

- The postcode-to-geography lookup worked cleanly.
- Claude was able to carry the OA id into later questions.
- The demographic write-up was readable and useful.
- Raw ONSPD access made the OAC follow-up possible.

For a human user, the conversation mostly looked like a success.

## Where it struggled

The main problem was not wrong answers. It was inefficiency.

Claude used a large `os_map_inventory` call when the user only wanted a short
description of the OA. That response was too large for the client and overflowed
the token/output budget, so Claude had to fall back to a saved local file. That
is not a good user experience for an otherwise simple question.

Claude also made some extra calls that were not really needed, such as checking
the ONS geo cache status in the middle of the flow.

So the issue here is:

- not "the tools cannot answer the question"
- but "the tools make the client work harder than it should"

## Plain-English conclusion

MCP-Geo is already capable of answering this kind of enquiry, but it is still
too low-level for the smoothest AI-client experience.

The user wanted:

`Tell me about this Output Area`

Claude had to build that answer by stitching together several tools:

- geography lookup
- area geometry
- map inventory
- one or more NOMIS dataset calls
- raw ONSPD inspection

That is why the session worked but still felt a bit clunky.

## What would make this better

The biggest improvement would be a single compact "small area profile" tool.

That tool should return, in one response:

- the OA and its parent geographies
- population and households
- OAC codes and labels
- a small built-environment summary
- a few headline demographic facts

That would let Claude answer the whole follow-up question directly, without
trying a large raw inventory call.

## What to tell users today

Until that higher-level surface exists, the best user guidance is:

- ask for a short profile, not a full building inventory
- ask for specific themes if possible

Examples:

- `Give me a short profile of OA E00048678`
- `Summarise population, tenure, and ethnicity for that OA`
- `What is the OA classification for CV3 1HB?`
- `How many usual residents and households are in that OA?`

Those prompts are more likely to keep the client on a compact route.

## Recommended wording for demos

If this flow is shown in a demo, the fair summary is:

`Claude successfully moved from postcode to Output Area, then produced a small-area demographic summary and OA classification using MCP-Geo. The remaining issue is not data access but workflow efficiency: some follow-up questions still force the client to orchestrate too many low-level tools.`

## Bottom line

This trace is a good example of "mostly working, but not yet elegant".

The result was useful. The main next step is to make this use case cheaper and
more direct by giving AI clients a task-shaped Output Area profile surface,
instead of expecting them to build one from several low-level calls.
