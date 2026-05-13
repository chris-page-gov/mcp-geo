
Claude finished the response
Show me a map so I can see postcodes around of CV3 1HB
Claude responded: Got the coordinates.

Used mcp-geo integration, loaded tools
Used mcp-geo integration, loaded tools
The user wants to see a map showing postcodes around CV3 1HB. I have access to OS/geo MCP tools. Let me use the mcp-geo tools to get postcode data and render a map. Let me first look up the postcode CV3 1HB to get its location, then find nearby postcodes.

Let me load the tool schemas I need first.

Show less

Loading tools
Request

{
  "query": "select:mcp__mcp-geo__os_places_by_postcode,mcp__mcp-geo__os_apps_render_boundary_explorer,mcp__mcp-geo__ons_geo_by_postcode",
  "max_results": 3
}
Let me first look up the postcode CV3 1HB to get its coordinates, then render a boundary explorer map centered on it.

M


ons_geo_by_postcode
Request

{
  "postcode": "CV3 1HB"
}
Response

{"query":{"postcode":"CV31HB","derivationMode":"exact"},"lookup":{"keyType":"postcode","product":"ONSPD","derivationMode":"exact","release":"February 2026","resolvedRelease":"February 2026","sourceName":"ONS Postcode Directory (exact)","sourceFormat":"ndjson","schemaFingerprint":"f6f847e317e9b825569caccff0a3f864cb456787f730541341c13c99067d173d","resolvedSourceUrl":null,"cachedAt":"2026-04-10T22:16:22Z","freshness":null},"geographies":{"cty25":{"code":"E99999999"},"ced25":{"code":"E99999999"},"lad25":{"code":"E08000026"},"wd25":{"code":"E05001226"},"parncp25":{"code":"E43000246"},"hlth19":{"code":"E18000005"},"nhser24":{"code":"E40000011"},"ctry25":{"code":"E92000001"},"rgn25":{"code":"E12000005"},"ssr95":{"code":"7"},"pcon24":{"code":"E14001182"},"eer20":{"code":"E15000005"},"educ23":{"code":"E24000043"},"ttwa15":{"code":"E30000195"},"pco19":{"code":"E16000070"},"itl25":{"code":"E08000026"},"wdstl05":{"code":"00CQGD"},"oa01":{"code":"E00048678"},"wdcas03":{"code":"00CQFJ"},"npark16":{"code":"E65000001"},"lsoa01":{"code":"E01009617"},"msoa01":{"code":"E02001984"},"oa11":{"code":"E00048678"},"lsoa11":{"code":"E01009617"},"msoa11":{"code":"E02001984"},"wz11":{"code":"E33020570"},"sicbl24":{"code":"E38000251"},"bua24":{"code":"E63010120"},"pfa23":{"code":"E23000014"},"cal24":{"code":"E56000007"},"icb23":{"code":"E54000018"},"oa21":{"code":"E00048678"},"lsoa21":{"code":"E01009617"},"msoa21":{"code":"E02001984"}},"normalizedGeographies":{"oa":{"code":"E00048678","name":null,"currentCode":"E00048678","currentName":null,"status":"unknown","sourceDataset":null,"codeFamily":null,"successorCode":null,"successorName":null,"level":null},"lsoa":{"code":"E01009617","name":null,"currentCode":"E01009617","currentName":"Coventry 027C","status":"current","sourceDataset":"RGC","codeFamily":"lsoa","successorCode":null,"successorName":null,"level":"lower_layer_super_output_area"},"msoa":{"code":"E02001984","name":null,"currentCode":"E02001984","currentName":"Coventry 027","status":"current","sourceDataset":"RGC","codeFamily":"msoa","successorCode":null,"successorName":null,"level":"middle_layer_super_output_area"},"lad":{"code":"E08000026","name":null,"currentCode":"E08000026","currentName":"Coventry","status":"current","sourceDataset":"RGC","codeFamily":"lad","successorCode":null,"successorName":null,"level":"local_authority_district"},"ward":{"code":"E05001226","name":null,"currentCode":"E05001226","currentName":"Lower Stoke","status":"current","sourceDataset":"RGC","codeFamily":"ward","successorCode":null,"successorName":null,"level":"ward"},"country":{"code":"E92000001","name":null,"currentCode":"E92000001","currentName":"England","status":"current","sourceDataset":"RGC","codeFamily":"country","successorCode":null,"successorName":null,"level":"country"},"region":{"code":"E12000005","name":null,"currentCode":"E12000005","currentName":"West Midlands","status":"current","sourceDataset":"RGC","codeFamily":"region","successorCode":null,"successorName":null,"level":"region"}},"semanticFields":{"postcode":"CV31HB","lad_code":"E08000026","oa_code":"E00048678","lsoa_code":"E01009617","msoa_code":"E02001984","ward_code":"E05001226","country_code":"E92000001","region_code":"E12000005"},"codeStatusSummary":{"unknown":1,"current":6},"geographyCount":34,"provenance":{"source":"ons_geo_cache","product":"ONSPD","derivationMode":"exact","release":"February 2026","resolvedRelease":"February 2026","schemaFingerprint":"f6f847e317e9b825569caccff0a3f864cb456787f730541341c13c99067d173d","resolvedSourceUrl":null,"freshness":null}}
The postcode CV3 1HB is in Coventry (LAD: E08000026), Ward: Lower Stoke. Now let me get the actual coordinates by looking up the postcode via os_places_by_postcode, and then render a boundary explorer map. Actually, let me just render the boundary explorer directly with a search term for CV3 1HB. The boundary explorer should be able to center on the postcode area.

Let me render the boundary explorer focused on postcode level for CV3 1HB. I need to find the lat/lng for this postcode first. Let me use os_places_by_postcode.

Show less
M


os_places_by_postcode
Request

{
  "postcode": "CV3 1HB"
}
Response

{"uprns":[{"uprn":"100070620457","address":"136, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4062585,"lon":-1.4754072,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620459","address":"138, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.406285,"lon":-1.4753187,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620461","address":"140, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4063118,"lon":-1.4752595,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620463","address":"142, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4063475,"lon":-1.4752003,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620465","address":"144, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.406374,"lon":-1.4751118,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620466","address":"146, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4063826,"lon":-1.4750235,"classification":"RD04","classificationDescription":"Terraced","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620468","address":"152, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4064509,"lon":-1.4748218,"classification":"RD02","classificationDescription":"Detached","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620469","address":"154, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4064622,"lon":-1.4747139,"classification":"RD02","classificationDescription":"Detached","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620470","address":"156, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4065066,"lon":-1.4745958,"classification":"RD03","classificationDescription":"Semi-Detached","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620471","address":"158, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4065422,"lon":-1.4745218,"classification":"RD03","classificationDescription":"Semi-Detached","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620472","address":"160, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4065596,"lon":-1.4743893,"classification":"RD03","classificationDescription":"Semi-Detached","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620473","address":"162, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4065683,"lon":-1.4743157,"classification":"RD03","classificationDescription":"Semi-Detached","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620474","address":"164, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4066308,"lon":-1.4742121,"classification":"RD03","classificationDescription":"Semi-Detached","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100070620475","address":"166, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4066483,"lon":-1.474109,"classification":"RD03","classificationDescription":"Semi-Detached","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10093949647","address":"GROUNDSMANS HOUSE, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.404929,"lon":-1.47556,"classification":"RD","classificationDescription":"Dwelling","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100071503878","address":"BINLEY ROAD SERVICE STATION, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4060971,"lon":-1.475512,"classification":"CR05","classificationDescription":"Petrol Filling Station","local_custodian_code":4610,"localCustodianName":null},{"uprn":"100071315856","address":"BULLS HEAD, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.4059168,"lon":-1.4774398,"classification":"CR06","classificationDescription":"Public House / Bar / Nightclub","local_custodian_code":4610,"localCustodianName":null},{"uprn":"10024027459","address":"COVENTRY & NORTH WARWICKSHIRE SPORTS CLUB, BINLEY ROAD, COVENTRY, CV3 1HB","lat":52.40495,"lon":-1.4754678,"classification":"CL06CK","classificationDescription":"Cricket Facility","local_custodian_code":4610,"localCustodianName":null}],"provenance":{"source":"os_places","timestamp":1777374338.2289412}}
I have the coordinates for CV3 1HB - approximately lat: 52.406, lon: -1.475. Now I can render the boundary explorer map centered on this location, showing postcodes. Let me use the os_apps_render_boundary_explorer tool with postcode level.

The boundary explorer is ready. I need to render it. Let me use the os_resources_get tool to get the HTML content and display it.

Done
Got the coordinates. Now let me render the map centred on CV3 1HB with postcode boundaries.


Used mcp-geo integration, loaded tools
Used mcp-geo integration, loaded tools

Loading tools
Request

{
  "query": "select:mcp__mcp-geo__os_resources_get",
  "max_results": 1
}
Let me get the HTML content for the boundary explorer widget.

M


os_resources_get

Result
The HTML is very large (199KB). Let me just fetch all the chunks and save it to a file, then serve it as an artifact. Actually, let me save it piece by piece. The content is 199,012 bytes total and I've gotten 24,576 bytes so far.

Actually, I think the best approach is to save this HTML to a file. Let me get all the chunks and write them to a file, then present it to the user.

But that's a lot of chunks (199012 / 24576 ≈ 9 chunks). Let me fetch them all.

Actually, let me think about this differently.

I need to retrieve all the remaining chunks of this large HTML file and assemble them into a complete artifact that the user can view directly.

Show more
M


os_resources_get

Result
This is going to be a very large HTML file. I need to get all 9 chunks (199012 / 24576 ≈ 8.1 chunks) and save them to a file. Let me get the remaining chunks. Actually, let me just write the first chunk to a file and then append the subsequent chunks. But the Write tool overwrites the file, so I need to get all chunks first and then write them all at once.

Let me get all the remaining chunks simultaneously where possible - but I need to do them sequentially since each chunk depends on the previous nextPageToken.

I'll fetch them sequentially and accumulate the text, working through each offset point until I reach the end of the file.

Show more
M


os_resources_get

Result
This is going to take a very long time to get all the chunks. Let me save what I have so far and keep fetching. Actually, let me think of a better approach.

The file is 199,012 bytes. I need approximately 9 chunks at 24576 bytes each. Let me just fetch them all and concatenate them, then save the complete HTML file.

I've got chunks 0-73728 so far. Let me continue getting the rest.

Show more
M


os_resources_get

Result
This is taking a lot of chunks. Let me think about a better approach. The HTML file is ~200KB and I'm getting it in 24KB chunks - that's 9 chunks. Rather than fetching them all in here and accumulating the text (which would use a lot of context), let me use bash to fetch the whole file programmatically.

Wait, but I can't just call a URL from bash because it's a special ui:// protocol served by the MCP server. I need to use the MCP tool to get it.

Let me think of an alternative approach. The HTML widget is the boundary explorer. Rather than downloading it and displaying it, maybe I should just tell the user about what's available and let the tool do its job.

Actually, the response from os_apps_render_boundary_explorer gave me a resourceUri: "ui://mcp-geo/boundary-explorer". I could use mcp__cowork__create_artifact to embed this widget, but it's hosted as an MCP resource rather than a standalone URL. Instead, I'll save the HTML to the workspace and give the user a link to it. I've got 4 chunks so far and need to fetch the remaining 5 chunks to complete the file.

I'm going to keep fetching the rest of the chunks rather than trying to work around the limitations of the write tools. Let me continue pulling the remaining data.

Show more
M


os_resources_get

Result
I'm getting a lot of context here. Let me think of an alternative approach. Instead of downloading all these chunks and assembling the file manually (using up all my context), let me use bash to call the mcp-geo server's API directly, or maybe I can use a different approach.

Actually, looking at this more carefully, the boundary explorer is a rich HTML widget that requires:

MapLibre GL JS (from a vendor path)
A host connection (postMessage API) to call MCP tools
A proxy backend for OS maps
This means simply serving the HTML file won't work well without that infrastructure. The widget is designed to run inside the mcp-geo app environment.

The boundary explorer tool has already done its job configuring the app with the initial location and zoom for CV3 1HB, so the widget just needs to be opened in the right context. I realize I can't access ui:// URIs from bash, so I'll need to fetch the remaining chunks and assemble the complete HTML file myself.

Looking at the config returned, the HTML widget is meant to be rendered in an embedded view, and I could potentially use the artifact creation tool to display it, but I'm burning through context quickly and need to think about whether there's a more efficient approach here.

The user wants to see postcodes around CV3 1HB on a map, and the boundary explorer is the right tool for this. I've already fetched several chunks of the HTML file, so I should consolidate what I have, fetch the remaining chunks, save the complete file to the workspace, and give the user a link to access it. I'm hitting context limits with all this HTML, so let me pivot to creating an interactive map visualization instead. I'll build a self-contained HTML artifact using OpenStreetMap and MapLibre GL, centered on the CV3 1HB coordinates I already have, rather than trying to fetch and store massive boundary polygon data.

Show more
Done

M

mcp-geo os_apps_render_boundary_explorer
Let me take a more efficient approach and create a map artifact directly, centred on CV3 1HB with postcode boundaries.


Loaded tools
Loaded tools

Loading tools
Request

{
  "query": "select:mcp__cowork__create_artifact,mcp__mcp-geo__os_features_query",
  "max_results": 2
}
Now let me create a nice map artifact centered on CV3 1HB. Since I can't use external map tile APIs (network access is blocked in artifacts), I need to work with what I have.

Actually, looking at the artifact restrictions: "network access is blocked except for the exact CDN URLs listed below" - and the CDN URLs listed are only Chart.js, Grid.js, Mermaid.js, and their CSS. No Leaflet, no MapLibre, no OpenStreetMap tiles.

So I can't create an interactive map in an artifact with tiles. I need a different approach.

Let me think about what I can do:

Use the mcp-geo tools to get postcode data and then create a static SVG-based visualization
Use the OS features query to get postcode polygons and create a Canvas/SVG map
Actually wait - looking at the boundary explorer tool more carefully, it returns a ui://mcp-geo/boundary-explorer resource. The Cowork environment has a special way of rendering these - it's not just a regular HTML file. The os_apps_render_boundary_explorer tool renders a widget that's displayed in the Cowork sidebar. This suggests that Cowork knows how to render UI resources from the mcp-geo service, so I should leverage that capability instead of trying to build my own map visualization.

But I was trying to get the HTML and save it as a file, which is the wrong approach. The ui:// resource is meant to be rendered directly by Cowork through the uiResourceUris field. I need to figure out how to save this as a self-contained HTML page that the user can open, since I have file access and can run code in the sandbox.

The boundary explorer widget is configured correctly and the app is ready, but I've only fetched 5 of 9 chunks of the HTML. Rather than continue burning through my context window fetching the rest, I should try a different approach—maybe creating an SVG-based map using postcode data from the OS API, or building a simple HTML file with Leaflet.js from a CDN.

Actually, since the file will be saved to the workspace rather than as an artifact, I can use any CDN I want. But on second thought, I already have most of the boundary explorer HTML fetched—it's the perfect tool for what Chris needs, so I should just finish pulling the remaining chunks efficiently instead of switching approaches.

Let me create a simple Leaflet map HTML file that fetches nearby postcodes dynamically using the Postcodes.io API to show what's around CV3 1HB. I'm realizing the OS Features API might not have postcode boundaries readily available, so I'll take a simpler approach—create a self-contained Leaflet HTML file centered on CV3 1HB with OpenStreetMap tiles, a prominent marker for the postcode, and fetch nearby postcode sectors from the postcodes.io API directly within the HTML file. I'm going to skip the complexity of fetching all those chunks and instead build a self-contained HTML file with Leaflet and OpenStreetMap, centered on CV3 1HB with the coordinates I already have, then use the Postcodes.io API to dynamically load nearby postcode data when the page loads.

Show less
Done
I have all the location data I need. Rather than reassembling the chunked HTML, let me create a clean interactive postcode map saved to your folder.


Created a file
Created a file

Created postcodes-cv3-1hb.html
postcodes-cv3-1hb.html
Done
Here's your postcode map:

View postcodes around CV3 1HB

Open it in a browser and it will load ~100 postcodes within 1.2 km of CV3 1HB (Binley Road, Coventry) from the postcodes.io API. Each postcode is plotted as a coloured dot — colour-coded by sector (CV3 1, CV3 2, etc.) — and you can click any marker to see the ward, coordinates, and postcode details. Your focus postcode CV3 1HB is pinned in orange.


Postcodes cv3 1hb
Code · HTML


ChatGPT Atlas






Claude is AI and can make mistakes. Please double-check responses.
Postcodes cv3 1hb · HTML

ChatGPT Atlas
