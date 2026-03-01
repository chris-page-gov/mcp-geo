import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

function setRangeValue(page, selector, value) {
  return page.evaluate(
    ({ target, nextValue }) => {
      const element = document.querySelector(target);
      if (!element) {
        return false;
      }
      element.value = String(nextValue);
      element.dispatchEvent(new Event("input", { bubbles: true }));
      return true;
    },
    { target: selector, nextValue: value }
  );
}

test("boundary explorer exposes style controls, cache status, and timeout guidance", async ({ page }) => {
  await page.addInitScript(() => {
    const inventoryPayload = {
      bbox: [-1.538, 52.414, -1.536, 52.416],
      layers: {
        uprns: {
          count: 2,
          results: [
            {
              uprn: "1000000001",
              lat: 52.4148,
              lon: -1.5373,
              address: "1 Test Road, Coventry CV1 1AA",
            },
            {
              uprn: "1000000002",
              lat: 52.4147,
              lon: -1.5369,
              address: "2 Test Road, Coventry CV1 1AA",
            },
          ],
        },
        buildings: {
          features: [
            {
              id: "building-1",
              type: "Feature",
              properties: {},
              geometry: {
                type: "Polygon",
                coordinates: [
                  [
                    [-1.53745, 52.41472],
                    [-1.53715, 52.41472],
                    [-1.53715, 52.41496],
                    [-1.53745, 52.41496],
                    [-1.53745, 52.41472],
                  ],
                ],
              },
            },
          ],
        },
        road_links: {
          features: [
            {
              id: "road-1",
              type: "Feature",
              properties: {},
              geometry: {
                type: "LineString",
                coordinates: [
                  [-1.5378, 52.41465],
                  [-1.5365, 52.4149],
                ],
              },
            },
          ],
        },
        path_links: {
          features: [
            {
              id: "path-1",
              type: "Feature",
              properties: {},
              geometry: {
                type: "LineString",
                coordinates: [
                  [-1.5377, 52.41495],
                  [-1.5368, 52.4152],
                ],
              },
            },
          ],
        },
      },
    };

    window.__inventoryMode = "ok";
    window.__messages = [];

    window.addEventListener("message", (event) => {
      const message = event.data;
      if (!message || message.jsonrpc !== "2.0" || message.id === undefined) {
        return;
      }
      window.__messages.push(message.method || "");
      const respond = (result) => {
        window.postMessage({ jsonrpc: "2.0", id: message.id, result }, "*");
      };
      const respondError = (errorMessage) => {
        window.postMessage(
          {
            jsonrpc: "2.0",
            id: message.id,
            error: { code: -32000, message: errorMessage },
          },
          "*"
        );
      };

      if (message.method === "ui/initialize") {
        respond({
          protocolVersion: "2026-01-26",
          hostContext: {
            displayMode: "inline",
            availableDisplayModes: ["inline", "fullscreen"],
            platform: "web",
            userAgent: "playwright",
            containerDimensions: { maxHeight: 760 },
            mcpGeo: { proxyBase: "http://localhost:8000" },
          },
        });
        return;
      }

      if (message.method === "ui/request-display-mode") {
        respond({ mode: "inline" });
        return;
      }

      if (message.method !== "tools/call") {
        respond({});
        return;
      }

      const rawName = message.params?.name || message.params?.tool || "";
      const name = String(rawName).replaceAll(".", "_");

      if (name === "os_apps_log_event") {
        respond({ status: "logged" });
        return;
      }

      if (name === "admin_lookup_find_by_name") {
        respond({
          results: [
            {
              id: "E05001229",
              level: "WARD",
              name: "Sherbourne",
              bbox: [-1.538, 52.414, -1.536, 52.416],
              geometry: {
                rings: [
                  [
                    [-1.538, 52.414],
                    [-1.536, 52.414],
                    [-1.536, 52.416],
                    [-1.538, 52.416],
                    [-1.538, 52.414],
                  ],
                ],
              },
            },
          ],
          count: 1,
          live: true,
        });
        return;
      }

      if (name === "admin_lookup_area_geometry") {
        respond({
          id: "E05001229",
          level: "WARD",
          name: "Sherbourne",
          bbox: [-1.538, 52.414, -1.536, 52.416],
          geometry: {
            rings: [
              [
                [-1.538, 52.414],
                [-1.536, 52.414],
                [-1.536, 52.416],
                [-1.538, 52.416],
                [-1.538, 52.414],
              ],
            ],
          },
        });
        return;
      }

      if (name === "admin_lookup_get_cache_status") {
        respond({
          cacheEnabled: true,
          total: 240783,
          maturity: { label: "ready" },
          performance: { degraded: false, reason: null, impact: null },
        });
        return;
      }

      if (name === "ons_geo_cache_status") {
        respond({
          available: true,
          rowCount: 31000000,
          lastRefreshed: "2026-02-28T08:30:00Z",
          performance: { degraded: false, reason: null, impact: null },
        });
        return;
      }

      if (name === "os_map_inventory") {
        if (window.__inventoryMode === "timeout_error") {
          respondError("RPC timeout");
          return;
        }
        respond(inventoryPayload);
        return;
      }

      if (name === "os_map_export") {
        respond({ uri: "resource://mcp-geo/os-exports/mock.json" });
        return;
      }

      respond({});
    });
  });

  const workerPath = path.resolve(__dirname, "../../ui/vendor/maplibre-gl-csp-worker.js");
  const workerBody = fs.readFileSync(workerPath, "utf-8");
  const syntheticTile = Buffer.from(
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
      body: syntheticTile,
    });
  });

  const fileUrl = pathToFileURL(path.resolve(__dirname, "../../ui/boundary_explorer.html")).href;
  await page.goto(fileUrl);

  await expect(page.locator("#hostStatus")).toContainText("Host connected");
  await expect(page.locator("#layerBoundaryFill")).not.toBeChecked();

  await page.fill("#searchInput", "Sherbourne");
  await page.click("#searchButton");
  await page.waitForSelector(".result");
  await page.click(".result [data-action='toggle']");

  await page.waitForFunction(() => {
    const probe = window.__MCP_GEO_BOUNDARY_EXPLORER__;
    if (!probe || typeof probe.getSnapshot !== "function") {
      return false;
    }
    return probe.getSnapshot()?.selection?.selectedCount === 1;
  });

  let snapshot = await page.evaluate(() => window.__MCP_GEO_BOUNDARY_EXPLORER__.getSnapshot());
  expect(snapshot.layers.areaFill).toBeFalsy();

  await page.check("#layerBoundaryFill");
  await setRangeValue(page, "#boundaryFillOpacity", 0.3);
  await page.waitForTimeout(120);
  snapshot = await page.evaluate(() => window.__MCP_GEO_BOUNDARY_EXPLORER__.getSnapshot());
  expect(snapshot.layers.areaFill).toBeTruthy();
  expect(snapshot.styleControls.boundaryFillOpacity).toBeCloseTo(0.3, 2);
  await expect(page.locator("#boundaryFillOpacityValue")).toHaveText("0.30");

  await setRangeValue(page, "#basemapOpacity", 0.08);
  await expect(page.locator("#basemapOpacityValue")).toHaveText("0.08");

  await page.check("#layerBuildings");
  await page.check("#layerRoads");
  await page.check("#layerPaths");
  await page.click("#refreshInventory");
  await page.waitForFunction(() => {
    const probe = window.__MCP_GEO_BOUNDARY_EXPLORER__;
    if (!probe || typeof probe.getSnapshot !== "function") {
      return false;
    }
    const snapshot = probe.getSnapshot();
    return snapshot?.sourceCounts?.uprns === 2;
  });
  await expect(page.locator("#guidancePanel")).toContainText("OS connectivity looks healthy");

  await page.click("#refreshCacheStatus");
  await expect(page.locator("#cacheStatus")).toContainText("Boundary cache");
  await expect(page.locator("#cacheStatus")).toContainText("ONS geo cache");
  await expect(page.locator("#cacheStatus")).toContainText("records=240783");

  await page.evaluate(() => {
    window.__inventoryMode = "timeout_error";
  });
  await page.click("#refreshInventory");
  await expect(page.locator("#infoBanner")).toContainText("Inventory request failed: RPC timeout");
  await expect(page.locator("#guidancePanel")).toContainText("Latest inventory issue: RPC timeout");
});
