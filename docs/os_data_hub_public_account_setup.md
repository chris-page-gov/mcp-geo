# OS Data Hub public-account setup for MCP-Geo

Last checked: 2026-06-16

This guide is for validating MCP-Geo with a normal OS Data Hub account, as a
member of the public, using the minimum setup needed for the first live
named-place lookup.

## What you need

- A web browser and an email address you can verify.
- Docker installed and running.
- Git installed.
- A local clone of this repository, or permission to clone it.

Do not paste OS API keys into chat, GitHub issues, committed files, or shared
logs. Prefer the `OS_API_KEY_FILE` setup below.

## 1. Create the OS Data Hub account

1. Open the OS Data Hub root:
   <https://osdatahub.os.uk/>
2. Create a new account.
3. Complete the email verification and any terms/registration prompts.
4. Log in to the OS Data Hub.

The account by itself is not enough for API calls. OS API credentials are
created inside an API project.

## 2. Create an API project and key

1. In OS Data Hub, open **API Dashboard**.
2. Open **APIs** in the secondary navigation.
3. Find **OS Names API**.
4. Click **Add to API project**.
5. Choose **Add to NEW PROJECT**.
6. Name the project, for example `mcp-geo-public-test`.
7. Create the project.
8. On the project page, copy the **Project API Key**.

For MCP-Geo's first OS Names smoke test, the Project API Key is enough. You do
not need the Project API Secret unless you intentionally switch to bearer /
OAuth authentication.

Current public/free account testing found **OS Places API** unavailable in the
API list. Do not use OS Places as the first public-account smoke test. The
MCP-Geo `os_places_*` postcode/address/UPRN tools require an OS Places API
entitlement and should be treated as a later licensed-account validation path.

If you later use more OS-backed MCP-Geo tools, add the matching available OS API
to the same project so the same Project API Key is authorised for it. Useful
additions for broader testing include:

- **OS Linked Identifiers API** for linked identifier lookups.
- **OS Net API** for OS Net workflows.
- **OS Downloads API** for OS Downloads API workflows.
- **OS NGD API - Features** for NGD feature queries.
- **OS Vector Tile API**, **OS Features API**, or **OS Maps API** for map,
  tile, and feature workflows when those are available to the account.

If the OS Data Hub does not offer one of those APIs to the account, record that
as an account/product entitlement finding rather than an MCP-Geo install
failure.

## 3. Clone MCP-Geo

```bash
git clone https://github.com/chris-page-gov/mcp-geo.git
cd mcp-geo
cp .env.example .env
```

If you are testing from an existing clone, start from the repository root and
ensure `.env` exists:

```bash
cp -n .env.example .env
```

## 4. Store the API key locally

Create a private local secret file:

```bash
mkdir -p ~/.secrets
chmod 700 ~/.secrets
nano ~/.secrets/os_api_key
chmod 600 ~/.secrets/os_api_key
```

Paste only the Project API Key into `~/.secrets/os_api_key`. The file should
contain the key and no `OS_API_KEY=` prefix.

Then edit `.env` in the repo and set:

```text
OS_API_KEY_FILE=/Users/YOUR_USER/.secrets/os_api_key
OS_API_AUTH_MODE=query
```

Replace `/Users/YOUR_USER` with the real absolute path on the test machine.
Leave `OS_API_KEY=` unset unless you deliberately want to store the key inline
in `.env`.

Important `.env` rules for Docker:

- Set **either** `OS_API_KEY_FILE` **or** `OS_API_KEY`, not both. Do not rely
  on precedence. In a bare server environment, a non-empty `OS_API_KEY`
  prevents MCP-Geo from reading `OS_API_KEY_FILE`.
- Do not wrap values in quote marks in `.env` when using `docker run --env-file`.
  Docker passes quotes through as part of the value. For example,
  `OS_API_KEY="abc"` sends `"abc"` to MCP-Geo, not `abc`.
- Do not use smart quotes around secrets or paths.
- Keep optional cache/log path settings commented for the first test. Bare
  `docker run` does not automatically mount host directories such as
  `/Users/<you>/Library/Application Support/mcp-geo`.
- `ROUTE_GRAPH_DSN`, `BOUNDARY_CACHE_DSN`, and PostGIS are not required for the
  OS Names smoke test. Leave route-graph and boundary-cache settings disabled
  until you intentionally test routing or cached boundary workflows.

For a bare `docker run`, the host secret file must also be mounted into the
container. The commands below mount `~/.secrets/os_api_key` at the same absolute
path so the `OS_API_KEY_FILE` value in `.env` works inside the container.

## 5. Build the Docker image

```bash
docker build -t mcp-geo-server .
```

If the build hangs at `load metadata for docker.io/library/python:3.11-slim` or
`docker pull` reports `error getting credentials`, test with a temporary clean
Docker config:

```bash
mkdir -p /tmp/mcp-geo-docker-config
DOCKER_CONFIG=/tmp/mcp-geo-docker-config docker pull python:3.11-slim
DOCKER_CONFIG=/tmp/mcp-geo-docker-config docker build -t mcp-geo-server .
```

If the temporary config works, the repository build is healthy and the machine
has a Docker Desktop credential-helper problem to repair.

## 6. Smoke-test MCP discovery

Send a JSON-RPC request with an `id`:

```bash
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  | docker run --rm -i --env-file .env \
      -v "$HOME/.secrets/os_api_key:$HOME/.secrets/os_api_key:ro" \
      mcp-geo-server
```

Expected result: JSON output containing `result.tools`.

If there is no output, check that the request includes `"id":1`. Requests
without an `id` are JSON-RPC notifications and the STDIO adapter correctly does
not reply.

## 7. Smoke-test the OS Names API key

```bash
REQUEST='{"jsonrpc":"2.0","id":2,"method":"tools/call","params":'\
'{"name":"os_names_find","arguments":{"text":"Oxford","limit":5}}}'
printf '%s\n' "$REQUEST" \
  | docker run --rm -i --env-file .env \
      -v "$HOME/.secrets/os_api_key:$HOME/.secrets/os_api_key:ro" \
      mcp-geo-server
```

Expected result: JSON output with `ok:true` or named-place results for Oxford.

Common failures:

- `NO_API_KEY`: MCP-Geo could not see a key. Check that `.env` has the
  correct absolute `OS_API_KEY_FILE`, the file exists, and Docker can read the
  path. With bare `docker run`, also check that the secret file is mounted with
  `-v`.
- `OS_API_KEY_INVALID`: OS rejected the key. Check that the key was copied
  correctly, **OS Names API** was added to the project, and the key has not
  been regenerated or revoked. Also check that `.env` does not contain quote
  marks or smart quotes around `OS_API_KEY`.
- `OS_API_ERROR`: OS returned another upstream error. Inspect the response
  message, OS service status, quota, and API entitlement.
- No output: the STDIO request was a notification or is waiting for input.
  Include a JSON-RPC `id`, keep `-i`, and send exactly one newline-terminated
  JSON object.

## 8. Optional licensed-account OS Places validation

Only run this section if the account can add **OS Places API** to the project.
In public/free account testing, OS Places was not available.

```bash
REQUEST='{"jsonrpc":"2.0","id":3,"method":"tools/call","params":'\
'{"name":"os_places_by_postcode","arguments":{"postcode":"SW1A 1AA"}}}'
printf '%s\n' "$REQUEST" \
  | docker run --rm -i --env-file .env \
      -v "$HOME/.secrets/os_api_key:$HOME/.secrets/os_api_key:ro" \
      mcp-geo-server
```

Expected result: JSON output with `ok:true` or address/place results for the
postcode. If this returns `OS_API_KEY_INVALID`, confirm that **OS Places API**
was actually added to the project and is available to the account.

## 9. LandIS validation

LandIS has two different setup levels:

- Metadata/discovery only: no PostGIS warehouse is required. These tools use
  checked-in registry/archive metadata and should work in the basic Docker
  image: `landis_catalog_list_products`, `landis_metadata_get`,
  `landis_archive_list_items`, and `landis_archive_get_item`.
- Spatial LandIS answers: PostGIS is required, and it must be populated with
  normalized LandIS tables. This includes `landis_soilscapes_point`,
  `landis_soilscapes_area_summary`, `landis_natmap_point`,
  `landis_natmap_area_summary`, `landis_natmap_thematic_area_summary`,
  `landis_nsi_nearest_sites`, `landis_nsi_within_area`,
  `landis_nsi_profile_summary`, and `landis_derive_pipe_risk`.

For a full LandIS system, use the dedicated spatial warehouse guide:
[LandIS full spatial warehouse setup](landis_spatial_warehouse_setup.md). That
is the recommended path for Stephen's LandIS testing.

The first LandIS smoke test can stay metadata-only:

```bash
REQUEST='{"jsonrpc":"2.0","id":4,"method":"tools/call","params":'\
'{"name":"landis_catalog_list_products","arguments":{"limit":5}}}'
printf '%s\n' "$REQUEST" \
  | docker run --rm -i --env-file .env \
      -v "$HOME/.secrets/os_api_key:$HOME/.secrets/os_api_key:ro" \
      mcp-geo-server
```

If the goal is to query Soilscapes, NATMAP, NSI, or derived pipe risk at a
point/area, use a repo wrapper such as `scripts/claude-mcp-local` rather than a
bare `docker run`. The wrapper starts the PostGIS sidecar and can bootstrap the
LandIS warehouse from a configured local LandIS data root. On first start that
bootstrap can take materially longer than normal because it loads spatial
tables.

Minimum concepts for the spatial path:

- `LANDIS_WAREHOUSE_DSN` points MCP-Geo at the PostGIS warehouse. If unset,
  LandIS falls back to `BOUNDARY_CACHE_DSN` when available.
- `ROUTE_GRAPH_DSN` is for routing/pgRouting and is not the LandIS warehouse
  setting.
- `LANDIS_LOCAL_DATA_ROOT` points at the host directory containing the local
  LandIS mirror/archive, commonly `~/Data`.
- The warehouse must be populated by the LandIS ingest scripts or by the
  wrapper bootstrap. An empty PostGIS database is not enough.

## 10. Hand off for live validation

When asking another tool or agent to validate the setup, provide only the
secret-file path, not the key value. For example:

```text
The OS key is in /Users/YOUR_USER/.secrets/os_api_key. Use OS_API_KEY_FILE, not
an inline OS_API_KEY.
```

For repo wrapper scripts such as `scripts/claude-mcp-local`, the host-side
`OS_API_KEY_FILE` can be read before the container starts, so the wrapper path
does not need the manual `-v` secret-file mount shown above.

## References

- OS API project setup:
  <https://docs.os.uk/os-apis/core-concepts/getting-started-with-an-api-project>
- OS API authentication modes:
  <https://docs.os.uk/os-apis/core-concepts/authentication>
- OS Names API overview:
  <https://docs.os.uk/os-apis/accessing-os-apis/os-names-api>
- OS Linked Identifiers API overview:
  <https://docs.os.uk/os-apis/accessing-os-apis/os-linked-identifiers-api>
