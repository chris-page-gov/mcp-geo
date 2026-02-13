import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { pathToFileURL, fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test("boundary explorer imports GeoJSON and Shapefile.zip local layers and applies polygon selection", async ({
  page,
}) => {
  await page.addInitScript(() => {
    const inventory = {
      layers: {
        uprns: {
          results: [
            {
              uprn: "1000000001",
              lat: 51.505,
              lon: -0.12,
              address: "1 Test Street, London SW1A 1AA",
            },
            {
              uprn: "1000000002",
              lat: 51.5052,
              lon: -0.1198,
              address: "2 Test Street, London SW1A 1AA",
            },
          ],
        },
        buildings: { features: [] },
        road_links: { features: [] },
        path_links: { features: [] },
      },
    };
    window.addEventListener("message", (event) => {
      const message = event.data;
      if (!message || message.jsonrpc !== "2.0") {
        return;
      }
      if (message.id === undefined) {
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
            containerDimensions: { maxHeight: 760 },
            mcpGeo: { proxyBase: "http://localhost:8000" },
          },
        });
        return;
      }
      if (message.method === "tools/call") {
        const name = message.params?.name || message.params?.tool;
        if (name === "os_map.inventory" || name === "os_map_inventory") {
          respond(inventory);
          return;
        }
        if (name === "os_apps.log_event" || name === "os_apps_log_event") {
          respond({ status: "logged" });
          return;
        }
        respond({});
      }
    });
  });

  const workerPath = path.resolve(__dirname, "../../ui/vendor/maplibre-gl-csp-worker.js");
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

  await page.route("**/shpjs@4.0.4/**/shp.min.js*", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/javascript",
      body: `
window.shp = async function () {
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { source: "zip-layer" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-0.121,51.5045],[-0.119,51.5045],[-0.119,51.5062],[-0.121,51.5062],[-0.121,51.5045]]]
        }
      }
    ]
  };
};
      `,
    });
  });

  const fileUrl = pathToFileURL(path.resolve(__dirname, "../../ui/boundary_explorer.html")).href;
  await page.goto(fileUrl);

  await expect(page.locator("#hostStatus")).toContainText("Host connected");
  await page.click("#refreshInventory");
  await page.waitForFunction(() => {
    const el = document.getElementById("highlightCount");
    return el && Number(el.textContent || "0") === 0;
  });

  const polygonGeoJson = JSON.stringify({
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { source: "geojson-layer" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-0.121, 51.5045], [-0.119, 51.5045], [-0.119, 51.5062], [-0.121, 51.5062], [-0.121, 51.5045]]],
        },
      },
    ],
  });

  await page.setInputFiles("#fileInput", {
    name: "selection.geojson",
    mimeType: "application/geo+json",
    buffer: Buffer.from(polygonGeoJson, "utf-8"),
  });
  await expect(page.locator("#localLayers")).toContainText("selection.geojson");

  await page.setInputFiles("#fileInput", {
    name: "selection.zip",
    mimeType: "application/zip",
    buffer: Buffer.from("PK-test", "utf-8"),
  });
  await expect(page.locator("#localLayers")).toContainText("selection.zip");

  await page.evaluate(() => {
    window.applyLocalLayerSelection({
      type: "Feature",
      properties: { source: "test-selection" },
      geometry: {
        type: "Polygon",
        coordinates: [[[-0.121, 51.5045], [-0.119, 51.5045], [-0.119, 51.5062], [-0.121, 51.5062], [-0.121, 51.5045]]],
      },
    });
  });
  await expect(page.locator("#infoBanner")).toContainText("Selected by local layer");
  await expect(page.locator("#highlightCount")).toHaveText("2");
});
