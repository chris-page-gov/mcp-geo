import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";
import {
  installDeterministicHostBridge,
  loadHostCapabilityProfiles,
  profileById,
  roundTripUiInitialize,
} from "./support/host_simulation.js";

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
const hostProfileCatalog = loadHostCapabilityProfiles(repoRoot);
const codexIdeProfile = profileById(hostProfileCatalog, "codex_ide_ui");
const codexCliProfile = profileById(hostProfileCatalog, "codex_cli_stdio");
const claudePartialProfile = profileById(hostProfileCatalog, "claude_desktop_ui_partial");

const LATENCY_BUDGETS_MS = {
  "trial-1-static-osm": { desktop: 8_000, mobile: 12_000 },
  "trial-2-os-maps-render": { desktop: 10_000, mobile: 14_000 },
  "trial-3-geography-selector": { desktop: 16_000, mobile: 22_000 },
  "trial-4-boundary-explorer": { desktop: 20_000, mobile: 28_000 },
  "trial-5-host-simulation": { desktop: 4_000, mobile: 6_000 },
};

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

function latencyBudgetMs(testInfo, trialId) {
  const isMobile = testInfo.project.name.includes("mobile");
  const budgetByClass = LATENCY_BUDGETS_MS[trialId] || {
    desktop: 8_000,
    mobile: 12_000,
  };
  return isMobile ? budgetByClass.mobile : budgetByClass.desktop;
}

function latencyDetails(testInfo, trialId, startedAtMs) {
  const latencyMs = Date.now() - startedAtMs;
  const latencyBudget = latencyBudgetMs(testInfo, trialId);
  expect(latencyMs).toBeLessThanOrEqual(latencyBudget);
  return {
    latencyMs,
    latencyBudgetMs: latencyBudget,
    latencyPass: latencyMs <= latencyBudget,
  };
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
  expect(hostProfileCatalog.profiles.length).toBeGreaterThanOrEqual(3);
  expect(codexIdeProfile).not.toBeNull();
  expect(codexCliProfile).not.toBeNull();
  expect(claudePartialProfile).not.toBeNull();
});

test("trial-1 static osm proxy map renders in browser", async ({ page }, testInfo) => {
  const startedAt = Date.now();
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
    accessibility: { altText: "Static OSM proxy map showing Westminster bbox." },
    ...latencyDetails(testInfo, "trial-1-static-osm", startedAt),
  });
});

test("trial-2 os_maps.render tool output produces renderable image", async (
  { request, page },
  testInfo
) => {
  const startedAt = Date.now();
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
    accessibility: { altText: "Rendered os_maps.render output image." },
    ...latencyDetails(testInfo, "trial-2-os-maps-render", startedAt),
  });
});

test("trial-3 geography selector map persists overlays after style switch", async (
  { page },
  testInfo
) => {
  const startedAt = Date.now();
  test.skip(
    testInfo.project.name !== "chromium-desktop",
    "Widget host emulation with style/local-layer assertions is validated on desktop Chromium."
  );
  await installDeterministicHostBridge(page, {
    profile: codexIdeProfile,
    seed: 17,
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
  await expect(page.locator("#mapStyleSelect")).toHaveValue("osm");

  const screenshot = await captureEvidence(page, testInfo, "trial-3-geography-selector");
  const mapPanel = await captureMapPanel(page, testInfo, "trial-3-geography-selector");
  writeObservation(testInfo, "trial-3-geography-selector", {
    screenshot,
    mapPanel,
    style: "osm",
    switchAfterOverlay: true,
    page: "ui/geography_selector.html",
    hostProfile: codexIdeProfile?.id || "unknown",
    accessibility: { altText: "Geography selector map with address overlays." },
    ...latencyDetails(testInfo, "trial-3-geography-selector", startedAt),
  });
});

test("trial-4 boundary explorer imports local layers and highlights matches", async (
  { page },
  testInfo
) => {
  const startedAt = Date.now();
  test.skip(
    testInfo.project.name !== "chromium-desktop",
    "Widget host emulation with local-layer highlight assertions is validated on desktop Chromium."
  );
  await installDeterministicHostBridge(page, {
    profile: codexIdeProfile,
    seed: 19,
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

  const fileUrl = pathToFileURL(path.resolve(repoRoot, "ui/boundary_explorer.html")).href;
  await page.goto(fileUrl);

  await expect(page.locator("#hostStatus")).toContainText("Host connected");
  await page.evaluate(() => {
    window.shp = async function () {
      return {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: { source: "zip-layer" },
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
      };
    };
  });
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
    hostProfile: codexIdeProfile?.id || "unknown",
    accessibility: { altText: "Boundary explorer map with local-layer highlights." },
    ...latencyDetails(testInfo, "trial-4-boundary-explorer", startedAt),
  });
});

test("trial-5 deterministic host-simulation fixtures are stable across engines", async (
  { page },
  testInfo
) => {
  const startedAt = Date.now();
  const selectedProfile = (() => {
    if (testInfo.project.name === "chromium-desktop") {
      return codexIdeProfile;
    }
    if (testInfo.project.name === "chromium-mobile") {
      return codexCliProfile;
    }
    return claudePartialProfile;
  })();
  await installDeterministicHostBridge(page, {
    profile: selectedProfile,
    seed: 23,
  });
  // Ensure addInitScript has a fresh document to attach to across engines.
  await page.goto("about:blank");
  await page.setContent("<main><h1>Host simulation replay</h1></main>");
  const initResult = await roundTripUiInitialize(page);
  expect(initResult).toBeTruthy();
  expect(initResult.protocolVersion).toBe("2026-01-26");
  expect(initResult.hostContext?.platform).toBe(
    selectedProfile?.hostContext?.platform || "web"
  );
  expect(initResult.hostContext?.mcpGeo?.proxyBase).toBe("http://localhost:8000");
  const screenshot = await captureEvidence(page, testInfo, "trial-5-host-simulation");
  writeObservation(testInfo, "trial-5-host-simulation", {
    screenshot,
    hostProfile: selectedProfile?.id || "unknown",
    degradationMode: selectedProfile?.degradationMode || "unknown",
    fixtureVersion: hostProfileCatalog.version,
    accessibility: { altText: "Host simulation replay probe screen." },
    ...latencyDetails(testInfo, "trial-5-host-simulation", startedAt),
  });
});
