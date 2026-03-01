import { test, expect } from "@playwright/test";
import path from "path";
import { pathToFileURL, fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const MAPLIBRE_STUB = `
(() => {
  class FakeMap {
    constructor(options) {
      this.options = options;
      this.handlers = new Map();
      this.onceHandlers = new Map();
      this.center = { lng: options.center?.[0] ?? 0, lat: options.center?.[1] ?? 0 };
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
      const list = this.handlers.get(name) || [];
      list.forEach((handler) => handler(payload));
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

    easeTo(opts) {
      this.center = {
        lng: opts.center?.[0] ?? this.center.lng,
        lat: opts.center?.[1] ?? this.center.lat,
      };
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

test("simple map auth mode and style diagnostics are deterministic", async ({ page }) => {
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
      body: JSON.stringify({
        version: 8,
        sources: {
          os_vts: {
            type: "vector",
            tiles: ["http://localhost/maps/vector/vts/tile/{z}/{x}/{y}.pbf"],
          },
        },
        layers: [{ id: "background", type: "background", paint: { "background-color": "#f4f7f8" } }],
      }),
    });
  });

  await page.route("**/maps/vector/vts/tile/**", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/x-protobuf", body: "" });
  });

  const fileUrl = pathToFileURL(path.resolve(__dirname, "../../ui/simple_map.html")).href;
  await page.goto(fileUrl);
  await page.fill("#proxyBase", "http://localhost:8000");

  await expect(page.locator("#token")).toHaveAttribute("type", "password");
  await expect(page.locator("#apiKey")).toHaveAttribute("type", "password");

  await page.fill("#token", '{"access_token":"token-abc"}');
  await page.click("#loadBtn");
  await expect(page.locator("#status")).toContainText("browser token");
  await expect(page.locator("#authMode")).toContainText("Browser bearer token");
  await expect(page.locator("#timings")).toContainText('"authMode": "bearer"');

  await page.fill("#token", "");
  await page.fill("#apiKey", "api-key-123");
  await page.click("#loadBtn");
  await expect(page.locator("#status")).toContainText("API key");
  await expect(page.locator("#authMode")).toContainText("API key override");
  await expect(page.locator("#timings")).toContainText('"authMode": "api_key"');

  await page.fill("#apiKey", "");
  await page.selectOption("#osStyle", "OS_VTS_3857_Dark.json");
  await page.click("#loadBtn");
  await expect(page.locator("#status")).toContainText("server's saved OS key");
  await expect(page.locator("#authMode")).toContainText("Server environment key");
  await expect(page.locator("#timings")).toContainText('"authMode": "server_env"');
  await expect(page.locator("#timings")).toContainText('"selectedStyle": "OS_VTS_3857_Dark.json"');
});
