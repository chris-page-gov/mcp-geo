import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./trials/tests",
  timeout: 90_000,
  expect: {
    timeout: 15_000,
  },
  retries: 0,
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile:
          "../research/map_delivery_research_2026-02/evidence/logs/playwright_trials_results.json",
      },
    ],
  ],
  outputDir: "../research/map_delivery_research_2026-02/evidence/logs/playwright-artifacts",
  use: {
    baseURL: "http://127.0.0.1:8000",
    viewport: { width: 1400, height: 900 },
  },
  projects: [
    {
      name: "chromium-desktop",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox-desktop",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit-desktop",
      use: { ...devices["Desktop Safari"] },
    },
    {
      name: "chromium-mobile",
      use: { ...devices["Pixel 7"] },
    },
    {
      name: "webkit-mobile",
      use: { ...devices["iPhone 13"] },
    },
  ],
  webServer: {
    command:
      "cd .. && (./.venv/bin/python -m uvicorn server.main:app --host 127.0.0.1 --port 8000 --log-level warning || python3 -m uvicorn server.main:app --host 127.0.0.1 --port 8000 --log-level warning)",
    port: 8000,
    timeout: 120_000,
    reuseExistingServer: true,
  },
});
