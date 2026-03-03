import { test, expect } from "@playwright/test";

import { UI_FILES, uiFileUrl } from "./support/ui_paths.js";
import { HOST_PROFILES } from "./support/host_profiles.js";
import { installMcpBridge } from "./support/mcp_bridge.js";
import {
  assertCompactGlobalContract,
  sendHostContextChanged,
  waitForCompactWidthAtMost,
} from "./support/compact_assertions.js";

const HOST_MATRIX = [
  ["vscode_inline_only_500", HOST_PROFILES.vscode_inline_only_500],
  ["claude_inline_500", HOST_PROFILES.claude_inline_500],
];

const UI_SELECTORS = {
  "boundary_explorer.html": { cta: "#searchButton", status: "#hostStatus", fullscreen: true },
  "geography_selector.html": { cta: "#searchButton", status: "#status", fullscreen: true },
  "statistics_dashboard.html": { cta: "#datasetSearchButton", status: "#status", fullscreen: true },
  "simple_map.html": { cta: "#loadBtn", status: "#status", fullscreen: false },
  "feature_inspector.html": { cta: "#loadFeature", status: "#statusBadge", fullscreen: true },
  "route_planner.html": { cta: "#calculateRoute", status: "#statusBadge", fullscreen: true },
};

test.describe("compact matrix acceptance", () => {
  for (const uiFile of UI_FILES) {
    for (const [profileName, profile] of HOST_MATRIX) {
      test(`${uiFile} renders compact contract (${profileName})`, async ({ page }) => {
        await installMcpBridge(page, {
          hostContext: profile,
          strictToolMatching: false,
        });

        await page.goto(uiFileUrl(uiFile), { waitUntil: "domcontentloaded" });

        const selectors = UI_SELECTORS[uiFile];
        await assertCompactGlobalContract(page, {
          ctaSelector: selectors.cta,
          statusSelector: selectors.status,
        });

        await sendHostContextChanged(page, {
          containerDimensions: { maxWidth: 320, maxHeight: 500 },
        });
        await waitForCompactWidthAtMost(page, 320);

        if (selectors.fullscreen) {
          const toggle = page.locator("#fullscreenToggle");
          await expect(toggle).toBeVisible();
          if (profileName === "vscode_inline_only_500") {
            await expect(toggle).toContainText("Try maximise");
          } else {
            await expect(toggle).toContainText("Maximise");
          }
        }

        await expect
          .poll(() =>
            page.evaluate(() => ({
              overflowX: document.body?.dataset?.overflowX || null,
              overflowPx: Number(document.body?.dataset?.overflowPx || "0"),
            }))
          )
          .toEqual({ overflowX: "false", overflowPx: 0 });
      });
    }
  }
});

test.describe("compact query override", () => {
  for (const uiFile of UI_FILES) {
    test(`${uiFile} forces compact with compact=1`, async ({ page }) => {
      await installMcpBridge(page, {
        hostContext: HOST_PROFILES.fullscreen_capable_desktop,
        strictToolMatching: false,
      });

      await page.setViewportSize({ width: 1200, height: 900 });
      await page.goto(`${uiFileUrl(uiFile)}?compact=1`, { waitUntil: "domcontentloaded" });

      await expect
        .poll(() =>
          page.evaluate(() => ({
            compact: document.body?.dataset?.compact || null,
            override: document.body?.dataset?.compactOverride || null,
          }))
        )
        .toEqual({ compact: "true", override: "true" });
    });

    test(`${uiFile} disables compact with compact=0`, async ({ page }) => {
      await installMcpBridge(page, {
        hostContext: HOST_PROFILES.claude_inline_500,
        strictToolMatching: false,
      });

      await page.setViewportSize({ width: 320, height: 500 });
      await page.goto(`${uiFileUrl(uiFile)}?compact=0`, { waitUntil: "domcontentloaded" });

      await expect
        .poll(() =>
          page.evaluate(() => ({
            compact: document.body?.dataset?.compact || null,
            override: document.body?.dataset?.compactOverride || null,
          }))
        )
        .toEqual({ compact: "false", override: "false" });
    });
  }
});
