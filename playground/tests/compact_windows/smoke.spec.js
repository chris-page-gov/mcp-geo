import { test, expect } from "@playwright/test";
import { UI_FILES, uiFileUrl } from "./support/ui_paths.js";
import { HOST_PROFILES } from "./support/host_profiles.js";
import { installBasicMcpBridge } from "./support/mcp_bridge.js";

test.describe("compact suite scaffold smoke", () => {
  for (const file of UI_FILES) {
    test(`loads ${file} with deterministic bridge`, async ({ page }) => {
      await installBasicMcpBridge(page, HOST_PROFILES.claude_inline_500);
      await page.goto(uiFileUrl(file), { waitUntil: "domcontentloaded" });
      await expect(page.locator("body")).toBeVisible();
    });
  }
});
