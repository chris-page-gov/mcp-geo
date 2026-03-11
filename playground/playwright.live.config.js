import { defineConfig, devices } from "@playwright/test";

const backendPort = Number(process.env.PLAYGROUND_LIVE_BACKEND_PORT || 8010);
const frontendPort = Number(process.env.PLAYGROUND_LIVE_FRONTEND_PORT || 4174);
const auditPackRoot = process.env.PLAYGROUND_LIVE_AUDIT_PACK_ROOT || "/tmp/mcp-geo-playwright-live-audit";
const backendCommand =
  `cd .. && (` +
  `./.venv/bin/python -m uvicorn server.main:app --host 127.0.0.1 --port ${backendPort} --log-level warning` +
  ` || python3 -m uvicorn server.main:app --host 127.0.0.1 --port ${backendPort} --log-level warning` +
  `)`;

export default defineConfig({
  testDir: "./tests/live",
  timeout: 120_000,
  workers: 1,
  expect: {
    timeout: 20_000,
  },
  retries: 0,
  reporter: [["list"]],
  outputDir: "test-results/live",
  use: {
    ...devices["Desktop Chrome"],
    baseURL: `http://127.0.0.1:${frontendPort}`,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure",
    viewport: { width: 1440, height: 960 },
  },
  webServer: [
    {
      command: backendCommand,
      port: backendPort,
      reuseExistingServer: true,
      timeout: 120_000,
      env: {
        AUDIT_PACK_ROOT: auditPackRoot,
        OS_API_KEY: process.env.OS_API_KEY || "",
        ONS_API_KEY: process.env.ONS_API_KEY || "",
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort} --strictPort`,
      port: frontendPort,
      reuseExistingServer: true,
      timeout: 60_000,
      env: {
        VITE_PROXY_TARGET: `http://127.0.0.1:${backendPort}`,
      },
    },
  ],
});
