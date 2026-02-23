import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test("boundary explorer host harness renders selected boundary and records fullscreen handshake fallback", async ({
  page,
}) => {
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
            availableDisplayModes: ["inline"],
            platform: "web",
            userAgent: "playwright",
            containerDimensions: { maxHeight: 760 },
            mcpGeo: { proxyBase: "http://localhost:8000" },
          },
        });
        return;
      }

      if (message.method === "ui/request-display-mode") {
        // Simulate host acknowledging request envelope but refusing mode transition.
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
              bbox: [-1.55509867953086, 52.4038886707963, -1.51486823563564, 52.4299515583343],
            },
          ],
          count: 1,
          live: true,
        });
        return;
      }

      if (name === "admin_lookup_area_geometry") {
        respond({
          isError: true,
          code: "ADMIN_LOOKUP_API_ERROR",
          message: "Admin lookup live query failed (all sources failed).",
        });
        return;
      }

      if (name === "os_map_inventory") {
        respond({
          layers: {
            uprns: { results: [] },
            buildings: { features: [] },
            road_links: { features: [] },
            path_links: { features: [] },
          },
        });
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
  await expect(page.locator("#fullscreenToggle")).toContainText("Try maximise");

  await page.fill("#searchInput", "Sherbourne");
  await page.click("#searchButton");
  await page.waitForSelector(".result");
  await page.click(".result [data-action='toggle']");

  await page.waitForFunction(() => {
    const probe = window.__MCP_GEO_BOUNDARY_EXPLORER__;
    if (!probe || typeof probe.getSnapshot !== "function") {
      return false;
    }
    const snapshot = probe.getSnapshot();
    const selected = snapshot?.selection?.selectedCount || 0;
    const sourceCount = snapshot?.boundaries?.sourceFeatureCount || 0;
    const renderedLine = snapshot?.boundaries?.renderedBoundaryLineCount || 0;
    const renderedOutline = snapshot?.boundaries?.renderedSelectedOutlineCount || 0;
    return selected === 1 && sourceCount === 1 && renderedLine + renderedOutline > 0;
  });

  const snapshot = await page.evaluate(() => window.__MCP_GEO_BOUNDARY_EXPLORER__.getSnapshot());
  expect(snapshot.selection.selectedCount).toBe(1);
  expect(snapshot.boundaries.sourceFeatureCount).toBe(1);
  expect(
    (snapshot.boundaries.renderedBoundaryLineCount || 0) +
      (snapshot.boundaries.renderedSelectedOutlineCount || 0)
  ).toBeGreaterThan(0);

  await page.click("#fullscreenToggle");
  await expect(page.locator("#infoBanner")).toContainText(
    "did not confirm fullscreen mode"
  );
});
