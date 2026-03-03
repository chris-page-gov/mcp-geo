import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/compact_windows",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  retries: 0,
  reporter: [
    ["list"],
    ["json", { outputFile: "../research/map_delivery_research_2026-02/evidence/logs/playwright_compact_results.json" }],
  ],
  outputDir: "../research/map_delivery_research_2026-02/evidence/logs/playwright-compact-artifacts",
  use: {
    ...devices["Desktop Chrome"],
  },
});
