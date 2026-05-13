---
title: "MCP-Geo Conversation Summary"
tags:
  - "summary"
  - "mcp-geo"
  - "llm-wiki"
---

# Conversation Summary

## CONV-001: LandIS, Nottinghamshire Coverage, and LEACS Access Probe

- Date: 2026-05-13
- Type: curated public-safe conversation record
- Reader: [CONV-001 reader](readers/conv-001-mcp-geo-landis-nottinghamshire-leacs.md)
- Source note: [CONV-001 source](sources/conv-001-mcp-geo-landis-nottinghamshire-leacs.md)
- Exchange count: 10
- Raw transcript status: not exported into this repository

This conversation began as a live MCP-Geo demonstration check, then moved into a practical geospatial investigation: identify collapse-risk geotechnical earthworks in Nottinghamshire, explain why LandIS-backed pipe-risk coverage was unavailable, recover the local PostGIS/LandIS workflow, inspect the mounted external data archive, and test whether missing LEACS data could be downloaded from public or authenticated LandIS routes.

The operational conclusion was that the MCP-Geo server and PostGIS/LandIS phase-2 archive path were recoverable, and Nottinghamshire can be served for NATMAP/Soilscapes/NSI-style soil context. LEACS-derived pipe-risk expansion is blocked because the public metadata and authenticated portal scan exposed LEACS descriptions but no downloadable LEACS payload.

## Key Outcomes

- MCP-Geo could be launched locally for demonstration once the secure OS API key source and server process were set up.
- OS NGD/admin tooling could identify Nottinghamshire and return geotechnical landform features relevant to collapse-risk screening.
- The LandIS warehouse issue was caused by local runtime/data availability, not by the MCP protocol surface itself.
- A working PostGIS sidecar could load the phase-2 LandIS archive tables needed for NATMAP, Soilscapes, and NSI queries.
- The external `ExtSSD-Data` archive was necessary for broader historical LandIS evidence, but it did not contain a LEACS data table.
- A fresh authenticated portal probe found no LEACS item, table, service, or relevant fields such as corrosion/shrink-swell indicators.
- The resulting LEACS access report is now the durable reference for future requests.

## Future Curation Candidates

Existing Claude conversation records in `docs/` should be curated into this same reader/exchange/source pattern when there is a specific reason to preserve them as a navigable MCP-Geo conversation history.
