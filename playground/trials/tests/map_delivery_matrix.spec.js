import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "../../..");
const evidenceRoot = path.join(
  repoRoot,
  "research",
  "map_delivery_research_2026-02",
  "evidence"
);
const screenshotDir = path.join(evidenceRoot, "screenshots");
const logDir = path.join(evidenceRoot, "logs");
const trialLogPath = path.join(logDir, "playwright_trials_observations.jsonl");
const syntheticTilePath = path.join(repoRoot, "playground/trials/fixtures/synthetic_osm_tile.png");

function ensureEvidenceDirs() {
  fs.mkdirSync(screenshotDir, { recursive: true });
  fs.mkdirSync(logDir, { recursive: true });
}

function safeSegment(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function writeObservation(testInfo, trialId, details) {
  ensureEvidenceDirs();
  const record = {
    timestamp: new Date().toISOString(),
    browser: testInfo.project.name,
    trialId,
    title: testInfo.title,
    status: testInfo.status,
    details,
  };
  fs.appendFileSync(trialLogPath, `${JSON.stringify(record)}\n`, "utf-8");
}

async function captureEvidence(page, testInfo, label) {
  ensureEvidenceDirs();
  const project = safeSegment(testInfo.project.name);
  const testLabel = safeSegment(label);
  const fileName = `${project}-${testLabel}.png`;
  const outputPath = path.join(screenshotDir, fileName);
  await page.screenshot({ path: outputPath, fullPage: true });
  return outputPath;
}

async function captureMapPanel(page, testInfo, label, selector = "#map") {
  ensureEvidenceDirs();
  const project = safeSegment(testInfo.project.name);
  const testLabel = safeSegment(label);
  const fileName = `${project}-${testLabel}-map-panel.png`;
  const outputPath = path.join(screenshotDir, fileName);
  await page.locator(selector).screenshot({ path: outputPath });
  return outputPath;
}

async function mcpCall(request, payload, sessionId = null) {
  const headers = { "content-type": "application/json" };
  if (sessionId) {
    headers["mcp-session-id"] = sessionId;
  }
  const response = await request.post("http://127.0.0.1:8000/mcp", {
    headers,
    data: payload,
  });
  expect(response.ok()).toBeTruthy();
  return {
    body: await response.json(),
    headers: response.headers(),
  };
}

test.beforeAll(() => {
  ensureEvidenceDirs();
  expect(fs.existsSync(syntheticTilePath)).toBeTruthy();
});

test("trial-1 static osm proxy map renders in browser", async ({ page }, testInfo) => {
  const staticMapUrl =
    "http://127.0.0.1:8000/maps/static/osm?bbox=-0.18,51.49,-0.05,51.54&size=640&zoom=13";
  await page.setContent(
    `<main style="margin:0;padding:16px;font-family:system-ui;background:#f3f5f7">
      <h1 style="font-size:16px;margin:0 0 12px">Trial 1 - Static OSM Proxy</h1>
      <img id="map" src="${staticMapUrl}" alt="Static map trial" style="border:1px solid #ccd4dd;max-width:100%;" />
    </main>`
  );
  await page.waitForFunction(() => {
    const map = document.getElementById("map");
    return Boolean(map && map.complete && map.naturalWidth > 0 && map.naturalHeight > 0);
  });
  const dimensions = await page.evaluate(() => {
    const map = document.getElementById("map");
    return {
      width: map?.naturalWidth ?? 0,
      height: map?.naturalHeight ?? 0,
    };
  });
  expect(dimensions.width).toBeGreaterThan(100);
  expect(dimensions.height).toBeGreaterThan(100);
  const screenshot = await captureEvidence(page, testInfo, "trial-1-static-osm");
  writeObservation(testInfo, "trial-1-static-osm", {
    dimensions,
    mapUrl: staticMapUrl,
    screenshot,
  });
});

test("trial-2 os_maps.render tool output produces renderable image", async (
  { request, page },
  testInfo
) => {
  const init = await mcpCall(request, {
    jsonrpc: "2.0",
    id: "trial-init",
    method: "initialize",
    params: { protocolVersion: "2025-11-25", capabilities: {} },
  });
  const sessionId = init.headers["mcp-session-id"];
  expect(sessionId).toBeTruthy();

  const renderCall = await mcpCall(
    request,
    {
      jsonrpc: "2.0",
      id: "trial-render",
      method: "tools/call",
      params: {
        name: "os_maps.render",
        arguments: {
          bbox: [-0.18, 51.49, -0.05, 51.54],
          size: 640,
          zoom: 13,
          layers: ["light"],
        },
      },
    },
    sessionId
  );

  expect(renderCall.body?.result?.ok).toBeTruthy();
  const imagePath = renderCall.body?.result?.data?.render?.imageUrl;
  expect(typeof imagePath).toBe("string");

  const absoluteUrl = new URL(imagePath, "http://127.0.0.1:8000").toString();
  await page.setContent(
    `<main style="margin:0;padding:16px;font-family:system-ui;background:#f7f8fa">
      <h1 style="font-size:16px;margin:0 0 12px">Trial 2 - os_maps.render</h1>
      <img id="map" src="${absoluteUrl}" alt="Tool map output" style="border:1px solid #ccd4dd;max-width:100%;" />
    </main>`
  );
  await page.waitForFunction(() => {
    const map = document.getElementById("map");
    return Boolean(map && map.complete && map.naturalWidth > 0 && map.naturalHeight > 0);
  });
  const dimensions = await page.evaluate(() => {
    const map = document.getElementById("map");
    return {
      width: map?.naturalWidth ?? 0,
      height: map?.naturalHeight ?? 0,
    };
  });
  expect(dimensions.width).toBeGreaterThan(100);
  expect(dimensions.height).toBeGreaterThan(100);
  const screenshot = await captureEvidence(page, testInfo, "trial-2-os-maps-render");
  writeObservation(testInfo, "trial-2-os-maps-render", {
    sessionId,
    imagePath,
    absoluteUrl,
    dimensions,
    screenshot,
  });
});

test("trial-3 geography selector map persists overlays after style switch", async (
  { page },
  testInfo
) => {
  test.skip(
    testInfo.project.name !== "chromium-desktop",
    "Widget host emulation is validated in Chromium for deterministic file:// behavior."
  );
  await page.addInitScript(() => {
    const addressResults = [
      {
        uprn: "1000000001",
        address: "1 Trial Street",
        lat: 51.5,
        lon: -0.12,
        classificationDescription: "Residential",
      },
      {
        uprn: "1000000002",
        address: "2 Trial Street",
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
          respond({ results: addressResults });
          return;
        }
        if (name === "os_apps.log_event" || name === "os_apps_log_event") {
          respond({ status: "logged" });
          return;
        }
        if (name === "admin_lookup.containing_areas" || name === "admin_lookup_containing_areas") {
          respond({ results: [] });
          return;
        }
        if (name === "admin_lookup.area_geometry" || name === "admin_lookup_area_geometry") {
          respond({});
          return;
        }
        respond({});
      }
    });
  });

  const workerPath = path.resolve(repoRoot, "ui/vendor/maplibre-gl-csp-worker.js");
  const workerBody = fs.readFileSync(workerPath, "utf-8");
  const syntheticTile = fs.readFileSync(syntheticTilePath);

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

  await page.route("**/maps/vector/vts/resources/styles**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        version: 8,
        sources: {
          synthetic_osm: {
            type: "raster",
            tiles: ["http://localhost:8000/maps/raster/osm/{z}/{x}/{y}.png"],
            tileSize: 256,
          },
        },
        layers: [{ id: "synthetic-osm", type: "raster", source: "synthetic_osm" }],
      }),
    });
  });

  const fileUrl = pathToFileURL(path.resolve(repoRoot, "ui/geography_selector.html")).href;
  await page.goto(fileUrl);
  await expect(page.locator("#status")).toContainText("Host connected");

  await page.fill("#queryInput", "Trial");
  await page.click("#searchButton");

  await page.waitForFunction(() => {
    const el = document.getElementById("diagnostics");
    if (!el) {
      return false;
    }
    try {
      const data = JSON.parse(el.textContent || "{}");
      return (
        data?.data?.addressPoints >= 2 &&
        data?.sources?.ready === true &&
        data?.rendered?.addresses >= 2 &&
        data?.mapLoaded === true &&
        data?.lastMapError === null
      );
    } catch {
      return false;
    }
  });

  // Validate overlays survive a post-render style switch.
  await page.selectOption("#mapStyleSelect", "osm");
  await page.waitForFunction(() => {
    const el = document.getElementById("diagnostics");
    if (!el) {
      return false;
    }
    try {
      const data = JSON.parse(el.textContent || "{}");
      return (
        data?.data?.addressPoints >= 2 &&
        data?.sources?.ready === true &&
        data?.rendered?.addresses >= 2 &&
        data?.style === "osm" &&
        data?.mapLoaded === true &&
        data?.lastMapError === null
      );
    } catch {
      return false;
    }
  });
  await expect(page.locator("#debugBadges")).not.toContainText("Error:");

  const screenshot = await captureEvidence(page, testInfo, "trial-3-geography-selector");
  const mapPanel = await captureMapPanel(page, testInfo, "trial-3-geography-selector");
  writeObservation(testInfo, "trial-3-geography-selector", {
    screenshot,
    mapPanel,
    style: "osm",
    switchAfterOverlay: true,
    page: "ui/geography_selector.html",
  });
});

test("trial-4 boundary explorer imports local layers and highlights matches", async (
  { page },
  testInfo
) => {
  test.skip(
    testInfo.project.name !== "chromium-desktop",
    "Widget host emulation is validated in Chromium for deterministic file:// behavior."
  );
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

  const workerPath = path.resolve(repoRoot, "ui/vendor/maplibre-gl-csp-worker.js");
  const workerBody = fs.readFileSync(workerPath, "utf-8");
  const syntheticTile = fs.readFileSync(syntheticTilePath);

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

  const fileUrl = pathToFileURL(path.resolve(repoRoot, "ui/boundary_explorer.html")).href;
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
          coordinates: [
            [
              [-0.121, 51.5045],
              [-0.119, 51.5045],
              [-0.119, 51.5062],
              [-0.121, 51.5062],
              [-0.121, 51.5045],
            ],
          ],
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
        coordinates: [
          [
            [-0.121, 51.5045],
            [-0.119, 51.5045],
            [-0.119, 51.5062],
            [-0.121, 51.5062],
            [-0.121, 51.5045],
          ],
        ],
      },
    });
  });

  await expect(page.locator("#infoBanner")).toContainText("Selected by local layer");
  await expect(page.locator("#highlightCount")).toHaveText("2");
  await page.waitForFunction(() => {
    const canvas = document.querySelector("#map canvas.maplibregl-canvas");
    return Boolean(canvas && canvas.width > 10 && canvas.height > 10);
  });

  const screenshot = await captureEvidence(page, testInfo, "trial-4-boundary-explorer");
  const mapPanel = await captureMapPanel(page, testInfo, "trial-4-boundary-explorer");
  writeObservation(testInfo, "trial-4-boundary-explorer", {
    screenshot,
    mapPanel,
    style: "osm",
    highlightedUprns: 2,
  });
});
