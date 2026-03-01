import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { pathToFileURL, fileURLToPath } from "url";

test("geography selector keeps dots after style switch", async ({ page }) => {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  await page.addInitScript(() => {
    const addressResults = [
      {
        uprn: "1000000001",
        address: "1 Test Street",
        lat: 51.5,
        lon: -0.12,
        classificationDescription: "Residential",
      },
      {
        uprn: "1000000002",
        address: "2 Test Street",
        lat: 51.501,
        lon: -0.121,
        classificationDescription: "Residential",
      },
    ];
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
            containerDimensions: { maxHeight: 700 },
            mcpGeo: { proxyBase: "http://localhost:8000" },
          },
        });
        return;
      }
      if (message.method === "tools/call") {
        const name = message.params?.name || message.params?.tool;
        if (name === "os_places.search") {
          // Simulate clients that sanitize tool names (e.g. disallow ".").
          window.postMessage(
            {
              jsonrpc: "2.0",
              id: message.id,
              error: { code: -32000, message: "Tool not found on server: os_places.search" },
            },
            "*"
          );
          return;
        }
        if (name === "os_places_search") {
          respond({
            structuredContent: { results: addressResults },
            content: [{ type: "json", json: { results: addressResults } }],
          });
          return;
        }
        if (name === "os_apps.log_event") {
          respond({ status: "logged" });
          return;
        }
        if (name === "admin_lookup.containing_areas") {
          respond({ results: [] });
          return;
        }
        if (name === "admin_lookup.area_geometry") {
          respond({});
          return;
        }
        respond({});
      }
    });
  });

  const workerPath = path.resolve(
    __dirname,
    "../../ui/vendor/maplibre-gl-csp-worker.js"
  );
  const workerBody = fs.readFileSync(workerPath, "utf-8");
  const emptyPng = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=",
    "base64"
  );

  await page.route("**/maps/worker/maplibre-gl-csp-worker.js", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/javascript",
      body: workerBody,
    });
  });

  await page.route("**/maps/raster/osm/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "image/png",
      body: emptyPng,
    });
  });

  await page.route("**/maps/vector/vts/resources/styles**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        version: 8,
        sources: {},
        layers: [
          {
            id: "background",
            type: "background",
            paint: { "background-color": "#f3f0e9" },
          },
        ],
      }),
    });
  });

  const fileUrl = pathToFileURL(
    path.resolve(__dirname, "../../ui/geography_selector.html")
  ).href;
  await page.goto(fileUrl);

  await expect(page.locator("#status")).toContainText("Host connected");

  await page.fill("#queryInput", "Test");
  await page.click("#searchButton");
  await expect(page.locator("#flowStatus")).toContainText("Found");

  await page.waitForFunction(() => {
    const el = document.getElementById("diagnostics");
    if (!el) {
      return false;
    }
    try {
      const data = JSON.parse(el.textContent || "{}");
      return data?.data?.addressPoints >= 2;
    } catch {
      return false;
    }
  });

  await page.$eval("#mapOpacity", (el) => {
    el.value = "0.15";
    el.dispatchEvent(new Event("input", { bubbles: true }));
  });
  await page.waitForFunction(() => {
    const el = document.getElementById("diagnostics");
    if (!el) {
      return false;
    }
    try {
      const data = JSON.parse(el.textContent || "{}");
      return Number(data?.opacity) === 0.15;
    } catch {
      return false;
    }
  });

  await page.click("[data-testid='layer-toggle-input-addresses']");
  await page.waitForFunction(() => {
    const el = document.getElementById("diagnostics");
    if (!el) {
      return false;
    }
    try {
      const data = JSON.parse(el.textContent || "{}");
      return data?.layerVisibility?.addresses === false;
    } catch {
      return false;
    }
  });
  await page.click("[data-testid='layer-toggle-input-addresses']");

  await page.selectOption("#mapStyleSelect", "os_OS_VTS_3857_Light.json");

  await page.waitForFunction(() => {
    const el = document.getElementById("diagnostics");
    if (!el) {
      return false;
    }
    try {
      const data = JSON.parse(el.textContent || "{}");
      return data?.data?.addressPoints >= 2;
    } catch {
      return false;
    }
  });

  // Capture map rendering for regression coverage
  await expect(page.locator("#map")).toBeVisible();
  await expect(page.locator("#map")).toHaveScreenshot("geography-selector-map.png", {
    maxDiffPixelRatio: 0.015,
  });
});
