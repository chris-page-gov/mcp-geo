import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

import { uiFileUrl } from "./support/ui_paths.js";
import { HOST_PROFILES } from "./support/host_profiles.js";
import { installMcpBridge } from "./support/mcp_bridge.js";
import {
  assertCompactGlobalContract,
  assertKeyboardReachesTarget,
  assertNoPageErrors,
  expectToolsCalled,
  getSelectOptionValues,
  readJsonText,
  sendHostContextChanged,
  setRangeValue,
  trackPageErrors,
  waitForCompactWidthAtMost,
} from "./support/compact_assertions.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "../../..");

const WORKER_BODY = fs.readFileSync(
  path.resolve(repoRoot, "ui/vendor/maplibre-gl-csp-worker.js"),
  "utf-8"
);

const EMPTY_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=",
  "base64"
);

const PROXY_STYLE = {
  version: 8,
  sources: {
    os_vts: {
      type: "vector",
      tiles: ["http://localhost/maps/vector/vts/tile/{z}/{x}/{y}.pbf"],
    },
  },
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#edf2f4" },
    },
  ],
};

const MAPLIBRE_STUB = `
(() => {
  class FakeMap {
    constructor(options) {
      this.options = options;
      this.handlers = new Map();
      this.onceHandlers = new Map();
      this.center = { lng: options.center?.[0] ?? 0, lat: options.center?.[1] ?? 0 };
      this.zoom = options.zoom ?? 10;
      setTimeout(() => this.emit("load"), 0);
    }

    on(name, handler) {
      if (!this.handlers.has(name)) this.handlers.set(name, []);
      this.handlers.get(name).push(handler);
    }

    once(name, handler) {
      if (!this.onceHandlers.has(name)) this.onceHandlers.set(name, []);
      this.onceHandlers.get(name).push(handler);
    }

    emit(name, payload) {
      (this.handlers.get(name) || []).forEach((handler) => handler(payload));
      const onceList = this.onceHandlers.get(name) || [];
      this.onceHandlers.delete(name);
      onceList.forEach((handler) => handler(payload));
    }

    addControl() {}

    setStyle(style) {
      this.style = style;
      this.emit("styledata", { style });
      this.emit("sourcedata", { sourceId: "base", isSourceLoaded: true });
      setTimeout(() => this.emit("idle"), 0);
    }

    getCenter() {
      return this.center;
    }

    getZoom() {
      return this.zoom;
    }

    easeTo(opts) {
      this.center = {
        lng: opts.center?.[0] ?? this.center.lng,
        lat: opts.center?.[1] ?? this.center.lat,
      };
      this.zoom = opts.zoom ?? this.zoom;
      setTimeout(() => {
        this.emit("moveend", {});
        this.emit("idle", {});
      }, 0);
    }

    loaded() {
      return true;
    }

    isStyleLoaded() {
      return true;
    }

    areTilesLoaded() {
      return true;
    }

    isMoving() {
      return false;
    }

    isZooming() {
      return false;
    }

    isRotating() {
      return false;
    }

    remove() {}
  }

  window.maplibregl = {
    workerUrl: "",
    addProtocol() {},
    NavigationControl: class {},
    Map: FakeMap,
  };
})();
`;

const PMTILES_STUB = `
(() => {
  window.pmtiles = {
    Protocol: class {
      constructor() {
        this.tile = () => {};
      }
      add() {}
    },
    PMTiles: class {
      constructor(url) {
        this.url = url;
      }
      async getMetadata() {
        return { vector_layers: [{ id: "demo" }] };
      }
    },
  };
})();
`;

async function routeCommonMapAssets(page) {
  await page.route("**/maps/worker/maplibre-gl-csp-worker.js", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/javascript",
      body: WORKER_BODY,
    });
  });

  await page.route("**/maps/raster/osm/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "image/png",
      body: EMPTY_PNG,
    });
  });

  await page.route("**/maps/vector/vts/resources/styles**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(PROXY_STYLE),
    });
  });

  await page.route("**/maps/vector/vts/tile/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/x-protobuf",
      body: "",
    });
  });
}

async function routeShapefileStub(page) {
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
}

function boundaryInventoryResult() {
  return {
    bbox: [-0.122, 51.504, -0.118, 51.507],
    layers: {
      uprns: {
        count: 3,
        results: [
          {
            uprn: "1000000001",
            lat: 51.505,
            lon: -0.1201,
            address: "1 TEST STREET SW1A1AA",
            classification_code: "RD01",
            classification_description: "Residential",
            logical_status: "1",
          },
          {
            uprn: "1000000002",
            lat: 51.5052,
            lon: -0.1199,
            address: "2 TEST STREET SW1A1AA",
            classification_code: "RD01",
            classification_description: "Residential",
            logical_status: "1",
          },
          {
            uprn: "1000000003",
            lat: 51.5053,
            lon: -0.1197,
            address: "3 TRADE LANE SW1A1AB",
            classification_code: "CM02",
            classification_description: "Commercial",
            logical_status: "2",
          },
        ],
      },
      buildings: {
        features: [
          {
            id: "b1",
            geometry: {
              type: "Polygon",
              coordinates: [[[-0.1208, 51.5048], [-0.1198, 51.5048], [-0.1198, 51.5054], [-0.1208, 51.5054], [-0.1208, 51.5048]]],
            },
            properties: { use: "mixed" },
          },
        ],
      },
      road_links: {
        features: [
          {
            id: "r1",
            geometry: {
              type: "LineString",
              coordinates: [[-0.1211, 51.505], [-0.1192, 51.505]],
            },
            properties: { usrn: "200000001" },
          },
        ],
      },
      path_links: {
        features: [
          {
            id: "p1",
            geometry: {
              type: "LineString",
              coordinates: [[-0.1208, 51.5049], [-0.1194, 51.5057]],
            },
            properties: {},
          },
        ],
      },
    },
  };
}

function geographyToolRules() {
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
      lat: 51.5008,
      lon: -0.119,
      classificationDescription: "Residential",
    },
  ];

  return [
    {
      name: "os_places.search",
      aliases: ["os_places_search"],
      result: {
        results: addressResults,
      },
    },
    {
      name: "os_places.by_postcode",
      aliases: ["os_places_by_postcode"],
      result: {
        uprns: addressResults,
      },
    },
    {
      name: "os_places.by_uprn",
      aliases: ["os_places_by_uprn"],
      result: {
        result: addressResults[0],
      },
    },
    {
      name: "admin_lookup.find_by_name",
      result: {
        results: [
          {
            id: "E05000001",
            name: "Test Ward",
            level: "WARD",
            bbox: [-0.123, 51.499, -0.118, 51.503],
          },
        ],
      },
    },
    {
      name: "admin_lookup.containing_areas",
      result: {
        results: [{ id: "E05000001", name: "Test Ward", level: "WARD" }],
        meta: { source: "cache" },
      },
    },
    {
      name: "admin_lookup.area_geometry",
      result: {
        id: "E05000001",
        name: "Test Ward",
        level: "WARD",
        bbox: [-0.123, 51.499, -0.118, 51.503],
        geometry: {
          type: "Feature",
          properties: {},
          geometry: {
            type: "Polygon",
            coordinates: [[[-0.123, 51.499], [-0.118, 51.499], [-0.118, 51.503], [-0.123, 51.503], [-0.123, 51.499]]],
          },
        },
      },
    },
    {
      name: "admin_lookup.get_cache_status",
      result: {
        status: "ok",
        counts: { total: 240000 },
      },
    },
    {
      name: "admin_lookup.search_cache",
      result: {
        results: [{ id: "E05000001", name: "Test Ward", level: "WARD" }],
      },
    },
  ];
}

test.describe("compact acceptance smoke (CW-7)", () => {
  test("boundary explorer satisfies compact strict acceptance contract", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.setViewportSize({ width: 360, height: 500 });

    await installMcpBridge(page, {
      hostContext: HOST_PROFILES.claude_inline_500,
      toolRules: [
        {
          name: "admin_lookup.find_by_name",
          when: { text: "NO_MATCH" },
          result: { results: [] },
        },
        {
          name: "admin_lookup.find_by_name",
          result: {
            results: [
              {
                id: "E05000001",
                name: "Test Ward",
                level: "WARD",
                bbox: [-0.122, 51.504, -0.118, 51.507],
              },
            ],
          },
        },
        {
          name: "admin_lookup.area_geometry",
          result: {
            id: "E05000001",
            name: "Test Ward",
            level: "WARD",
            bbox: [-0.122, 51.504, -0.118, 51.507],
            geometry: {
              type: "Feature",
              properties: {},
              geometry: {
                type: "Polygon",
                coordinates: [[[-0.122, 51.504], [-0.118, 51.504], [-0.118, 51.507], [-0.122, 51.507], [-0.122, 51.504]]],
              },
            },
          },
        },
        {
          name: "os_map.inventory",
          aliases: ["os_map_inventory"],
          result: boundaryInventoryResult(),
        },
        {
          name: "os_map.export",
          aliases: ["os_map_export"],
          result: { status: "prepared", exportId: "exp-001" },
        },
      ],
      strictToolMatching: true,
    });

    await routeCommonMapAssets(page);
    await routeShapefileStub(page);

    await page.goto(uiFileUrl("boundary_explorer.html"), { waitUntil: "domcontentloaded" });

    await expect(page.locator("#hostStatus")).toContainText("Host connected");
    await assertCompactGlobalContract(page, {
      ctaSelector: "#searchButton",
      statusSelector: "#hostStatus",
    });
    await assertKeyboardReachesTarget(page, "#searchButton");

    await sendHostContextChanged(page, {
      containerDimensions: { maxWidth: 320, maxHeight: 500 },
    });
    await waitForCompactWidthAtMost(page, 320);

    await page.fill("#searchInput", "Westminster");
    await page.press("#searchInput", "Enter");
    await expect(page.locator("#results [data-action='toggle']").first()).toBeVisible();

    await page.locator("#results [data-action='toggle']").first().evaluate((node) => {
      node.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
    });
    await expect(page.locator("#selectedCount")).toHaveText("1");
    await page.click("#boundaryInventory button[data-action='remove']");
    await expect(page.locator("#selectedCount")).toHaveText("0");

    await page.locator("#results [data-action='toggle']").first().evaluate((node) => {
      node.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
    });
    await expect(page.locator("#selectedCount")).toHaveText("1");

    await page.locator("#refreshInventory").click({ force: true });
    await expect(page.locator("#hostStatus")).toContainText("Host connected");

    await page.fill("#uprnAddressFilter", "TEST STREET");
    await page.selectOption("#uprnClassificationFilter", "RD01");
    await page.check("#uprnFlagRequireAddress");
    await page.check("#uprnFlagActive");
    await page.check("#uprnFlagResidential");
    await expect(page.locator("#infoBanner")).toContainText("UPRN filters");

    await page.selectOption("#detailLevel", "postcode");
    await expect(page.locator("#infoBanner")).toContainText("POSTCODE total");
    await page.selectOption("#detailLevel", "uprn");
    await expect(page.locator("#infoBanner")).toContainText("UPRN total");

    for (const selector of [
      "#layerUprns",
      "#layerUprnDots",
      "#layerBuildings",
      "#layerRoads",
      "#layerPaths",
    ]) {
      await page.uncheck(selector);
      await expect(page.locator(selector)).not.toBeChecked();
      await page.check(selector);
      await expect(page.locator(selector)).toBeChecked();
    }

    const beforeStyleSwap = Number(await page.locator("#highlightCount").textContent());
    const styleValues = await getSelectOptionValues(page, "#basemapStyle");
    for (const styleValue of styleValues) {
      await page.selectOption("#basemapStyle", styleValue);
      await expect(page.locator("#basemapStyle")).toHaveValue(styleValue);
    }
    await expect(page.locator("#highlightCount")).toHaveText(String(beforeStyleSwap));

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

    const csvPayload = [
      "lat,lon,name",
      "51.5050,-0.1200,CSV One",
      "51.5051,-0.1198,CSV Two",
    ].join("\n");

    await page.setInputFiles("#fileInput", {
      name: "selection.geojson",
      mimeType: "application/geo+json",
      buffer: Buffer.from(polygonGeoJson, "utf-8"),
    });
    await expect(page.locator("#importStatus")).toContainText("Imported selection.geojson");

    await page.setInputFiles("#fileInput", {
      name: "selection.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(csvPayload, "utf-8"),
    });
    await expect(page.locator("#importStatus")).toContainText("Imported selection.csv");

    await page.setInputFiles("#fileInput", {
      name: "selection.zip",
      mimeType: "application/zip",
      buffer: Buffer.from("PK-test", "utf-8"),
    });
    await expect(page.locator("#importStatus")).toContainText("Imported selection.zip");

    await page.setInputFiles("#fileInput", {
      name: "selection.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("unsupported", "utf-8"),
    });
    await expect(page.locator("#importStatus")).toContainText("Import failed for selection.txt");

    await page.evaluate(() => {
      window.applyLocalLayerSelection({
        type: "Feature",
        properties: { source: "selection-test" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-0.121, 51.5045], [-0.119, 51.5045], [-0.119, 51.5062], [-0.121, 51.5062], [-0.121, 51.5045]]],
        },
      });
    });

    await expect(page.locator("#infoBanner")).toContainText("Selected by local layer");
    await expect(page.locator("#highlightCount")).toHaveText("2");

    await expect(page.locator("#fullscreenToggle")).toHaveText("Maximise");
    await page.click("#fullscreenToggle");
    await expect(page.locator("#fullscreenToggle")).toHaveText("Exit maximise");
    await page.click("#fullscreenToggle");
    await expect(page.locator("#fullscreenToggle")).toHaveText("Maximise");

    await sendHostContextChanged(page, {
      availableDisplayModes: ["inline"],
      displayMode: "inline",
    });
    await expect(page.locator("#fullscreenToggle")).toContainText("Try maximise");
    await page.click("#fullscreenToggle");
    await expect(page.locator("#hostStatus")).toBeVisible();

    await expectToolsCalled(page, [
      "admin_lookup.find_by_name",
      "os_map.inventory",
    ]);
    await assertNoPageErrors(pageErrors, "boundary_explorer");
  });

  test("geography selector satisfies compact strict acceptance contract", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.setViewportSize({ width: 360, height: 500 });

    await installMcpBridge(page, {
      hostContext: HOST_PROFILES.claude_inline_500,
      toolRules: geographyToolRules(),
      strictToolMatching: true,
    });

    await routeCommonMapAssets(page);

    await page.goto(uiFileUrl("geography_selector.html"), { waitUntil: "domcontentloaded" });

    await expect(page.locator("#status")).toContainText("Host connected");
    await assertCompactGlobalContract(page, {
      ctaSelector: "#searchButton",
      statusSelector: "#status",
    });
    await expect(page.locator("#compactTabs")).toBeVisible();
    await expect(page.locator("#compactTabs button.active")).toHaveText("Map");
    await expect(page.locator("#zoomLadderPanel")).toBeHidden();
    await page.click("#zoomLadderToggle");
    await expect(page.locator("#zoomLadderPanel")).toBeVisible();
    await page.locator("#zoomLadder .zoom-step").first().click();
    await expect(page.locator("#zoomLadderPanel")).toBeHidden();

    await page.click("#compactTabs button[data-tab='search']");
    await assertKeyboardReachesTarget(page, "#searchButton");

    await sendHostContextChanged(page, {
      containerDimensions: { maxWidth: 320, maxHeight: 500 },
    });
    await waitForCompactWidthAtMost(page, 320);

    await page.click("#searchButton");
    await expect(page.locator("#flowStatus")).toContainText("Enter a search term");

    await page.fill("#queryInput", "Test Street");
    await page.click("#searchButton");
    await expect(page.locator("#flowStatus")).toContainText("Found");
    await page.click("#compactTabs button[data-tab='results']");
    await page.locator("#results .result-card").first().click();
    await page.click("#compactTabs button[data-tab='info']");
    await expect(page.locator("#selectionSummary")).toContainText("Selected UPRNs");

    await page.click("#compactTabs button[data-tab='search']");
    await page.getByRole("button", { name: "Postcode" }).click();
    await page.fill("#queryInput", "SW1A1AA");
    await page.click("#searchButton");
    await expect(page.locator("#flowStatus")).toContainText("Found");

    await page.getByRole("button", { name: "UPRN" }).click();
    await page.fill("#queryInput", "1000000001");
    await page.click("#searchButton");
    await expect(page.locator("#flowStatus")).toContainText("Found");

    await page.getByRole("button", { name: "Area name" }).click();
    await page.selectOption("#levelSelect", "ward");
    await page.fill("#queryInput", "Test Ward");
    await page.click("#searchButton");
    await expect(page.locator("#flowStatus")).toContainText("Found");
    await page.click("#compactTabs button[data-tab='results']");
    await page.locator("#results .result-card").first().click();
    await page.click("#compactTabs button[data-tab='info']");
    await expect(page.locator("#selectionSummary")).toContainText("Selected areas (1)");
    await page.click("#clearSelection");
    await expect(page.locator("#selectionSummary")).toContainText("No selection yet");

    await page.click("#compactTabs button[data-tab='search']");
    await page.getByRole("button", { name: "Free text" }).click();
    await page.fill("#queryInput", "Test Street");
    await page.click("#searchButton");
    await expect(page.locator("#flowStatus")).toContainText("Found");

    await page.click("#compactTabs button[data-tab='debug']");
    await setRangeValue(page, "#mapOpacity", 0.15);
    await expect.poll(async () => (await readJsonText(page, "#diagnostics")).opacity).toBe(0.15);
    await setRangeValue(page, "#mapOpacity", 0.55);
    await expect.poll(async () => (await readJsonText(page, "#diagnostics")).opacity).toBe(0.55);
    await setRangeValue(page, "#mapOpacity", 1);
    await expect.poll(async () => (await readJsonText(page, "#diagnostics")).opacity).toBe(1);

    for (const layerId of ["boundaries", "addresses"]) {
      const selector = `[data-testid='layer-toggle-input-${layerId}']`;
      await page.uncheck(selector);
      await expect.poll(async () => (await readJsonText(page, "#diagnostics")).layerVisibility[layerId]).toBe(false);
      await page.check(selector);
      await expect.poll(async () => (await readJsonText(page, "#diagnostics")).layerVisibility[layerId]).toBe(true);
    }

    const beforeStyleSwap = await readJsonText(page, "#diagnostics");
    const beforeAddressCount = Number(beforeStyleSwap?.data?.addressPoints || 0);

    const styleValues = await getSelectOptionValues(page, "#mapStyleSelect");
    for (const styleValue of styleValues) {
      await page.selectOption("#mapStyleSelect", styleValue);
      await expect
        .poll(async () => (await readJsonText(page, "#diagnostics")).style)
        .toBe(styleValue);
    }

    await expect
      .poll(async () => Number((await readJsonText(page, "#diagnostics"))?.data?.addressPoints || 0))
      .toBeGreaterThanOrEqual(beforeAddressCount);

    await expect(page.locator("#fullscreenToggle")).toHaveText("Maximise");
    await page.click("#fullscreenToggle");
    await expect(page.locator("#fullscreenToggle")).toHaveText("Exit maximise");
    await page.click("#fullscreenToggle");

    await sendHostContextChanged(page, {
      availableDisplayModes: ["inline"],
      displayMode: "inline",
    });
    await expect(page.locator("#fullscreenToggle")).toContainText("Try maximise");

    await expectToolsCalled(page, ["os_places.search", "admin_lookup.find_by_name"]);
    await assertNoPageErrors(pageErrors, "geography_selector");
  });

  test("statistics dashboard satisfies compact strict acceptance contract", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.setViewportSize({ width: 360, height: 500 });

    await installMcpBridge(page, {
      hostContext: HOST_PROFILES.claude_inline_500,
      toolRules: [
        {
          name: "ons_search.query",
          result: {
            results: [
              {
                id: "ds_test",
                title: "Test Dataset",
                description: "Compact dashboard test dataset",
                state: "published",
              },
            ],
            total: 1,
          },
        },
        {
          name: "ons_data.editions",
          result: { editions: [{ id: "2026" }] },
        },
        {
          name: "ons_data.versions",
          result: { versions: [{ id: "1" }] },
        },
        {
          name: "ons_codes.list",
          result: { dimensions: ["geography", "measure", "time"] },
        },
        {
          name: "ons_codes.options",
          when: { dimension: "geography" },
          result: { options: ["E09000001", "E09000033"] },
        },
        {
          name: "ons_codes.options",
          when: { dimension: "measure" },
          result: { options: ["value"] },
        },
        {
          name: "ons_codes.options",
          when: { dimension: "time" },
          result: { options: ["2025", "2026"] },
        },
        {
          name: "ons_data.query",
          when: { geography: "E09000001" },
          result: { results: [{ observation: 12.5 }] },
        },
        {
          name: "ons_data.query",
          when: { geography: "E09000033" },
          result: { results: [{ observation: 18.75 }] },
        },
      ],
      strictToolMatching: true,
    });

    await page.goto(uiFileUrl("statistics_dashboard.html"), { waitUntil: "domcontentloaded" });

    await expect(page.locator("#status")).toContainText("Host connected");
    await assertCompactGlobalContract(page, {
      ctaSelector: "#datasetSearchButton",
      statusSelector: "#status",
    });
    await assertKeyboardReachesTarget(page, "#datasetSearchButton");

    await page.click("#datasetSearchButton");
    await expect(page.locator("#flowStatus")).toContainText("Enter a dataset search term");

    await page.fill("#datasetSearch", "housing");
    await page.click("#datasetSearchButton");
    await expect(page.locator("#flowStatus")).toContainText("Found 1 dataset result");

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

    await page.selectOption("#timeSelect", "");
    await page.click("#runQuery");
    await expect(page.locator("#flowStatus")).toContainText("Complete all required fields");
    await expect(page.locator("#queryError")).toContainText("Pick dataset/edition/version");

    await sendHostContextChanged(page, {
      containerDimensions: { maxWidth: 320, maxHeight: 500 },
    });
    await waitForCompactWidthAtMost(page, 320);

    await expect(page.locator("#fullscreenToggle")).toHaveText("Maximise");
    await page.click("#fullscreenToggle");
    await expect(page.locator("#fullscreenToggle")).toHaveText("Exit maximise");
    await page.click("#fullscreenToggle");
    await sendHostContextChanged(page, {
      availableDisplayModes: ["inline"],
      displayMode: "inline",
    });
    await expect(page.locator("#fullscreenToggle")).toContainText("Try maximise");

    await expectToolsCalled(page, ["ons_search.query", "ons_data.query", "ons_codes.options"]);
    await assertNoPageErrors(pageErrors, "statistics_dashboard");
  });

  test("simple map lab satisfies compact strict acceptance contract", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.setViewportSize({ width: 360, height: 500 });

    await page.route("**/maplibre-gl@5.7.1/dist/maplibre-gl.css", async (route) => {
      await route.fulfill({ status: 200, contentType: "text/css", body: "" });
    });

    await page.route("**/maplibre-gl@5.7.1/dist/maplibre-gl.js", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/javascript", body: MAPLIBRE_STUB });
    });

    await page.route("**/pmtiles@3.2.1/dist/pmtiles.js", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/javascript", body: PMTILES_STUB });
    });

    await page.route("**/maps/vector/vts/resources/styles**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(PROXY_STYLE),
      });
    });

    await page.route("**/maps/vector/vts/tile/**", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/x-protobuf", body: "" });
    });

    await page.goto(uiFileUrl("simple_map.html"), { waitUntil: "domcontentloaded" });

    await assertCompactGlobalContract(page, {
      ctaSelector: "#loadBtn",
      statusSelector: "#status",
    });
    await assertKeyboardReachesTarget(page, "#loadBtn");

    await expect(page.locator("#token")).toHaveAttribute("type", "password");
    await expect(page.locator("#apiKey")).toHaveAttribute("type", "password");

    await page.fill("#proxyBase", "http://localhost:8000");

    await page.selectOption("#mode", "pmtiles");
    await page.fill("#pmtilesUrl", "");
    await page.click("#loadBtn");
    await expect(page.locator("#status")).toContainText("PMTiles URL is required");

    await page.fill("#pmtilesUrl", "https://example.com/demo.pmtiles");
    await page.click("#loadBtn");
    await expect(page.locator("#status")).toContainText("PMTiles");

    await page.selectOption("#mode", "os_vector");

    await page.fill("#token", '{"access_token":"token-abc"}');
    await page.fill("#apiKey", "");
    await page.click("#loadBtn");
    await expect(page.locator("#status")).toContainText("browser token");
    await expect(page.locator("#authMode")).toContainText("Browser bearer token");

    await page.fill("#token", "");
    await page.fill("#apiKey", "api-key-123");
    await page.click("#loadBtn");
    await expect(page.locator("#status")).toContainText("API key");
    await expect(page.locator("#authMode")).toContainText("API key override");

    await page.fill("#apiKey", "");
    await page.click("#loadBtn");
    await expect(page.locator("#status")).toContainText("server's saved OS key");
    await expect(page.locator("#authMode")).toContainText("Server environment key");

    const styleValues = await getSelectOptionValues(page, "#osStyle");
    await page.fill("#apiKey", "api-key-123");
    for (const styleValue of styleValues) {
      await page.selectOption("#osStyle", styleValue);
      await page.click("#loadBtn");
      const timings = await readJsonText(page, "#timings");
      expect(timings.selectedStyle).toBe(styleValue);
      expect(timings.authMode).toBe("api_key");
    }

    await sendHostContextChanged(page, {
      containerDimensions: { maxWidth: 320, maxHeight: 500 },
    });
    await waitForCompactWidthAtMost(page, 320);

    await assertNoPageErrors(pageErrors, "simple_map");
  });

  test("feature inspector satisfies compact strict acceptance contract", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.setViewportSize({ width: 360, height: 500 });

    await installMcpBridge(page, {
      hostContext: HOST_PROFILES.claude_inline_500,
      toolRules: [
        {
          name: "os_linked_ids.get",
          aliases: ["os_linked_ids_get"],
          result: { toid: "osgb123", uprn: "1000000099", usrn: "200000001" },
        },
      ],
      strictToolMatching: true,
    });

    await page.goto(uiFileUrl("feature_inspector.html"), { waitUntil: "domcontentloaded" });

    await expect(page.locator("#statusBadge")).toContainText("Host connected");
    await assertCompactGlobalContract(page, {
      ctaSelector: "#loadFeature",
      statusSelector: "#statusBadge",
    });
    await assertKeyboardReachesTarget(page, "#loadFeature");

    await page.fill("#identifierInput", "");
    await page.click("#loadFeature");
    await expect(page.locator("#statusBadge")).toContainText("Enter an identifier");

    await page.fill("#identifierInput", "1000000099");
    await page.selectOption("#identifierType", "uprn");
    await page.click("#loadFeature");
    await expect(page.locator("#statusBadge")).toContainText("Feature loaded");
    await expect(page.locator("#toidChip")).toContainText("osgb123");
    await expect(page.locator("#uprnChip")).toContainText("1000000099");

    await expect(page.locator("#fullscreenToggle")).toHaveText("Maximise");
    await page.click("#fullscreenToggle");
    await expect(page.locator("#fullscreenToggle")).toHaveText("Exit maximise");
    await page.click("#fullscreenToggle");

    await sendHostContextChanged(page, {
      availableDisplayModes: ["inline"],
      displayMode: "inline",
      containerDimensions: { maxWidth: 320, maxHeight: 500 },
    });
    await waitForCompactWidthAtMost(page, 320);
    await expect(page.locator("#fullscreenToggle")).toContainText("Try maximise");

    await expectToolsCalled(page, ["os_linked_ids.get"]);
    await assertNoPageErrors(pageErrors, "feature_inspector");
  });

  test("route planner satisfies compact strict acceptance contract", async ({ page }) => {
    const pageErrors = trackPageErrors(page);
    await page.setViewportSize({ width: 360, height: 500 });

    await installMcpBridge(page, {
      hostContext: HOST_PROFILES.claude_inline_500,
      toolRules: [],
      strictToolMatching: false,
    });

    await page.goto(uiFileUrl("route_planner.html"), { waitUntil: "domcontentloaded" });

    await expect(page.locator("#statusBadge")).toContainText("Host connected");
    await assertCompactGlobalContract(page, {
      ctaSelector: "#calculateRoute",
      statusSelector: "#statusBadge",
    });
    await assertKeyboardReachesTarget(page, "#calculateRoute");

    await page.fill("#startInput", "invalid");
    await page.click("#calculateRoute");
    await expect(page.locator("#flowStatus")).toContainText("lat,lon");

    const modes = await getSelectOptionValues(page, "#routeMode");
    for (const modeValue of modes) {
      await page.fill("#startInput", "51.500,-0.120");
      await page.fill("#endInput", "51.510,-0.100");
      await page.selectOption("#routeMode", modeValue);
      await page.click("#calculateRoute");
      await expect(page.locator("#flowStatus")).toContainText("Route ready");
      await expect(page.locator("#payload")).toContainText(`"mode": "${modeValue}"`);
    }

    await expect(page.locator("#fullscreenToggle")).toHaveText("Maximise");
    await page.click("#fullscreenToggle");
    await expect(page.locator("#fullscreenToggle")).toHaveText("Exit maximise");
    await page.click("#fullscreenToggle");

    await sendHostContextChanged(page, {
      availableDisplayModes: ["inline"],
      displayMode: "inline",
      containerDimensions: { maxWidth: 320, maxHeight: 500 },
    });
    await waitForCompactWidthAtMost(page, 320);
    await expect(page.locator("#fullscreenToggle")).toContainText("Try maximise");

    await assertNoPageErrors(pageErrors, "route_planner");
  });
});
