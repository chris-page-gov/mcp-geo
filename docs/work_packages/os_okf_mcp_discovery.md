# OS data discovery with OKF and MCP

Status: meeting demonstrator and proposed 4–6 week work package<br>
Prepared: 15 July 2026<br>
Meeting: Ordnance Survey, 09:00 Europe/London

## Decision and thesis

Take forward one vertical slice: **spatial discovery from an address to the data and
capabilities around it**.

The demonstrator should not try to reproduce Google Maps. It should expose the part of
Ordnance Survey's offer that a map alone cannot explain: authoritative data products,
identifiers, feature semantics, coverage, provenance, access routes and the operations that
can be performed over them.

The division of responsibility is deliberate:

- **Open Knowledge Format (OKF)** is the portable, deterministic discovery contract. It says
  what exists, how it can be searched or spatially filtered, where it came from, and how a
  selected record relates to a callable capability.
- **Model Context Protocol (MCP)** is the governed execution and delivery layer. It lets a
  client list and read the same pack, then invoke an existing read-only OS capability with
  credentials held by the server.
- **The viewer** is the human proof. Search, facets, list and map must operate on the same
  reduced candidate set, so the map is another discovery control rather than a separate
  presentation of unrelated results.

This makes the lifecycle from the earlier API-to-MCP talk tangible: **publish** authoritative
metadata into OKF; **discover** it through search, facets and space; **bind** a selected record to
an MCP contract; **execute** through an existing governed tool; and **audit** the sources,
arguments and outcome. MCP does not replace product, metadata or API governance—the OKF record
makes those decisions portable and visible before execution.

This is a useful work package because each layer remains independently valuable. The OKF pack
can be inspected without an OS credential; an MCP client can consume it without this viewer;
and the viewer can explain the data before a user decides to make a live API call.

## Implemented-now architecture

The branch establishes a deliberately small bridge rather than changing existing MCP tool
contracts.

```text
MCP tool registry ─┐
MCP resources ─────┼─ deterministic builder ─ OKF pack ─┬─ MCP resources/read
OS API catalogue ──┘                                     ├─ HTTP data assets
                                                        └─ discovery viewer

OKF selection ── okf-mcp-binding ── existing read-only MCP tool ── OS API
        └────── okf-geospatial ───── list/map/shared filters
```

The canonical generated pack is under `resources/okf_geo_discovery/`:

| Entry | Purpose | MCP resource URI |
| --- | --- | --- |
| `descriptor.json` | Portable OKF descriptor and extension declarations | `resource://mcp-geo/okf-discovery-descriptor` |
| `manifest.json` | Counts, entrypoints and integrity hashes | `resource://mcp-geo/okf-discovery-manifest` |
| `overview.json` | Small startup and facet summary | `resource://mcp-geo/okf-discovery-overview` |
| `records.json` | Searchable tool, resource and OS catalogue records | `resource://mcp-geo/okf-discovery-records` |
| `spatial-index.json` | Coverage, CRS, geometry and spatial-filter metadata | `resource://mcp-geo/okf-discovery-spatial-index` |
| `mcp-bindings.json` | Read-only MCP request templates and argument flows | `resource://mcp-geo/okf-discovery-mcp-bindings` |

The descriptor adds two external, optional extensions: `okf-geospatial.v1` and
`okf-mcp-binding.v1`. Keeping them outside the core record file lets an ordinary OKF consumer
ignore them, while a geospatial viewer or MCP client can opt in.

The checked-in `overview.json` currently reports:

- 404 searchable records: 103 MCP tools, 28 stable packaged/declared MCP resources and 273 OS
  API catalogue entries;
- 210 spatial profiles and 15 MCP bindings across `os_places`, `os_features` and
  `os_linked_ids`;
- 273 OS catalogue entries split into 186 features, 58 downloads, 14 search, 10 maps and 5
  positioning entries.

The six OKF resources and environment-specific cache/export instances are deliberately excluded
from the 28-resource stable source inventory. Optional runtime resource families remain declared
in the overview without snapshotting local filenames. This prevents the pack from changing merely
because its own output or a local cache exists. The builder makes no network calls, stores no
secret values and uses a fixed version snapshot timestamp rather than the wall clock; its integrity
hashes therefore support deterministic drift checking.

The pack is exposed through normal MCP resource listing and reading over HTTP and STDIO. The
registered UI resource is `ui://mcp-geo/okf-discovery`; `/okf-discovery` is the convenient
browser entry and redirects to `/ui/okf-discovery`. The data assets are an explicit six-file
allowlist and share the server's HTTP authentication boundary when authentication is enabled.

Live OS calls use the existing tools rather than a new demo-only endpoint. Binding records say
`credential_mode: server-managed`, never ask the client to supply an upstream key, and contain
no secret. If `OS_API_KEY` is not configured, the expected live-call response is HTTP 501 with
`{"isError": true, "code": "NO_API_KEY", ...}`. Discovery of the checked-in OKF pack remains
useful in that state.

The credentialled path was rehearsed successfully before the meeting; the key-safe status/count
evidence is recorded in the [15 July live rehearsal log](os_okf_mcp_live_rehearsal_2026-07-15.md).

## Why this is the missing layer, not a new direction

The repository's original build backlog already called for a discoverable tool/resource
registry, versioned provenance-bearing resources and a server guide translating user language
into tool sequences ([original build design](../build_initial_version.md)). Later work made the
remaining gap more explicit:

- the [OS catalogue delivery review](../reports/os_catalog_repo_usage_and_delivery_plan_2026-02-12.md)
  says the catalogue is organised by transport while user questions are domain-first, and
  proposes intent, overlap and delivery metadata;
- the [Boundary Explorer design](../../research/os_dataset_selection/initial_design_codex.md)
  proposes a layer catalogue to prevent dataset confusion while composing Places, Features and
  Linked Identifiers on a map;
- the [MCP Apps alignment](../mcp_apps_alignment.md) defines the `ui://`, `resources/read`,
  `tools/call` and deterministic fallback contracts that a host-integrated viewer must respect.

Those assets prove execution, cataloguing and map interaction separately. OKF supplies the
portable publication and discovery contract between them. Week 1 should not invent a new OS
taxonomy locally: OS staff should validate the authoritative product/API/collection sources and
the earlier proposed `surface`, `domain`, `preferredFor`, `overlapsWith` and `deliveryHint`
metadata. The pilot Map tab remains discovery-oriented; Boundary Explorer's feature inventory
and executable map recipes are a possible later consumer, not something this query-anchor map
pretends to provide.

## Six-minute Explorer House demonstration

The script uses returned values throughout. Do not put a guessed UPRN, TOID, feature identifier
or collection version on a slide or into the request.

### 0:00–0:45 — State the proposition

Open `/okf-discovery` and say:

> The map is not the product catalogue. OKF describes the authoritative data and capabilities;
> MCP provides a governed way to use them; this interface lets people and agents discover the
> same things.

Point out the current 404-record inventory and the three featured capability families. Explain
that the six pack files are portable JSON, not state hidden in the demo UI.

### 0:45–1:40 — Search and spatial discovery use one set

Search for `building`, select the OS Features family, then open the Map tab. The Map tab applies
an explicit map-eligible/spatial-profile facet and reports how many spatial records are mapped from
the wider text/facet matches. Move or narrow the map if the viewport control is enabled. Confirm
that the map feature `recordIds` and the Map-mode candidate IDs/count agree; do not imply that the
few metadata-only matches omitted from the map have geometry.

Open one result and show its source, coverage/CRS metadata and MCP binding. The useful thing is
not just where a feature is drawn, but how a user can discover and use the data behind it.

### 1:40–2:40 — Resolve a real address and UPRN

Call the binding for:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "os_places.by_postcode",
    "arguments": {"postcode": "SO16 0AS"}
  }
}
```

Select the appropriate Explorer House address from the returned `uprns` array. Copy only these
returned values into the next steps:

- `<UPRN_FROM_SELECTED_PLACES_RESULT>`
- `<LAT_FROM_SELECTED_PLACES_RESULT>`
- `<LON_FROM_SELECTED_PLACES_RESULT>`

Say explicitly that a postcode may return several addressable objects and that a UPRN identifies
an addressable object; neither should be treated as a building polygon.

### 2:40–4:15 — Discover the current NGD building collection and query nearby features

First discover, rather than guess, the live collection version:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "os_features.collections",
    "arguments": {"q": "building"}
  }
}
```

Choose `<LATEST_BUILDING_COLLECTION_ID_FROM_COLLECTIONS_RESULT>` from the returned
`latestByBaseId` mapping. Derive a small WGS84 bounding box around the returned Places point,
then call:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "os_features.query",
    "arguments": {
      "collection": "<LATEST_BUILDING_COLLECTION_ID_FROM_COLLECTIONS_RESULT>",
      "bbox": "<SMALL_BBOX_DERIVED_FROM_RETURNED_LON_LAT>",
      "includeGeometry": true,
      "limit": 20
    }
  }
}
```

Show the returned building geometries and their actual properties. The bbox uses longitude,
latitude order in `OGC:CRS84`; web display is EPSG:3857, while EPSG:27700 remains the normal
choice when British National Grid analysis is required.

Describe these as **near the selected address point**. Do not claim that a particular NGD
building feature is the addressable object unless an authoritative returned relationship proves
that join.

### 4:15–5:15 — Follow the authoritative identifier graph

Use the UPRN returned by Places:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "os_linked_ids.get",
    "arguments": {
      "identifier": "<UPRN_FROM_SELECTED_PLACES_RESULT>",
      "identifierType": "uprn"
    }
  }
}
```

Show only identifiers and relationship information present in the live response. A valid empty
or partial relationship result is preferable to an invented join: it makes coverage and
provenance visible, which is part of the value of the discovery contract.

### 5:15–6:00 — Close on the work-package decision

Return to the OKF record and its binding. Summarise:

1. OKF made the OS product, spatial semantics and callable route discoverable.
2. MCP executed a read-only route without moving an OS credential into the client or pack.
3. OS Places, NGD features and linked identifiers showed the depth of the data behind the map.

If a credential or upstream API is unavailable, stop after showing the request template and the
documented `NO_API_KEY` contract. The key-free discovery flow is the rehearsed fallback, not a
reason to fabricate a live result.

## Proposed 4–6 week work package

### Outcome

Deliver a reusable, measured OS discovery vertical slice in which a person and an MCP client can
find the same OS data capability by text, metadata or location; understand its authority and
access conditions; and execute a safe read-only route using returned identifiers.

### Stages and gates

| Stage | Indicative time | Deliverables | Exit gate |
| --- | --- | --- | --- |
| 0. Joint discovery contract | Week 1 | Three priority user tasks; authoritative metadata/source register; agreed terms for product, dataset, collection, feature and operation; agreed Explorer House scenario and access route; baseline and numeric targets for time-to-correct-selection, correct-product rate or another OS-owned outcome | OS product, API, data-governance and user-research owners approve scope, sources, baseline and target measures |
| 1. Production-shaped OKF profile | Weeks 1–2 | Versioned geospatial and MCP-binding schemas; product/API/collection mappings; coverage, CRS, licence, access, currency/vintage and identifier fields; deterministic build and validation | Two consecutive builds are byte-identical; every required field is present or explicitly `unknown` with provenance; no secret values; integrity check passes |
| 2. Governed MCP vertical slice | Weeks 2–3 | HTTP and STDIO resource delivery; Places → NGD Features → Linked Identifiers binding flow; dynamic collection-version discovery; normalized errors and audit/provenance evidence | A fresh client can list/read the pack and run the four-step script with server-managed credentials; missing credentials return `NO_API_KEY`; no client or generated artifact contains an upstream key |
| 3. OKF Explorer map integration | Weeks 3–4 | Map tab in the OKF Explorer repository; shared filter state; synchronized list/map selection; spatial viewport filter; coverage-versus-feature rendering; stable deep links | Given the same query state, list and map expose exactly the same stable record IDs and count; a copied URL restores query, facets, viewport and selected record; key-free fallback remains usable |
| 4. OS staff pilot and hardening | Week 5 | Task-based usability trial, accessibility/browser checks, performance budget, source freshness/withdrawal handling, licence and security review, operational runbook | Target users complete the agreed discovery tasks without facilitator intervention and meet the Stage 0 numeric target; all incorrect or ambiguous provenance/identifier claims are resolved; error and no-result paths pass |
| 5. Optional scale and handoff | Week 6 | Larger OS corpus, spatial-index performance work, release/versioning policy, maintenance owners, adoption roadmap and reusable reference pack | OS and OKF maintainers accept ownership boundaries, update cadence, release artefacts and a measured next-product backlog |

Stage 4 is the minimum complete package. Week 6 is an explicit scale/handoff option, not hidden
contingency for finishing the core vertical slice.

### Acceptance criteria

The package is accepted when all of the following are evidenced:

1. A user can find each of the three featured families by text, facet and a geographic route,
   and can distinguish a data product, API operation and returned feature.
2. For every query state, the list and map have the same reduced candidate IDs; selection in
   either view selects the same record in the other.
3. A clean MCP client can list and read all six OKF resources over both supported transports,
   verify the manifest hashes and follow a binding to an existing tool.
4. The Explorer House script selects an address and UPRN from the live Places response, resolves
   a current building collection from `latestByBaseId`, queries geometry around the returned
   point, and reports Linked Identifiers exactly as returned. Zero-result paths remain truthful.
5. Every surfaced record carries a source and access statement; spatial records carry explicit
   scope, CRS and geometry/coverage meaning; time-sensitive records carry a vintage or an
   explicit unknown/staleness state.
6. Rebuilding from the same registries produces identical bytes. A changed registry causes a
   reviewed, explainable pack diff rather than silent runtime drift.
7. No OKF file, browser request or client argument contains an OS secret. Live access uses
   server-managed credentials and the shared normalized error contract.
8. The desktop browser flow, keyboard path, map pan/zoom, label readability, deep links and
   key-free fallback pass the agreed acceptance test.

### OKF Explorer follow-up: the map is a filter, not a fork

The durable follow-up belongs in the OKF Explorer repository. Add a `Map` tab as a view over the
Explorer's existing result pipeline rather than building a second geospatial search engine.

The invariant should be:

```text
all records
  ∩ text query
  ∩ ordinary facets
  ∩ records with matching spatial semantics
  ∩ optional map viewport / drawn geometry
= one reduced candidate set used by list, map, count and details
```

Stable OKF record IDs are the join key between views. Search text, facets, viewport/drawn geometry
and selection should remain in the URL query/hash so links are reproducible. The map must
visually distinguish product coverage from returned feature geometry and point locations. It
should default to a label-safe OS vector basemap when the deployment has the permitted
server-side access route, with a neutral/key-free fallback that still shows analytical overlays.

Start with the external `spatial-index.json` profile and bounding boxes. Add more expensive
geometry or vector-tile indexing only when corpus size and measured interaction latency require
it. This preserves OKF portability and gives non-geospatial packs no new mandatory burden.

## Current limitations and honest boundaries

- This is an exemplar profile, not a ratified OKF geospatial or MCP-binding standard.
- The 273-entry OS catalogue is the repository's checked-in source snapshot. Product currency,
  withdrawal dates, licences and access tiers require joint verification against OS's current
  systems of record before external publication.
- The 210 spatial profiles combine runtime or checked-in endpoint schemas with curated
  family-level semantics. The UI labels family geometry/CRS separately from operation output;
  Explorer House markers are query anchors, not authoritative record extents or feature geometry.
- The viewer in this repository proves the interaction; it is not yet the reusable Map tab in
  the separate OKF Explorer codebase.
- The checked-in viewer can discover request templates, but a host-mediated live-call experience
  and durable audit display remain follow-up work.
- Live OS calls depend on the server's configured OS credential and upstream availability. The
  OKF pack and key-free discovery path are intentionally independent of those calls.
- A spatial NGD building result near an address point and a Linked Identifiers result for its
  UPRN are separate evidence lanes. The demonstrator must not imply a direct UPRN-to-building
  relationship unless OS returns one.
- OS Places, OS Features and OS Linked Identifiers cover Great Britain in this profile; it must
  not be described as complete UK coverage.
- The example binding currently demonstrates a building alias. The live presentation should
  resolve and use the current collection ID returned by `os_features.collections`.
- Scale, spatial-index performance, accessibility and cross-host MCP-App behaviour still require
  measured acceptance testing.

## Ordered follow-ups if time remains before 09:00

Each checkpoint leaves a demonstrable stopping point. Do not start the next group until the
previous one is green.

### If 15 minutes remain — freeze a reliable key-free demo

1. Run the deterministic generator in check mode and the targeted generator/resource/UI tests.
2. Start the server and smoke-test `/okf-discovery`, all six resource reads, list/map switching,
   search, facets, details, static assets, ETags and the no-key state.
3. Rehearse the first two minutes and keep `overview.json` plus `mcp-bindings.json` open as the
   browser-independent fallback.

Stop here with a portable pack, visible UI and accurate talk track.

### If 30 minutes remain — add live evidence and rehearse the chain

4. Through the configured server route, run postcode, collection discovery, bounded feature
   query and Linked Identifiers once. Keep returned identifiers only in temporary speaker notes;
   do not commit them as timeless examples and do not expose the credential.
5. Verify the selected current collection and the exact response paths used by the placeholders.
6. Rehearse the complete six-minute script once with live access and once with the
   `NO_API_KEY`/upstream-unavailable fallback.

Stop here with one verified live journey and a fallback that tells the same architectural story.

### If 60 minutes remain — turn the demo into acceptance evidence

7. Add or complete a browser assertion that list and map contain the same record IDs after a
   combined text, family and viewport filter; verify desktop map pan, zoom and label readability.
8. Exercise MCP `resources/list` and `resources/read` over HTTP and STDIO, including an integrity
   check and an authenticated-route case when auth is enabled.
9. Capture a short result log containing only statuses, counts, source/vintage metadata and
   placeholder labels—not secrets or reusable live identifiers—and record any failed acceptance
   criterion in the backlog.
10. Freeze structural changes at least 15 minutes before the meeting and use the final period for
    browser reset, window layout and rehearsal.

Only after those checks should work begin on the cross-repository OKF Explorer Map tab.

## Questions for Ordnance Survey staff

### Discovery problem and users

1. Which three discovery tasks currently fail most often: finding a product, finding the right
   API/operation, understanding feature content, checking coverage/currency, or joining IDs?
2. Who is the first user: an OS customer, internal support/product staff, data engineers,
   analysts, application developers, or an AI agent acting for one of them?
3. Where does discovery currently break between the website, Data Hub, technical docs, product
   catalogues and API responses?

### Authority and metadata

4. What is the authoritative system of record for products, datasets, NGD collections, API
   operations, versions/withdrawals, licence/access tiers and geographic coverage?
5. Which distinctions must OKF preserve between product, dataset, collection, feature type,
   API operation and download?
6. Which fields best express OS's advantage over a general web map: currency, lineage,
   completeness, feature semantics, identifiers, precision, change history, legal status or
   service guarantees?
7. Can unknown, partial, retired and credential-restricted coverage be exposed explicitly rather
   than omitted?

### Geospatial and identifier journey

8. Is Explorer House the right stable vertical slice, and what returned relationship would OS
   regard as authoritative between its address UPRN, nearby NGD building features and linked
   identifiers?
9. Should discovery default to WGS84 for web/API interaction while preserving British National
   Grid and source CRS metadata for analysis?
10. Which collection/version-discovery behaviour is stable enough for clients, and how should a
    pack represent superseded or scheduled-for-withdrawal collections?

### MCP, access and viewer

11. What does the current OS MCP server already expose, which clients/hosts matter, and which tool
    or resource contracts are expected to remain stable?
12. Can the pilot use a server-managed demonstration credential, and what rate limits, test
    environments, licence text and logging constraints must the acceptance test observe?
13. May the viewer use the OS vector basemap in the pilot, and what attribution, styling, caching
    and screenshot/demo rules apply?
14. Should selecting a record merely prepare a binding, or should the first pilot execute the
    call in the MCP host with an explicit user action and visible provenance/audit evidence?

### Success and ownership

15. What measurable outcome would justify continuing: discovery time, fewer support requests,
    API activation, correct product selection, agent task success, or reuse of OS identifiers?
16. Who would own the OKF export, schema/profile decisions, MCP contract, Explorer integration,
    metadata quality and release cadence after the pilot?
17. Which additional product family should be the first test of generalisation after Places,
    NGD Features and Linked Identifiers?
