# Docker MCP Catalog Submission

This note captures the repo-local choices for publishing MCP-Geo to Docker's
MCP catalog and Docker Desktop MCP Toolkit.

Primary references:

- <https://github.com/docker/mcp-registry/blob/main/README.md>
- <https://github.com/docker/mcp-registry/blob/main/CONTRIBUTING.md>
- <https://github.com/docker/mcp-registry/blob/main/add_mcp_server.md>
- <https://github.com/docker/mcp-registry/blob/main/.github/PULL_REQUEST_TEMPLATE.md>
- <https://github.com/docker/mcp-registry/blob/main/cmd/validate/main.go>

## Publication Path

- Submission type: Docker-built local server
- Registry image name: `mcp/mcp-geo`
- Catalog category: `search`
- Security contact model: GitHub Private Vulnerability Reporting

## Repo Readiness Before Submission

- Root `LICENSE` file present and GitHub shows the repo as MIT-licensed.
- `SECURITY.md` present and GitHub Private Vulnerability Reporting is enabled.
- Docker-facing docs mention `OS_API_KEY` as the required live credential.
- `README.md`, `docs/Build.md`, and `docs/getting_started.md` align on the same
  setup story.

## Draft `server.yaml`

```yaml
name: mcp-geo
image: mcp/mcp-geo
type: server
meta:
  category: search
  tags:
    - geospatial
    - uk-data
    - ordnance-survey
    - ons
    - nomis
    - maps
about:
  title: UK Geography and Statistics
  description: Query UK geographies, boundaries, routing, and official statistics from Ordnance Survey, ONS, and NOMIS.
  icon: https://avatars.githubusercontent.com/u/121984645?v=4
source:
  project: https://github.com/chris-page-gov/mcp-geo
  commit: <replace-with-merged-sha>
config:
  description: Configure live Ordnance Survey access for geospatial queries. NOMIS credentials are optional and only needed for higher-rate statistical access.
  secrets:
    - name: mcp-geo.os_api_key
      env: OS_API_KEY
      example: <OS_API_KEY>
    - name: mcp-geo.nomis_uid
      env: NOMIS_UID
      required: false
      example: <NOMIS_UID>
    - name: mcp-geo.nomis_signature
      env: NOMIS_SIGNATURE
      required: false
      example: <NOMIS_SIGNATURE>
```

Notes:

- Do not use `MCP` or `Server` in `about.title`; Docker's validator rejects
  those title patterns.
- Do not expose `OS_API_KEY_FILE` in the catalog entry; the catalog UI is
  secret-oriented, so `OS_API_KEY` is the supported input.
- Do not add a `run` block unless Docker's validation tooling proves the image
  needs explicit overrides.
- Do not add `tools.json` unless `task build -- --tools mcp-geo` fails. MCP-Geo
  already lists tools without secrets, so a static tool snapshot should stay a
  fallback, not the source of truth.

## Submission Validation

In a checkout of `docker/mcp-registry`:

```bash
task validate -- --name mcp-geo
task build -- --tools mcp-geo
task catalog -- mcp-geo
docker mcp catalog import $PWD/catalogs/mcp-geo/catalog.yaml
```

After import:

- Enable the server in Docker Desktop MCP Toolkit.
- Confirm tool discovery succeeds without secrets.
- Confirm one OS-backed tool works with a review key.
- Share a low-privilege OS review key with Docker if they request live-call
  validation beyond tool discovery.
