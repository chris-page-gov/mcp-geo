import { test, expect } from "@playwright/test";
import path from "path";
import { pathToFileURL, fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test("route planner performs MCP host handshake and deterministic route planning", async ({ page }) => {
  await page.addInitScript(() => {
    window.addEventListener("message", (event) => {
      const message = event.data;
      if (!message || message.jsonrpc !== "2.0" || message.id === undefined) {
        return;
      }

      const respond = (result) => {
        window.postMessage({ jsonrpc: "2.0", id: message.id, result }, "*");
      };

      if (message.method === "ui/initialize") {
        respond({
          protocolVersion: "2026-01-26",
          hostContext: {
            displayMode: "inline",
            availableDisplayModes: ["inline", "fullscreen"],
            platform: "web",
            userAgent: "playwright",
            containerDimensions: { maxHeight: 500, maxWidth: 360 },
          },
        });
        return;
      }

      if (message.method === "ui/request-display-mode") {
        respond({ mode: message.params?.mode || "inline" });
        return;
      }

      if (message.method === "tools/call") {
        const name = message.params?.name || message.params?.tool;
        if (name === "os_apps.log_event" || name === "os_apps_log_event") {
          respond({ status: "logged" });
          return;
        }
      }

      respond({});
    });
  });

  const fileUrl = pathToFileURL(path.resolve(__dirname, "../../ui/route_planner.html")).href;
  await page.goto(fileUrl);

  await expect(page.locator("#statusBadge")).toContainText("Host connected");
  await expect(page.locator("#fullscreenToggle")).toContainText("Maximise");

  await page.fill("#startInput", "51.500,-0.120");
  await page.fill("#endInput", "51.510,-0.100");
  await page.selectOption("#routeMode", "walk");
  await page.click("#calculateRoute");

  await expect(page.locator("#flowStatus")).toContainText("Route ready");
  await expect(page.locator("#payload")).toContainText('"mode": "walk"');
  await expect(page.locator("#routeSteps")).toContainText("Estimated duration");

  await page.fill("#startInput", "invalid");
  await page.click("#calculateRoute");
  await expect(page.locator("#flowStatus")).toContainText("lat,lon");
});
