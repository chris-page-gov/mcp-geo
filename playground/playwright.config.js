import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  use: {
    baseURL: "http://localhost:4173"
  },
  webServer: {
    command: "npm run dev -- --host 0.0.0.0 --port 4173 --strictPort",
    port: 4173,
    reuseExistingServer: true
  }
});
