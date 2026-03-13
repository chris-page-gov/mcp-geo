import { defineConfig, devices } from "@playwright/test";

const backendPort = Number(process.env.PLAYGROUND_FIXTURE_PORT || 8787);
const frontendPort = Number(process.env.PLAYGROUND_FULL_FRONTEND_PORT || 4173);

export default defineConfig({
  testDir: "./tests/full",
  timeout: 90_000,
  workers: 1,
  expect: {
    timeout: 15_000,
  },
  retries: 0,
  reporter: [["list"]],
  outputDir: "test-results/full",
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
      command: "node tests/support/fixture_server.mjs",
      port: backendPort,
      reuseExistingServer: true,
      timeout: 60_000,
      env: {
        PLAYGROUND_FIXTURE_PORT: String(backendPort),
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
