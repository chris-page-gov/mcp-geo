import { test, expect } from "@playwright/test";
import { uiFileUrl } from "./support/ui_paths.js";
import { HOST_PROFILES } from "./support/host_profiles.js";
import { installBasicMcpBridge } from "./support/mcp_bridge.js";

test.describe("compact matrix scaffold", () => {
  test("boundary explorer loads at matrix viewport", async ({ page }) => {
    await installBasicMcpBridge(page, HOST_PROFILES.vscode_inline_only_500);
    await page.goto(uiFileUrl("boundary_explorer.html"), { waitUntil: "domcontentloaded" });
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("geography selector loads at matrix viewport", async ({ page }) => {
    await installBasicMcpBridge(page, HOST_PROFILES.vscode_inline_only_500);
    await page.goto(uiFileUrl("geography_selector.html"), { waitUntil: "domcontentloaded" });
    await expect(page.locator("body")).toBeVisible();
  });
});
