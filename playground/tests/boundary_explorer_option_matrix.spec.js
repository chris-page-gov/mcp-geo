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
      if (!element) return false;
      element.value = String(nextValue);
      element.dispatchEvent(new Event("input", { bubbles: true }));
      return true;
    },
    { target: selector, nextValue: value }
  );
}

async function setCheckbox(page, selector, checked) {
  const current = await page.isChecked(selector);
  if (current === checked) {
    return;
  }
  if (checked) {
    await page.check(selector);
  } else {
    await page.uncheck(selector);
  }
}

test("boundary explorer option matrix renders all controls and captures visual states", async ({
  page,
}, testInfo) => {
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
      const args = message.params?.arguments || {};

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
        const requested = Array.isArray(args.layers) ? args.layers : [];
        respond(window.__buildInventoryPayload(requested));
        return;
      }

      if (name === "os_map_export") {
        respond({ uri: "resource://mcp-geo/os-exports/matrix.json" });
        return;
      }

      respond({});
    });

    window.__buildInventoryPayload = (requestedLayers) => {
      const requested = Array.isArray(requestedLayers) ? requestedLayers : [];
      const cloneLayer = (value) => JSON.parse(JSON.stringify(value));
      const baseline = {
        uprns: {
          count: 3,
          results: [
            { uprn: "1000000101", lat: 52.41482, lon: -1.53731, address: "1 Test Road, Coventry CV1 1AA" },
            { uprn: "1000000102", lat: 52.4147, lon: -1.53688, address: "2 Test Road, Coventry CV1 1AA" },
            { uprn: "1000000103", lat: 52.41456, lon: -1.53705, address: "3 Test Road, Coventry CV1 1AA" },
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
                coordinates: [[[-1.53745, 52.4147], [-1.53715, 52.4147], [-1.53715, 52.41495], [-1.53745, 52.41495], [-1.53745, 52.4147]]],
              },
            },
            {
              id: "building-2",
              type: "Feature",
              properties: {},
              geometry: {
                type: "Polygon",
                coordinates: [[[-1.53704, 52.41453], [-1.53676, 52.41453], [-1.53676, 52.41475], [-1.53704, 52.41475], [-1.53704, 52.41453]]],
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
              geometry: { type: "LineString", coordinates: [[-1.5379, 52.4146], [-1.5364, 52.4149]] },
            },
          ],
        },
        path_links: {
          features: [
            {
              id: "path-1",
              type: "Feature",
              properties: {},
              geometry: { type: "LineString", coordinates: [[-1.53772, 52.41497], [-1.53686, 52.41518]] },
            },
          ],
        },
      };
      const payload = { bbox: [-1.538, 52.414, -1.536, 52.416], layers: {} };
      if (requested.includes("uprns")) payload.layers.uprns = cloneLayer(baseline.uprns);
      if (requested.includes("buildings")) payload.layers.buildings = cloneLayer(baseline.buildings);
      if (requested.includes("road_links")) payload.layers.road_links = cloneLayer(baseline.road_links);
      if (requested.includes("path_links")) payload.layers.path_links = cloneLayer(baseline.path_links);
      return payload;
    };
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
  await page.fill("#searchInput", "Sherbourne");
  await page.click("#searchButton");
  await page.waitForSelector(".result");
  await page.click(".result [data-action='toggle']");
  await page.waitForFunction(() => {
    const probe = window.__MCP_GEO_BOUNDARY_EXPLORER__;
    return !!probe && probe.getSnapshot?.()?.selection?.selectedCount === 1;
  });

  await setCheckbox(page, "#layerUprns", true);
  await setCheckbox(page, "#layerUprnDots", true);
  await setCheckbox(page, "#layerBuildings", true);
  await setCheckbox(page, "#layerRoads", true);
  await setCheckbox(page, "#layerPaths", true);
  await page.click("#refreshInventory");
  await page.waitForFunction(() => {
    const snapshot = window.__MCP_GEO_BOUNDARY_EXPLORER__?.getSnapshot?.();
    return snapshot?.sourceCounts?.uprns === 3;
  });

  const scenarios = [
    {
      id: "01_default_auto_outline",
      preset: "auto",
      detailLevel: "postcode",
      borderByCount: true,
      toggles: {
        layerBoundaryFill: false,
        layerUprns: true,
        layerUprnDots: false,
        layerBuildings: true,
        layerRoads: true,
        layerPaths: true,
      },
      sliders: {
        basemapOpacity: 0.12,
        boundaryFillOpacity: 0.0,
        uprnDensityOpacity: 0.52,
        buildingOpacity: 0.22,
        linkOpacity: 0.85,
      },
    },
    {
      id: "02_detail_dense_points",
      preset: "detail",
      detailLevel: "uprn",
      borderByCount: true,
      toggles: {
        layerBoundaryFill: false,
        layerUprns: true,
        layerUprnDots: true,
        layerBuildings: true,
        layerRoads: true,
        layerPaths: true,
      },
      sliders: {
        basemapOpacity: 0.08,
        boundaryFillOpacity: 0.0,
        uprnDensityOpacity: 0.64,
        buildingOpacity: 0.26,
        linkOpacity: 0.9,
      },
    },
    {
      id: "03_balanced_soft_fill",
      preset: "balanced",
      detailLevel: "postcode",
      borderByCount: true,
      toggles: {
        layerBoundaryFill: true,
        layerUprns: true,
        layerUprnDots: false,
        layerBuildings: true,
        layerRoads: true,
        layerPaths: true,
      },
      sliders: {
        basemapOpacity: 0.16,
        boundaryFillOpacity: 0.18,
        uprnDensityOpacity: 0.48,
        buildingOpacity: 0.24,
        linkOpacity: 0.78,
      },
    },
    {
      id: "04_links_first_outline",
      preset: "links",
      detailLevel: "postcode",
      borderByCount: false,
      toggles: {
        layerBoundaryFill: false,
        layerUprns: false,
        layerUprnDots: false,
        layerBuildings: false,
        layerRoads: true,
        layerPaths: true,
      },
      sliders: {
        basemapOpacity: 0.06,
        boundaryFillOpacity: 0.0,
        uprnDensityOpacity: 0.3,
        buildingOpacity: 0.12,
        linkOpacity: 0.96,
      },
    },
    {
      id: "05_uprn_dots_focus",
      preset: "detail",
      detailLevel: "uprn",
      borderByCount: true,
      toggles: {
        layerBoundaryFill: false,
        layerUprns: false,
        layerUprnDots: true,
        layerBuildings: false,
        layerRoads: false,
        layerPaths: false,
      },
      sliders: {
        basemapOpacity: 0.14,
        boundaryFillOpacity: 0.0,
        uprnDensityOpacity: 0.4,
        buildingOpacity: 0.1,
        linkOpacity: 0.4,
      },
    },
    {
      id: "06_building_mass_focus",
      preset: "balanced",
      detailLevel: "postcode",
      borderByCount: true,
      toggles: {
        layerBoundaryFill: true,
        layerUprns: false,
        layerUprnDots: false,
        layerBuildings: true,
        layerRoads: false,
        layerPaths: false,
      },
      sliders: {
        basemapOpacity: 0.2,
        boundaryFillOpacity: 0.12,
        uprnDensityOpacity: 0.28,
        buildingOpacity: 0.38,
        linkOpacity: 0.42,
      },
    },
    {
      id: "07_transport_highlight",
      preset: "links",
      detailLevel: "postcode",
      borderByCount: false,
      toggles: {
        layerBoundaryFill: true,
        layerUprns: false,
        layerUprnDots: false,
        layerBuildings: false,
        layerRoads: true,
        layerPaths: true,
      },
      sliders: {
        basemapOpacity: 0.1,
        boundaryFillOpacity: 0.1,
        uprnDensityOpacity: 0.2,
        buildingOpacity: 0.1,
        linkOpacity: 1.0,
      },
    },
    {
      id: "08_mixed_explainable",
      preset: "auto",
      detailLevel: "uprn",
      borderByCount: true,
      toggles: {
        layerBoundaryFill: false,
        layerUprns: true,
        layerUprnDots: true,
        layerBuildings: true,
        layerRoads: true,
        layerPaths: false,
      },
      sliders: {
        basemapOpacity: 0.11,
        boundaryFillOpacity: 0.0,
        uprnDensityOpacity: 0.58,
        buildingOpacity: 0.25,
        linkOpacity: 0.82,
      },
    },
  ];

  const results = [];
  for (const scenario of scenarios) {
    await test.step(`matrix: ${scenario.id}`, async () => {
      await page.selectOption("#hierarchyPreset", scenario.preset);
      await page.selectOption("#detailLevel", scenario.detailLevel);
      await setCheckbox(page, "#borderByCount", scenario.borderByCount);

      await setCheckbox(page, "#layerBoundaryFill", scenario.toggles.layerBoundaryFill);
      await setCheckbox(page, "#layerUprns", scenario.toggles.layerUprns);
      await setCheckbox(page, "#layerUprnDots", scenario.toggles.layerUprnDots);
      await setCheckbox(page, "#layerBuildings", scenario.toggles.layerBuildings);
      await setCheckbox(page, "#layerRoads", scenario.toggles.layerRoads);
      await setCheckbox(page, "#layerPaths", scenario.toggles.layerPaths);

      await setRangeValue(page, "#basemapOpacity", scenario.sliders.basemapOpacity);
      await setRangeValue(page, "#boundaryFillOpacity", scenario.sliders.boundaryFillOpacity);
      await setRangeValue(page, "#uprnDensityOpacity", scenario.sliders.uprnDensityOpacity);
      await setRangeValue(page, "#buildingOpacity", scenario.sliders.buildingOpacity);
      await setRangeValue(page, "#linkOpacity", scenario.sliders.linkOpacity);

      await page.click("#refreshInventory");
      await page.waitForTimeout(140);

      const snapshot = await page.evaluate(() => window.__MCP_GEO_BOUNDARY_EXPLORER__.getSnapshot());
      expect(snapshot.selection.selectedCount).toBe(1);
      expect(snapshot.layers.areaFill).toBe(scenario.toggles.layerBoundaryFill);
      expect(snapshot.layers.uprnDensity).toBe(scenario.toggles.layerUprns);
      expect(snapshot.layers.uprnDots).toBe(scenario.toggles.layerUprnDots);
      expect(snapshot.layers.buildings).toBe(scenario.toggles.layerBuildings);
      expect(snapshot.layers.roads).toBe(scenario.toggles.layerRoads);
      expect(snapshot.layers.paths).toBe(scenario.toggles.layerPaths);
      expect(snapshot.styleControls.basemapOpacity).toBeCloseTo(scenario.sliders.basemapOpacity, 2);
      expect(snapshot.styleControls.boundaryFillOpacity).toBeCloseTo(
        scenario.sliders.boundaryFillOpacity,
        2
      );
      expect(snapshot.styleControls.uprnDensityOpacity).toBeCloseTo(
        scenario.sliders.uprnDensityOpacity,
        2
      );
      expect(snapshot.styleControls.buildingOpacity).toBeCloseTo(
        scenario.sliders.buildingOpacity,
        2
      );
      expect(snapshot.styleControls.linkOpacity).toBeCloseTo(scenario.sliders.linkOpacity, 2);

      const screenshotName = `${scenario.id}.png`;
      const screenshotPath = testInfo.outputPath(screenshotName);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      await testInfo.attach(`matrix-${scenario.id}`, {
        path: screenshotPath,
        contentType: "image/png",
      });

      results.push({
        id: scenario.id,
        preset: scenario.preset,
        detailLevel: scenario.detailLevel,
        toggles: snapshot.layers,
        styleControls: snapshot.styleControls,
        sourceCounts: snapshot.sourceCounts,
        screenshot: screenshotName,
      });
    });
  }

  const summaryPath = testInfo.outputPath("matrix-summary.json");
  fs.writeFileSync(
    summaryPath,
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        scenarioCount: scenarios.length,
        scenarios: results,
      },
      null,
      2
    ),
    "utf-8"
  );
  await testInfo.attach("matrix-summary", {
    path: summaryPath,
    contentType: "application/json",
  });
  expect(results).toHaveLength(scenarios.length);
});
