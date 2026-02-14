
show me an OS MasterMap map of postcodes around The Village Hotel, Coventry

12:09

Pinpointed hotel location and orchestrated cartographic visualization

Let me find The Village Hotel in Coventry and then render an OS map of the area.


Located hotel coordinates and prepared regional postcode mapping

Searching for places
Request

{
  "queries": [
    {
      "query": "Village Hotel Coventry",
      "max_results": 1
    }
  ]
}
Response

{"places": [{"name": "Village Hotel Coventry", "address": "The Village Hotel & Leisure Club, Coventry Business Park, Dolomite Ave, Coventry CV4 9GZ, UK", "latitude": 52.4029579, "longitude": -1.5466815999999999, "rating": 4.1, "rating_count": 2802, "types": ["hotel", "wedding_venue", "pub", "bar", "lodging", "event_venue", "point_of_interest", "service", "establishment"], "place_id": "ChIJB1bVrRlLd0gRKlsDdevfZ8s", "weekday_hours": ["Monday: Open 24 hours", "Tuesday: Open 24 hours", "Wednesday: Open 24 hours", "Thursday: Open 24 hours", "Friday: Open 24 hours", "Saturday: Open 24 hours", "Sunday: Open 24 hours"], "price_level": null, "reviews": ["I stayed at The Village Hotel Coventry for a three-day training course and had a good experience all round. The conference room facilities were well-equipped and comfortable. We were fed well throughout the training and the bar food was good too. The bedrooms were comfortable and I slept well. The staff were really helpful - in particular Kayleigh, Jess, Milly, Chrystal, Ashley, Adrian and Michael. I'd recommend this hotel to anyone thinking of staying there.", "Had a great stay at the hotel. Room was great but best of all was the customer service. I had made a mistake during the booking but the front of house team (Aidan & Lewis) promptly took steps to help my family out. Would stay again just because I know the customer service team are welcoming.", "I have seen a few good reviews with regards to food at the village, so I just wanted to try and level things up. I have eaten there when it is busy and quiet and every time the food is way below average. You wouldn't mind if the menu was challenging, but it is very limited and very difficult for a good chef to get wrong.\nThe bar staff also need lessons on how to pull a decent pint.", "Just love the Fitness Centre/ Leisure club in Coventry. The classes are run by such fit and friendly team. The variety of the classes means there\u2019s something for everyone and are just so enjoyable. The pool offers a relaxing atmosphere as well as being warm and welcoming. The facilities are kept up to date and clean.", "Read fully:\n\nI stayed at village hotel 15/01/2025-17/01/2026 with my partner.\n\nOn the day of arrival to the hotel the receptionist checked us in and also charged us \u00a315 for late checkout on departure day. I did not approve this and the receptionist just added this on. I got an email stating that there had been an update to my booking and I had to raise this with the manager the next day. This was resolved but was very frustrating as they should not be charging me for services that I do not appro..."]}]}
Found the Village Hotel at 52.4029579, -1.5466815999999999. Now let me look up nearby postcodes and render an OS map of the area.

Done
Found the Village Hotel. Now let me get the postcodes around it and render an OS map.


Pivoted to alternative mapping tools when primary service faltered

Os places nearest
Request

{
  "lat": "52.4029579",
  "lon": "-1.5466816"
}
Error

Tool 'os_places_nearest' not found. Similarly named tool(s): mcp-geo:os_places_nearest
Need the mcp-geo: prefix.

M


Os places radius
Request

{
  "lat": 52.4029579,
  "lon": -1.5466816,
  "radiusMeters": 500,
  "limit": 100
}
Error

Tool execution failed
Let me try with a smaller radius or limit.

M


Os places nearest
Request

{
  "lat": 52.4029579,
  "lon": -1.5466816
}
Error

Tool execution failed
Let me try the postcode lookup approach - find postcodes near the hotel. First let me search for the postcode.

M


Os places by postcode
Request

{
  "postcode": "CV4 9GZ"
}
Error

Tool execution failed
The OS Places API seems to be having issues. Let me try a different approach - use os_maps_render to create a map of the area around the hotel, and use os_places_search to find addresses.

M


Os places search
Request

{
  "text": "Village Hotel Coventry CV4 9GZ",
  "limit": 5
}
Error

Tool execution failed
OS Places API seems to be down. Let me try os_maps_render to create the map directly, and use os_names_find for postcodes nearby.

Done
The OS Places API seems unavailable right now. Let me render the OS MasterMap directly for the area around the Village Hotel and find nearby postcodes another way.


Pivoted to alternative mapping approach after encountering technical difficulties
M


Os names find
Request

{
  "text": "Dolomite Avenue Coventry",
  "limit": 5
}
Error

Tool execution failed
Let me try os_maps_render with a bbox around the hotel location. The hotel is at 52.4029579, -1.5466816. I'll create a bbox of roughly 500m around it.

Approximate conversions at this latitude:

1 degree lat ≈ 111km, so 500m ≈ 0.0045 degrees
1 degree lon ≈ 111km * cos(52.4) ≈ 67.7km, so 500m ≈ 0.0074 degrees
M


Os maps render
Request

{
  "bbox": [
    -1.554,
    52.398,
    -1.539,
    52.408
  ],
  "size": 1024
}
Error

Tool execution failed
Let me try a simpler render request.

M


Os maps render
Request

{
  "bbox": [
    -1.554,
    52.398,
    -1.539,
    52.408
  ]
}
Error

Tool execution failed
Let me check what's happening with the mcp-geo tools. Let me try a very simple tool call.

M


Os mcp descriptor
Error

Tool execution failed
All mcp-geo tools are failing. Maybe the server is down or not properly connected. Let me check with the browser tools instead and try a different approach - maybe I can create an HTML map file using OS tiles directly.

Done
It looks like the mcp-geo server isn't responding right now, Chris. Let me take an alternative approach and build you an OS MasterMap HTML file using MapLibre GL with OS vector tiles directly.

Claude's response was interrupted


show me an OS MasterMap map of postcodes around The Village Hotel, Coventry

Claude is AI and can make mistakes. Please double-check responses.

---

## Codex investigation (2026-02-14)

Trace evidence from `/Users/crpage/repos/mcp-geo/logs/claude-trace.jsonl` for the
same request sequence:

- Latest relevant initialize session starts at line `2044`.
- Client calls at lines `2091` to `2105` exactly match the failing UI tools:
  - `os_places_radius`
  - `os_places_nearest`
  - `os_places_by_postcode`
  - `os_places_search`
  - `os_names_find`
  - `os_maps_render` (twice)
  - `os_mcp_descriptor`
- Matching server responses at lines `2092` to `2106` are all successful:
  - JSON-RPC `result` present
  - `result.status=200`
  - `result.isError` absent
- Session parse errors: `0`.

Conclusion:

- The failures shown in Claude UI were not upstream API failures and not
  transport-level JSON-RPC failures.
- They were post-transport host-side handling failures (tool call reached server
  and returned 200).
- Also observed in this conversation: initial tool-name mismatch (`os_places_nearest`
  vs `mcp-geo:os_places_nearest`) was a separate client naming issue.

Remediation shipped in repo:

- Auto-populate `structuredContent` for dict tool outputs in stdio/http MCP tool
  results so strict hosts can validate tool responses.
- Added explicit troubleshooting guidance in `docs/troubleshooting.md` covering:
  - `Tool execution failed` with `status=200` traces.
  - macOS `"python3.14" would like to access data from other apps` startup prompt.

Additional follow-up from later run:

- Claude can still emit an initial unprefixed call (for example `os_names_find`)
  and immediately suggest the namespaced equivalent (`mcp-geo:os_names_find`).
- Standalone MapLibre HTML helpers can fail in Claude inline preview with
  `maplibregl is not defined` while working normally in a real browser. Treat
  this as preview-runtime limitation, not MCP server failure.
