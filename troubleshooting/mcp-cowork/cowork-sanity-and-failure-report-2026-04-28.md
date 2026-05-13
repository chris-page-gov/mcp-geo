# Claude Cowork MCP-Geo Sanity and Failure Report

Date: 2026-04-28

## Scope

This note diagnoses the saved Claude Cowork transcripts in
`troubleshooting/mcp-cowork/` and separates:

- MCP-Geo server/runtime health
- Docker Desktop external-drive mount health
- Claude Cowork MCP-App/artifact handling

The immediate user-facing prompt was:

> Show me a map of CV3 1HB

## Primary Evidence

- Saved Cowork transcript:
  `troubleshooting/mcp-cowork/mcp-cowork-failures.md`
- Second saved Cowork transcript:
  `troubleshooting/mcp-cowork/mcp-cowork-fail2.md`
- Cowork-created standalone HTML map:
  `postcodes-cv3-1hb.html`
- Screenshot showing the standalone map failure:
  `[LOCAL_SCREENSHOT_PATH]`
- Claude local audit session:
  `[LOCAL_CLAUDE_AUDIT_JSONL]`
- Claude session metadata:
  `[LOCAL_CLAUDE_SESSION_METADATA]`

## Executive Summary

MCP-Geo itself passed the key sanity checks once optional external-drive mounts
were suppressed:

- STDIO initialize succeeded.
- `os_mcp.descriptor` returned server version `0.8.1`.
- `os_places.by_postcode` returned 18 UPRNs for `CV3 1HB` when run with the
  same `OS_API_KEY_FILE` shape that Claude uses.
- `os_apps.render_boundary_explorer` returned a valid MCP-App handoff with
  `resourceUri=ui://mcp-geo/boundary-explorer`.
- `os_resources.get` returned the MCP-App HTML resource with byte-offset
  pagination (`totalBytes=199012`, `nextPageToken=2048` in the sanity probe).

There are three real failure classes:

1. Docker Desktop previously could not mount `[EXTSSD_DATA_ROOT]` into
   containers. The drive was visible to macOS, but Docker failed with
   `mkdir [DOCKER_HOST_EXTSSD_PATH]: file exists`. This is consistent with
   an external drive being mounted after Docker Desktop started. A later probe
   now succeeds, so the mount issue is no longer current.
2. Claude Cowork did not render or preserve the MCP-App handoff. It fetched
   chunks of the 199 KB app resource, decided it was too large / backend-bound,
   then created custom Leaflet/OpenStreetMap artifacts instead of using the
   MCP-App resource.
3. The second standalone map failed for a separate, expected reason: it used
   `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`, and the screenshot
   shows OpenStreetMap returning a tile-policy block requiring a referrer.
   That is not an MCP-Geo basemap failure.

## Sanity Checks Run

### 1. Docker External-Drive Mount Probe

Command shape:

```bash
docker run --rm -v [EXTSSD_DATA_ROOT]:/mnt:ro alpine:3.20 sh -c 'ls -ld /mnt'
```

Initial result:

```text
docker: Error response from daemon: error while creating mount source path '[DOCKER_HOST_EXTSSD_DATA_PATH]': mkdir [DOCKER_HOST_EXTSSD_PATH]: file exists
```

macOS can see the path:

```text
[EXTSSD_MOUNT_ROOT]
[EXTSSD_DATA_ROOT]
```

Later result after the drive was available:

```text
drwxr-xr-x   30 root     root           960 Apr 11 03:52 /mnt
```

Interpretation: the original failure was a Docker Desktop mount-state problem,
not a missing host directory. The latest probe confirms Docker can now mount
the external data directory.

### 2. Claude Wrapper Plan

Default `.env` currently activates external-drive mounts:

```text
LANDIS_LOCAL_DATA_ROOT=[EXTSSD_DATA_ROOT]
BOUNDARY_RUNS_SEARCH_DIRS=[EXTSSD_DATA_ROOT]
MCP_TOOLS_DEFAULT_TOOLSET=starter
MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS=ons_geo_lookup,property_tax,features_layers,landis_soils
```

`scripts/claude-mcp-local` therefore plans:

```text
landis_host_data_root=[EXTSSD_DATA_ROOT]
landis_mount_enabled=true
boundary_runs_search_host_paths=[EXTSSD_DATA_ROOT]
```

With Docker Desktop in the current state, that default plan fails before MCP
startup.

### 3. MCP Sanity With External Mounts Suppressed

Environment override used for the sanity pass:

```bash
MCP_GEO_LANDIS_DATA_ROOT=/__missing_mcp_geo_landis
LANDIS_LOCAL_DATA_ROOT=/__missing_mcp_geo_landis
LANDIS_PORTAL_ARCHIVE_DIR=/__missing_mcp_geo_landis_portal
LANDIS_FULL_RELEASE_ARCHIVE_DIR=/__missing_mcp_geo_landis_full
BOUNDARY_RUNS_SEARCH_DIRS=/__missing_mcp_geo_boundary_search
OS_API_KEY_FILE=<same path configured for Claude>
```

Results:

```text
initialize: ok
os_places.by_postcode(CV3 1HB): 18 UPRNs
os_apps.render_boundary_explorer: resourceUri ui://mcp-geo/boundary-explorer
os_resources.get(ui://mcp-geo/boundary-explorer): totalBytes 199012, nextPageToken 2048
```

Interpretation: the postcode and MCP-App resource paths are server-healthy.

### 4. Claude Startup Scope Recheck After Mount Recovery

After the Docker mount probe succeeded, the Claude startup-scope checker reached
the wrapper and produced:

```text
wrapper=[LOCAL_REPO]/scripts/claude-mcp-local
build_mode=never
expected_scope=starter+ons_geo_lookup,property_tax,features_layers,landis_soils
baseline_tools=51
scoped_tools=51
FAIL: scoped tool count is not lower than baseline
```

Interpretation: this is no longer the external-drive startup failure. The
wrapper can start, but this checker cannot prove discovery reduction because
the wrapper hydrates `MCP_TOOLS_DEFAULT_TOOLSET` and
`MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS` from `.env` even in the "baseline" run.
Both measured runs are therefore already scoped. Treat this as a checker defect
or stale assertion, not evidence that the MCP server failed to start.

## Cowork Transcript Findings

### Finding 1: Version Answer Was Visibly Truncated

Transcript line 6 says:

```text
Claude responded: The mcp-geo MCP server running is version 0.
```

But the underlying tool response at line 33 clearly includes:

```json
{"server":"mcp-geo","version":"0.8.1","protocolVersion":"2025-11-25"}
```

And line 35 contains the correct final answer:

```text
The mcp-geo MCP server running is version 0.8.1
```

Classification: Cowork transcript/rendering artifact or response-summary
truncation, not an MCP-Geo version defect.

### Finding 2: Postcode Lookup Worked

The transcript shows `os_places_by_postcode` called with:

```json
{"postcode":"CV3 1HB"}
```

The response contains 18 address/UPRN rows, including residential addresses,
`BINLEY ROAD SERVICE STATION`, `BULLS HEAD`, and `COVENTRY & NORTH
WARWICKSHIRE SPORTS CLUB`.

Classification: MCP-Geo OS Places path worked in Cowork.

### Finding 3: MCP-App Handoff Was Not Preserved

Cowork correctly recognized the MCP-App flow:

- line 94: it says it needs to use `os_resources.get`
- line 96: it identifies `resourceUri: "ui://mcp-geo/boundary-explorer"`
- lines 113-119: it calls `os_resources_get`

Then it stops after one page of the resource:

```text
The HTML content is very large (199KB). I need to get the entire HTML and create an artifact.
```

It then concludes:

```text
the boundary explorer is an MCP app that likely needs a server backend to function properly,
so it probably won't work as a standalone artifact
```

Classification: Cowork host/model handling problem. The MCP server returned a
valid app resource and valid pagination instructions. The client did not render
the MCP-App as an MCP-App, and did not keep following byte-offset chunks.

### Finding 4: Cowork Created a Non-MCP Map Artifact

Cowork then used `mcp__cowork__create_artifact` and generated an HTML map with:

```html
https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css
https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js
```

The model explicitly noticed that Leaflet was not in the allowed artifact CDN
list, then proceeded anyway:

```text
Only these libraries may be loaded ... Hmm, Leaflet is not in the allowed CDN list ...
Given the uncertainty ... I'll go ahead and build an HTML artifact with Leaflet and OpenStreetMap tiles
```

Classification: Cowork artifact/provenance failure. The final map is not an
MCP-Geo MCP-App rendering and is not a faithful OS-backed map output.

### Finding 5: Second Run Repeated the Same Fallback and Hit OSM Tile Policy

The second transcript (`mcp-cowork-fail2.md`) shows the same pattern:

- `ons_geo_by_postcode` succeeded for `CV3 1HB`.
- `os_places_by_postcode` succeeded and returned 18 UPRNs.
- `os_apps_render_boundary_explorer` was called.
- `os_resources_get` was called repeatedly and saw the 199,012 byte UI
  resource.
- Cowork explicitly recognized that `ui://mcp-geo/boundary-explorer` is meant
  to be rendered directly by the host.
- Cowork then pivoted and created `postcodes-cv3-1hb.html` anyway.

The generated `postcodes-cv3-1hb.html` is not an MCP-Geo output. It loads:

```html
https://unpkg.com/leaflet@1.9.4/dist/leaflet.css
https://unpkg.com/leaflet@1.9.4/dist/leaflet.js
https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
```

It also fetches nearby postcode data from:

```text
https://api.postcodes.io/postcodes?lon=...&lat=...&radius=1200&limit=100
```

The screenshot confirms the visible failure mode: OSM tile images are replaced
with "Access blocked" panels because the standalone file is using the volunteer
tile service in a way that trips the tile usage policy. This confirms a
client/model fallback failure, not a failure of the MCP-Geo MCP-App resource or
OS Places postcode lookup.

## Likely Root Causes

1. Docker Desktop likely started before `[EXTSSD_MOUNT_ROOT]` was available,
   so its Linux VM could not bind-mount the path even though macOS could see it.
2. The wrapper treats optional external data paths as safe to mount when they
   exist on macOS, but it does not preflight whether Docker Desktop can actually
   mount them.
3. Cowork does not currently treat `text/html;profile=mcp-app` resource
   handoff as a renderable app. It treats the resource as a large HTML payload
   to convert into a Cowork artifact.
4. The model then falls back to custom artifact generation rather than using
   `resourceHandoff`, `resolverTool=os_resources.get`, `protocolMethod=resources/read`,
   and byte-offset pagination as the app-delivery contract.
5. Standalone fallback maps introduce uncontrolled external dependencies
   (`unpkg`, OSM raster tiles, Postcodes.io), which breaks provenance and can
   fail independently of MCP-Geo.

## Before Restarting Claude Cowork

Do this order:

1. Keep `[EXTSSD_MOUNT_ROOT]` mounted.
2. If the mount probe fails again, restart Docker Desktop after the drive is
   mounted.
3. Verify Docker can mount the external data directory:

```bash
docker run --rm -v [EXTSSD_DATA_ROOT]:/mnt:ro alpine:3.20 sh -c 'ls -ld /mnt'
```

4. Verify the wrapper plan:

```bash
MCP_GEO_DOCKER_PLAN_ONLY=1 ./scripts/claude-mcp-local
```

5. Verify startup:

```bash
MCP_GEO_DOCKER_BUILD=never ./scripts/check_claude_startup_scope.sh
```

Known caveat: this checker may currently fail with equal `baseline_tools` and
`scoped_tools` because `.env` applies the default scope to both runs. That does
not mean the wrapper failed to start.

Then restart Claude Cowork. If you need the new MCP-App handoff guidance in the
Docker image immediately, rebuild the `mcp-geo-server` image once before
restarting Cowork.

## Post-Restart Cowork Test Prompt

Use this prompt in Claude Cowork to avoid a custom-artifact fallback:

```text
Use only MCP-Geo for this test.

1. Call os_mcp.descriptor and report server version, protocolVersion, and total tool count.
2. Call os_places.by_postcode for CV3 1HB and report only the UPRN count plus the first and last address.
3. Call os_apps.render_boundary_explorer for CV3 1HB / Binley Road, Coventry.
4. If the client can render MCP-Apps, render the MCP-App directly.
5. If it cannot render MCP-Apps, do not create a custom Leaflet/OpenStreetMap artifact. Instead report the resourceUri, resolverTool, resolverArgs, protocolMethod, mimeType, totalBytes, and nextPageToken from os_resources.get.
```

Expected result:

- version `0.8.1`
- protocol version `2025-11-25`
- 103 total tools
- 18 UPRNs for `CV3 1HB`
- app resource `ui://mcp-geo/boundary-explorer`
- no Cowork-created custom Leaflet/OpenStreetMap artifact

## Follow-Up Backlog

- Add a wrapper preflight or documented switch for optional external-data mounts
  so Docker Desktop mount drift does not prevent core MCP startup.
- Add a compact MCP-App smoke test that calls `os_apps.render_boundary_explorer`
  and `os_resources.get` with pagination, then records whether the host renders,
  chunks, or falls back.
- Fix `scripts/check_claude_startup_scope.sh` so its baseline run is not
  re-scoped by `.env`, or make the check explicitly report "already scoped"
  when active defaults produce equal counts.
- Add Cowork-specific guidance to `docs/troubleshooting.md`: if
  `text/html;profile=mcp-app` is not rendered by the client, preserve the
  resource handoff and do not fabricate a substitute map.
- Keep `postcodes-cv3-1hb.html` only as failure evidence. It should not be
  treated as a product artifact or committed as an MCP-Geo map output.
