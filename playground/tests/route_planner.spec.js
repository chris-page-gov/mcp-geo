import { test, expect } from "@playwright/test";
import path from "path";
import { pathToFileURL, fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const MAPLIBRE_STUB = `
(() => {
  class FakeBounds {
    constructor() {
      this.points = [];
    }
    extend(point) {
      this.points.push(point);
      return this;
    }
    isEmpty() {
      return this.points.length === 0;
    }
  }

  class FakeMap {
    constructor(options) {
      this.options = options;
      this.handlers = new Map();
      this.sources = new Map();
      this.layers = new Map();
      setTimeout(() => this.emit("load"), 0);
    }

    on(name, handler) {
      if (!this.handlers.has(name)) this.handlers.set(name, []);
      this.handlers.get(name).push(handler);
    }

    emit(name, payload) {
      (this.handlers.get(name) || []).forEach((handler) => handler(payload));
    }

    addControl() {}

    setStyle(style) {
      this.style = style;
      setTimeout(() => this.emit("styledata", { style }), 0);
    }

    addSource(id, spec) {
      const source = {
        ...spec,
        data: spec.data,
        setData(next) {
          source.data = next;
        },
      };
      this.sources.set(id, source);
    }

    getSource(id) {
      return this.sources.get(id) || null;
    }

    addLayer(layer) {
      this.layers.set(layer.id, layer);
    }

    getLayer(id) {
      return this.layers.get(id) || null;
    }

    fitBounds() {}

    resize() {}
  }

  window.maplibregl = {
    workerUrl: "",
    NavigationControl: class {},
    LngLatBounds: FakeBounds,
    Map: FakeMap,
  };
})();
`;

test("route planner performs MCP host handshake and tool-backed route planning", async ({
  page,
}) => {
  await page.route("**/maplibre-gl@4.7.1/dist/maplibre-gl.css", async (route) => {
    await route.fulfill({ status: 200, contentType: "text/css", body: "" });
  });
  await page.route("**/maplibre-gl@4.7.1/dist/maplibre-gl.js", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/javascript",
      body: MAPLIBRE_STUB,
    });
  });
  await page.addInitScript(() => {
    window.__routeToolCalls = [];
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
            containerDimensions: { maxHeight: 500, maxWidth: 360 },
          },
        });
        return;
      }

      if (message.method === "ui/request-display-mode") {
        respond({ mode: message.params?.mode || "inline" });
        return;
      }

      if (message.method === "tools/call") {
        const name = message.params?.name || message.params?.tool;
        if (name === "os_apps.log_event" || name === "os_apps_log_event") {
          respond({ status: "logged" });
          return;
        }
        if (name === "os_route.get" || name === "os_route_get") {
          window.__routeToolCalls.push(message.params?.arguments || {});
          respond({
            profile: "emergency",
            distanceMeters: 3200,
            durationSeconds: 480,
            resolvedStops: [
              {
                label: "Retford Library",
                lat: 53.3221,
                lon: -0.9431,
              },
              {
                label: "Goodwin Hall",
                lat: 53.3212,
                lon: -0.9394,
              },
            ],
            route: {
              type: "Feature",
              geometry: {
                type: "LineString",
                coordinates: [
                  [-0.9431, 53.3221],
                  [-0.9418, 53.3217],
                  [-0.9394, 53.3212],
                ],
              },
              properties: { profile: "emergency" },
            },
            legs: [
              {
                distanceMeters: 3200,
                durationSeconds: 480,
                steps: [
                  {
                    instruction: "Follow Churchgate",
                    distanceMeters: 900,
                    durationSeconds: 120,
                    mode: "drive",
                  },
                  {
                    instruction: "Continue to Goodwin Hall",
                    distanceMeters: 2300,
                    durationSeconds: 360,
                    mode: "drive",
                  },
                ],
              },
            ],
            steps: [
              {
                instruction: "Follow Churchgate",
                distanceMeters: 900,
                durationSeconds: 120,
                mode: "drive",
              },
              {
                instruction: "Continue to Goodwin Hall",
                distanceMeters: 2300,
                durationSeconds: 360,
                mode: "drive",
              },
            ],
            warnings: [{ message: "Flood-risk zone 167647/3 treated as soft avoid." }],
            modeChanges: [],
            graph: {
              ready: true,
              graphVersion: "mrn-2026-03-01",
              sourceReleaseDate: "2026-03-01",
            },
          });
          return;
        }
      }

      respond({});
    });
  });

  const fileUrl = pathToFileURL(path.resolve(__dirname, "../../ui/route_planner.html")).href;
  await page.goto(fileUrl);

  await expect(page.locator("#statusBadge")).toContainText("Host connected");
  await expect(page.locator("#fullscreenToggle")).toContainText("Maximise");

  await page.fill("#startInput", "Retford Library, 17 Churchgate, Retford, DN22 6PE");
  await page.fill("#endInput", "Goodwin Hall, Chancery Lane, Retford, DN22 6DF");
  await page.fill("#avoidInput", "167647/3");
  await page.selectOption("#routeMode", "emergency");
  await page.click("#calculateRoute");

  await expect(page.locator("#flowStatus")).toContainText("Route ready");
  await expect(page.locator("#payload")).toContainText('"graphVersion": "mrn-2026-03-01"');
  await expect(page.locator("#routeSteps")).toContainText("Follow Churchgate");
  await expect(page.locator("#warnings")).toContainText("167647/3");
  await expect(page.locator("#map")).toHaveAttribute("data-route-rendered", "true");

  const toolCalls = await page.evaluate(() => window.__routeToolCalls);
  expect(toolCalls).toHaveLength(1);
  expect(toolCalls[0].profile).toBe("emergency");
  expect(toolCalls[0].constraints.avoidIds).toEqual(["167647/3"]);

  await page.fill("#startInput", "");
  await page.click("#calculateRoute");
  await expect(page.locator("#flowStatus")).toContainText("Enter valid start and end stops");
});
