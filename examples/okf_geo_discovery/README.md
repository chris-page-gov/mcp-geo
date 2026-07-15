# OKF + MCP geospatial discovery demonstrator

This is a meeting-ready vertical slice for the proposed Ordnance Survey work package. It joins a
deterministic Open Knowledge Format snapshot to spatial discovery metadata and read-only MCP
bindings. The list shows the filtered candidate set; the Map tab applies an explicit spatial-
eligibility lens and reports both its mapped count and the originating candidate count.

The canonical packaged UI is `ui/okf_discovery.html`; this directory intentionally contains only
launch and extension guidance so there is no second copy of the application to drift.

For a key-free discussion surface that needs no local server, open
<https://chris-page-gov.github.io/mcp-geo/>. Its static discovery workspace uses the same checked-in
pack, previews the same MCP bindings and deliberately cannot execute live OS calls.

## Launch for the meeting

Start MCP Geo from the repository root:

```bash
OS_API_KEY_FILE="$HOME/.secrets/os_api_key" \
  .venv/bin/uvicorn server.main:app --host 127.0.0.1 --port 8000
```

That file-based launch is the verified meeting setup on the maintainer workstation. The server
reads the key at startup; it does not send the key to the browser or write it into the OKF pack.
If the file is unavailable, omit `OS_API_KEY_FILE` to exercise the key-free discovery fallback.

If the local virtual environment is unavailable, use:

```bash
OS_API_KEY_FILE="$HOME/.secrets/os_api_key" \
  uv run uvicorn server.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000/ui/okf-discovery>. The app loads the checked-in JSON over same-origin
HTTP, which is the simplest browser-demo route. No `OS_API_KEY` is needed for search, facets,
details, provenance, MCP request previews or spatial filtering.

With `OS_API_KEY` configured on the **server**, the map first uses the proxied OS VTS Light style.
Without it, the app visibly falls back to key-free OpenStreetMap context. No credential is read,
stored or sent by the browser code.

## Demonstration flow

1. Choose **Explorer House** under the search box. The result set surfaces the featured
   `os_places`, `os_features` and `os_linked_ids` families.
2. Refine by family, knowledge type, access mode or named geography.
3. Switch to **Map**. The map derives its records from the same filters, excludes candidates without
   a spatial profile, and reports the mapped subset against the original match count.
4. Enable **Filter results to this map view**, then pan away from and back to Explorer House to
   show location-aware discovery.
5. Choose `os_places.by_postcode`, `os_features.query` or `os_linked_ids.get` and inspect coverage,
   identifiers, geometry, CRS, spatial filters and provenance.
6. Under **Use via MCP**, reveal or copy the deterministic read-only `tools/call` request. The UI
   previews the binding; it deliberately does not execute it.

## Data and host contracts

The browser attempts the following static endpoints first:

- `/okf-discovery/data/records.json`
- `/okf-discovery/data/spatial-index.json`
- `/okf-discovery/data/mcp-bindings.json`

In an embedded MCP App, failed bearer-protected subfetches fall back to correlated JSON-RPC
`resources/read` calls for:

- `resource://mcp-geo/okf-discovery-records`
- `resource://mcp-geo/okf-discovery-spatial-index`
- `resource://mcp-geo/okf-discovery-mcp-bindings`

The loader tolerates both a raw records array (the OKF Explorer large-dataset shape) and the older
`{"records": [...]}` wrapper. It also tolerates MCP host responses using `data`,
`structuredContent`, `contents[].text`, `content[].json` or JSON `content[].text` wrappers.

Regenerate or check the deterministic snapshot with:

```bash
.venv/bin/python scripts/build_mcp_geo_okf.py
.venv/bin/python scripts/build_mcp_geo_okf.py --check
python scripts/build_okf_discovery_pages.py --output-dir _site
python scripts/build_okf_discovery_pages.py --output-dir _site --check
```

## Deliberate first-slice boundaries

- Explorer House is a sourced demo **query location**, not a dataset centroid or coverage extent.
- Great Britain is named coverage. The current viewport interaction asks which featured spatial
  profiles are applicable to the Explorer House journey; it does not pretend that a named extent
  is a precise boundary polygon.
- The postcode-to-UPRN journey uses the UPRN returned by OS Places. No UPRN is asserted for OS HQ
  in the checked-in example.
- The MCP panel exposes a read-only request contract and the documented `NO_API_KEY` failure mode;
  credentials and execution remain server concerns.

These boundaries create clean follow-up packages: add precise dataset extents and administrative
geometries, execute selected bindings with explicit confirmation, port the Map view into OKF
Explorer, and evaluate discovery quality with OS staff tasks.
