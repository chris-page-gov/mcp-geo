import { test, expect } from "@playwright/test";
import path from "path";
import { pathToFileURL, fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test("feature inspector performs MCP host handshake and linked-id load", async ({ page }) => {
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
            availableDisplayModes: ["inline"],
            platform: "web",
            userAgent: "playwright",
            containerDimensions: { maxHeight: 500, maxWidth: 360 },
          },
        });
        return;
      }

      if (message.method === "tools/call") {
        const name = message.params?.name || message.params?.tool;
        if (name === "os_linked_ids.get" || name === "os_linked_ids_get") {
          respond({ toid: "osgb123", uprn: "1000000099", usrn: "200000001" });
          return;
        }
        if (name === "os_apps.log_event" || name === "os_apps_log_event") {
          respond({ status: "logged" });
          return;
        }
      }

      if (message.method === "ui/request-display-mode") {
        respond({ mode: "inline" });
        return;
      }

      respond({});
    });
  });

  const fileUrl = pathToFileURL(path.resolve(__dirname, "../../ui/feature_inspector.html")).href;
  await page.goto(fileUrl);

  await expect(page.locator("#statusBadge")).toContainText("Host connected");
  await expect(page.locator("#fullscreenToggle")).toContainText("Try maximise");

  await page.fill("#identifierInput", "1000000099");
  await page.selectOption("#identifierType", "uprn");
  await page.click("#loadFeature");

  await expect(page.locator("#statusBadge")).toContainText("Feature loaded");
  await expect(page.locator("#toidChip")).toContainText("osgb123");
  await expect(page.locator("#uprnChip")).toContainText("1000000099");
  await expect(page.locator("#usrnChip")).toContainText("200000001");
});
