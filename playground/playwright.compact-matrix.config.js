import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/compact_windows",
  testMatch: ["**/*matrix*.spec.js"],
  timeout: 90_000,
  expect: {
    timeout: 12_000,
  },
  retries: 0,
  reporter: [
    ["list"],
    [
      "json",
      {
        outputFile:
          "../research/map_delivery_research_2026-02/evidence/logs/playwright_compact_matrix_results.json",
      },
    ],
  ],
  outputDir: "../research/map_delivery_research_2026-02/evidence/logs/playwright-compact-matrix-artifacts",
  projects: [
    {
      name: "chromium-compact-320x500",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 320, height: 500 },
      },
    },
    {
      name: "chromium-compact-360x500",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 360, height: 500 },
      },
    },
    {
      name: "firefox-compact-320x500",
      use: {
        ...devices["Desktop Firefox"],
        viewport: { width: 320, height: 500 },
      },
    },
  ],
});
