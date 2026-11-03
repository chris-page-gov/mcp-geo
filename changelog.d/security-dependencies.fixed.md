- Refresh the playground's MCP client, Zod, Vite and affected transitive
  dependencies to versions outside the reviewed Dependabot ranges. Keep the
  Python geospatial server, provider policy and live-service configuration
  unchanged. Allow the full synthetic browser suite to select an installed
  browser through `PLAYWRIGHT_CHANNEL`.
- Emit standard MCP text content alongside structured fixture output so the
  SDK's response validation remains enabled during full browser tests.
- Pin the frontend CI runner to Ubuntu 24.04, which the existing pinned
  Playwright browser supports; the moving runner alias selected unsupported
  Ubuntu 26.04 before the suite could start.
