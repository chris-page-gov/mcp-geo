import { test, expect } from "@playwright/test";
import path from "path";
import { pathToFileURL, fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test("statistics dashboard exposes deterministic compact flow states", async ({ page }) => {
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
            containerDimensions: { maxHeight: 700, maxWidth: 360 },
          },
        });
        return;
      }

      if (message.method !== "tools/call") {
        respond({});
        return;
      }

      const name = message.params?.name || message.params?.tool;
      const args = message.params?.arguments || {};

      if (name === "ons_search.query") {
        respond({
          results: [
            {
              id: "ds_test",
              title: "Test Dataset",
              description: "Compact dashboard test dataset",
              state: "published",
            },
          ],
          total: 1,
        });
        return;
      }

      if (name === "ons_data.editions") {
        respond({ editions: [{ id: "2026" }] });
        return;
      }

      if (name === "ons_data.versions") {
        respond({ versions: [{ id: "1" }] });
        return;
      }

      if (name === "ons_codes.list") {
        respond({ dimensions: ["geography", "measure", "time"] });
        return;
      }

      if (name === "ons_codes.options") {
        if (args.dimension === "geography") {
          respond({ options: ["E09000001", "E09000033"] });
          return;
        }
        if (args.dimension === "measure") {
          respond({ options: ["value"] });
          return;
        }
        if (args.dimension === "time") {
          respond({ options: ["2025", "2026"] });
          return;
        }
      }

      if (name === "ons_data.query") {
        const value = args.geography === "E09000001" ? 12.5 : 18.75;
        respond({ results: [{ observation: value }] });
        return;
      }

      if (name === "os_apps.log_event" || name === "os_apps_log_event") {
        respond({ status: "logged" });
        return;
      }

      respond({});
    });
  });

  const fileUrl = pathToFileURL(path.resolve(__dirname, "../../ui/statistics_dashboard.html")).href;
  await page.goto(fileUrl);

  await expect(page.locator("#status")).toContainText("Host connected");
  await expect(page.locator("#flowStatus")).toContainText("Idle");

  await page.fill("#datasetSearch", "housing");
  await page.click("#datasetSearchButton");
  await expect(page.locator("#flowStatus")).toContainText("Found 1 dataset result");
  await expect(page.locator("#datasetResults")).toContainText("ds_test");

  await page.click("#datasetResults .list-item");
  await expect(page.locator("#editionMeta")).toContainText("1 edition");
  await expect(page.locator("#versionMeta")).toContainText("1 version");
  await expect(page.locator("#dimensionMeta")).toContainText("Dimensions: 3");

  await page.click("#loadOptions");
  await expect(page.locator("#optionMeta")).toContainText("Areas: 2");

  await page.click("#geoOptions input[value='E09000001']");
  await page.click("#geoOptions input[value='E09000033']");
  await page.selectOption("#measureSelect", "value");
  await page.selectOption("#timeSelect", "2026");
  await page.click("#runQuery");

  await expect(page.locator("#flowStatus")).toContainText("Loaded 2 comparison result");
  await expect(page.locator("#resultTable tr")).toHaveCount(2);

  await page.selectOption("#timeSelect", "");
  await page.click("#runQuery");
  await expect(page.locator("#flowStatus")).toContainText("Complete all required fields");
  await expect(page.locator("#queryError")).toContainText("Pick dataset/edition/version");
});
