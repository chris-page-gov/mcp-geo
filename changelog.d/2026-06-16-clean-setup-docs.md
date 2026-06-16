## Fixed

- Corrected the first-run Docker STDIO smoke-test docs to send JSON-RPC requests
  with IDs and documented Docker credential-helper hangs seen during clean
  public-image pulls.
- Added a public OS Data Hub account setup checklist covering API project
  creation, secret-file configuration, Docker build, and live OS Names
  validation, using the OS Data Hub root URL and documenting OS Places as
  entitlement-dependent.
- Added first-run `.env` clarifications for raw Docker use, including
  `OS_API_KEY` versus `OS_API_KEY_FILE` precedence, secret-file mounts, quoted
  values, optional cache paths, and PostGIS/route-graph settings.
- Clarified LandIS setup levels: catalog/metadata works without PostGIS, while
  Soilscapes, NATMAP, NSI, and pipe-risk tools require a populated LandIS
  PostGIS warehouse.
- Added a full spatial LandIS warehouse setup guide covering the recommended
  MCP-Geo plus PostGIS topology, wrapper-managed bootstrap path, archive
  validation, row-count checks, repeatable clean tests, and when a separate
  LandIS MCP server would be justified.
