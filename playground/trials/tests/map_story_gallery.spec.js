import { test, expect } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

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
const scenariosPath = path.join(repoRoot, "playground", "trials", "fixtures", "map_story_scenarios.json");
const scenariosData = JSON.parse(fs.readFileSync(scenariosPath, "utf-8"));
const scenarios = Array.isArray(scenariosData.stories) ? scenariosData.stories : [];
const mcpBaseUrl = process.env.MCP_GEO_TRIAL_BASE_URL || "http://127.0.0.1:8000";

const LATENCY_BUDGETS_MS = {
  default: 15_000,
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

function latencyDetails(startedAtMs, budget = LATENCY_BUDGETS_MS.default) {
  const latencyMs = Date.now() - startedAtMs;
  return {
    latencyMs,
    latencyBudgetMs: budget,
    latencyPass: latencyMs <= budget,
  };
}

async function mcpCall(request, payload, sessionId = null) {
  const headers = { "content-type": "application/json" };
  if (sessionId) {
    headers["mcp-session-id"] = sessionId;
  }
  const response = await request.post(`${mcpBaseUrl}/mcp`, {
    headers,
    data: payload,
  });
  expect(response.ok()).toBeTruthy();
  return {
    body: await response.json(),
    headers: response.headers(),
  };
}

function projectPoint(lon, lat, bbox, width, height) {
  const [minLon, minLat, maxLon, maxLat] = bbox;
  const x = ((lon - minLon) / (maxLon - minLon)) * width;
  const y = ((maxLat - lat) / (maxLat - minLat)) * height;
  return { x, y };
}

function ringPath(ring, bbox, width, height) {
  if (!Array.isArray(ring) || ring.length === 0) {
    return "";
  }
  const projected = ring
    .filter((coord) => Array.isArray(coord) && coord.length >= 2)
    .map(([lon, lat]) => projectPoint(lon, lat, bbox, width, height));
  if (projected.length < 2) {
    return "";
  }
  const [first, ...rest] = projected;
  return `M ${first.x.toFixed(2)} ${first.y.toFixed(2)} ${rest
    .map((p) => `L ${p.x.toFixed(2)} ${p.y.toFixed(2)}`)
    .join(" ")} Z`;
}

function centroidFromRing(ring, bbox, width, height) {
  if (!Array.isArray(ring) || ring.length === 0) {
    return null;
  }
  const projected = ring
    .filter((coord) => Array.isArray(coord) && coord.length >= 2)
    .map(([lon, lat]) => projectPoint(lon, lat, bbox, width, height));
  if (!projected.length) {
    return null;
  }
  const sum = projected.reduce(
    (acc, point) => ({ x: acc.x + point.x, y: acc.y + point.y }),
    { x: 0, y: 0 }
  );
  return {
    x: sum.x / projected.length,
    y: sum.y / projected.length,
  };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function styleFromProperties(kind, properties = {}) {
  const stroke = properties.stroke || (kind === "point" ? "#111827" : "#2563eb");
  const fill =
    properties.fill ||
    (kind === "polygon" ? "rgba(37,99,235,0.16)" : kind === "point" ? "#ffffff" : "none");
  const strokeWidth = Number.isFinite(Number(properties.strokeWidth))
    ? Number(properties.strokeWidth)
    : kind === "line"
      ? 3
      : 2;
  const dashArray = typeof properties.dashArray === "string" ? properties.dashArray : "";
  const radius = Number.isFinite(Number(properties.radius)) ? Number(properties.radius) : 5;
  return { stroke, fill, strokeWidth, dashArray, radius };
}

function geometryTypeToKind(geometryType) {
  if (geometryType === "Point" || geometryType === "MultiPoint") {
    return "point";
  }
  if (geometryType === "LineString" || geometryType === "MultiLineString") {
    return "line";
  }
  return "polygon";
}

function renderFeatureToSvg(feature, bbox, width, height) {
  if (!feature || typeof feature !== "object") {
    return { elements: [], labels: [] };
  }
  const geometry = feature.geometry || {};
  const properties = feature.properties || {};
  const geometryType = geometry.type;
  const coords = geometry.coordinates;
  const kind = geometryTypeToKind(geometryType);
  const style = styleFromProperties(kind, properties);
  const label = typeof properties.label === "string" ? properties.label : "";
  const elements = [];
  const labels = [];

  if (geometryType === "Point" && Array.isArray(coords) && coords.length >= 2) {
    const { x, y } = projectPoint(coords[0], coords[1], bbox, width, height);
    elements.push(
      `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="${style.radius}" fill="${escapeHtml(style.fill)}" stroke="${escapeHtml(style.stroke)}" stroke-width="${style.strokeWidth}" />`
    );
    if (label) {
      labels.push(`<text x="${(x + 8).toFixed(2)}" y="${(y - 8).toFixed(2)}" fill="#0f172a">${escapeHtml(label)}</text>`);
    }
    return { elements, labels };
  }

  if (geometryType === "MultiPoint" && Array.isArray(coords)) {
    for (const point of coords) {
      if (!Array.isArray(point) || point.length < 2) {
        continue;
      }
      const { x, y } = projectPoint(point[0], point[1], bbox, width, height);
      elements.push(
        `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="${style.radius}" fill="${escapeHtml(style.fill)}" stroke="${escapeHtml(style.stroke)}" stroke-width="${style.strokeWidth}" />`
      );
    }
    if (label && Array.isArray(coords[0])) {
      const { x, y } = projectPoint(coords[0][0], coords[0][1], bbox, width, height);
      labels.push(`<text x="${(x + 8).toFixed(2)}" y="${(y - 8).toFixed(2)}" fill="#0f172a">${escapeHtml(label)}</text>`);
    }
    return { elements, labels };
  }

  if (geometryType === "LineString" && Array.isArray(coords)) {
    const projected = coords
      .filter((coord) => Array.isArray(coord) && coord.length >= 2)
      .map(([lon, lat]) => projectPoint(lon, lat, bbox, width, height));
    if (projected.length >= 2) {
      const points = projected.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(" ");
      elements.push(
        `<polyline points="${points}" fill="none" stroke="${escapeHtml(style.stroke)}" stroke-width="${style.strokeWidth}" stroke-dasharray="${escapeHtml(style.dashArray)}" stroke-linecap="round" stroke-linejoin="round" />`
      );
      if (label) {
        const mid = projected[Math.floor(projected.length / 2)];
        labels.push(`<text x="${(mid.x + 8).toFixed(2)}" y="${(mid.y - 8).toFixed(2)}" fill="#111827">${escapeHtml(label)}</text>`);
      }
    }
    return { elements, labels };
  }

  if (geometryType === "MultiLineString" && Array.isArray(coords)) {
    for (const line of coords) {
      const projected = line
        .filter((coord) => Array.isArray(coord) && coord.length >= 2)
        .map(([lon, lat]) => projectPoint(lon, lat, bbox, width, height));
      if (projected.length < 2) {
        continue;
      }
      const points = projected.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(" ");
      elements.push(
        `<polyline points="${points}" fill="none" stroke="${escapeHtml(style.stroke)}" stroke-width="${style.strokeWidth}" stroke-dasharray="${escapeHtml(style.dashArray)}" stroke-linecap="round" stroke-linejoin="round" />`
      );
    }
    return { elements, labels };
  }

  if (geometryType === "Polygon" && Array.isArray(coords)) {
    const path = coords.map((ring) => ringPath(ring, bbox, width, height)).filter(Boolean).join(" ");
    if (path) {
      elements.push(
        `<path d="${path}" fill="${escapeHtml(style.fill)}" stroke="${escapeHtml(style.stroke)}" stroke-width="${style.strokeWidth}" stroke-dasharray="${escapeHtml(style.dashArray)}" />`
      );
      if (label) {
        const centroid = centroidFromRing(coords[0], bbox, width, height);
        if (centroid) {
          labels.push(`<text x="${centroid.x.toFixed(2)}" y="${centroid.y.toFixed(2)}" fill="#111827">${escapeHtml(label)}</text>`);
        }
      }
    }
    return { elements, labels };
  }

  if (geometryType === "MultiPolygon" && Array.isArray(coords)) {
    for (const polygon of coords) {
      const path = polygon
        .map((ring) => ringPath(ring, bbox, width, height))
        .filter(Boolean)
        .join(" ");
      if (!path) {
        continue;
      }
      elements.push(
        `<path d="${path}" fill="${escapeHtml(style.fill)}" stroke="${escapeHtml(style.stroke)}" stroke-width="${style.strokeWidth}" stroke-dasharray="${escapeHtml(style.dashArray)}" />`
      );
    }
    if (label && Array.isArray(coords[0]) && Array.isArray(coords[0][0])) {
      const centroid = centroidFromRing(coords[0][0], bbox, width, height);
      if (centroid) {
        labels.push(`<text x="${centroid.x.toFixed(2)}" y="${centroid.y.toFixed(2)}" fill="#111827">${escapeHtml(label)}</text>`);
      }
    }
    return { elements, labels };
  }

  return { elements, labels };
}

function buildOverlaySvg(overlayCollections, bbox, width, height) {
  const layerElements = [];
  const labelElements = [];
  for (const layer of overlayCollections || []) {
    const featureCollection = layer.featureCollection;
    const features = Array.isArray(featureCollection?.features) ? featureCollection.features : [];
    const itemElements = [];
    for (const feature of features) {
      const rendered = renderFeatureToSvg(feature, bbox, width, height);
      itemElements.push(...rendered.elements);
      labelElements.push(...rendered.labels);
    }
    if (itemElements.length) {
      layerElements.push(
        `<g data-layer-id="${escapeHtml(layer.id || "unknown")}">${itemElements.join("\n")}</g>`
      );
    }
  }

  return `<svg id="overlaySvg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" aria-label="Overlay layers">
    ${layerElements.join("\n")}
    <g class="labels">${labelElements.join("\n")}</g>
  </svg>`;
}

function legendItemsHtml(layers) {
  const safeLayers = Array.isArray(layers) ? layers : [];
  return safeLayers
    .map((layer) => {
      const id = escapeHtml(layer.id || "layer");
      const name = escapeHtml(layer.name || id);
      const count = Number.isFinite(Number(layer.count)) ? Number(layer.count) : 0;
      const kind = escapeHtml(layer.kind || "unknown");
      const source = escapeHtml(layer.source || "unknown");
      return `<li><span class="legend-name">${name}</span><span class="legend-meta">${kind} • ${source} • ${count}</span></li>`;
    })
    .join("\n");
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

async function captureMapPanel(page, testInfo, label, selector = "#mapPanel") {
  ensureEvidenceDirs();
  const project = safeSegment(testInfo.project.name);
  const testLabel = safeSegment(label);
  const fileName = `${project}-${testLabel}-map-panel.png`;
  const outputPath = path.join(screenshotDir, fileName);
  await page.locator(selector).screenshot({ path: outputPath });
  return outputPath;
}

for (const story of scenarios) {
  test(`${story.id}: ${story.title}`, async ({ request, page }, testInfo) => {
    test.skip(testInfo.project.name.includes("mobile"), "Story gallery screenshots are desktop-focused for slide production.");

    const startedAt = Date.now();

    const init = await mcpCall(request, {
      jsonrpc: "2.0",
      id: `${story.id}-init`,
      method: "initialize",
      params: { protocolVersion: "2025-11-25", capabilities: {} },
    });
    const sessionId = init.headers["mcp-session-id"];
    expect(sessionId).toBeTruthy();

    const renderCall = await mcpCall(
      request,
      {
        jsonrpc: "2.0",
        id: `${story.id}-render`,
        method: "tools/call",
        params: {
          name: "os_maps.render",
          arguments: {
            bbox: story.bbox,
            size: 1100,
            zoom: story.zoom || 13,
            overlays: story.overlays,
          },
        },
      },
      sessionId
    );

    const result = renderCall.body?.result;
    expect(result?.ok).toBeTruthy();

    const data = result?.data || {};
    const render = data.render || {};
    const overlayCollections = Array.isArray(data.overlayCollections) ? data.overlayCollections : [];
    const overlayLayers = Array.isArray(data.overlayLayers) ? data.overlayLayers : [];

    expect(typeof render.imageUrl).toBe("string");
    const mapUrl = new URL(render.imageUrl, mcpBaseUrl).toString();
    const mapWidth = Number.isFinite(Number(render.imageWidth)) ? Number(render.imageWidth) : 1100;
    const mapHeight = Number.isFinite(Number(render.imageHeight)) ? Number(render.imageHeight) : mapWidth;

    const overlaySvg = buildOverlaySvg(overlayCollections, story.bbox, mapWidth, mapHeight);
    const legendItems = legendItemsHtml(overlayLayers);
    const toolsHtml = (story.tools || []).map((tool) => `<li><code>${escapeHtml(tool)}</code></li>`).join("\n");
    const talkingPointsHtml = (story.talkingPoints || [])
      .map((point) => `<li>${escapeHtml(point)}</li>`)
      .join("\n");

    await page.setContent(`
      <main class="shell">
        <header>
          <h1>${escapeHtml(story.title)}</h1>
          <p class="subtitle">${escapeHtml(story.persona || "")}</p>
        </header>
        <section class="question">
          <p><strong>Question:</strong> ${escapeHtml(story.question || "")}</p>
          <p><strong>Decision:</strong> ${escapeHtml(story.decision || "")}</p>
        </section>
        <section class="layout">
          <figure id="mapPanel" class="map-panel">
            <img id="basemap" src="${mapUrl}" alt="${escapeHtml(story.title)}" width="${mapWidth}" height="${mapHeight}" />
            ${overlaySvg}
          </figure>
          <aside class="panel">
            <h2>Layer legend</h2>
            <ul class="legend">${legendItems}</ul>
            <h2>Tool choreography</h2>
            <ul class="tools">${toolsHtml}</ul>
            <h2>Talking points</h2>
            <ul class="talking-points">${talkingPointsHtml}</ul>
          </aside>
        </section>
      </main>
      <style>
        :root {
          --ink: #111827;
          --muted: #475569;
          --line: #d1d5db;
          --panel: rgba(255, 255, 255, 0.95);
          --bg-a: #eef2ff;
          --bg-b: #f8fafc;
          --accent: #2563eb;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
          color: var(--ink);
          background: radial-gradient(circle at top, var(--bg-a), var(--bg-b) 60%);
        }
        .shell {
          max-width: 1800px;
          margin: 0 auto;
          padding: 24px;
        }
        header h1 {
          margin: 0;
          font-size: 30px;
          line-height: 1.2;
        }
        .subtitle {
          margin: 6px 0 0;
          color: var(--muted);
          font-size: 16px;
        }
        .question {
          margin-top: 14px;
          padding: 14px 16px;
          border: 1px solid var(--line);
          border-radius: 12px;
          background: var(--panel);
          font-size: 15px;
        }
        .question p { margin: 6px 0; }
        .layout {
          margin-top: 16px;
          display: grid;
          grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.7fr);
          gap: 18px;
          align-items: start;
        }
        .map-panel {
          margin: 0;
          position: relative;
          border: 1px solid var(--line);
          border-radius: 14px;
          overflow: hidden;
          background: #fff;
        }
        .map-panel img {
          display: block;
          width: 100%;
          height: auto;
        }
        #overlaySvg {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
        }
        #overlaySvg .labels text {
          font-size: 13px;
          font-weight: 600;
          paint-order: stroke;
          stroke: rgba(255, 255, 255, 0.95);
          stroke-width: 3;
        }
        .panel {
          border: 1px solid var(--line);
          border-radius: 14px;
          background: var(--panel);
          padding: 14px;
        }
        .panel h2 {
          margin: 0 0 8px;
          font-size: 16px;
          color: var(--accent);
        }
        .panel ul {
          margin: 0 0 14px 0;
          padding-left: 16px;
          display: grid;
          gap: 6px;
        }
        .legend {
          list-style: none;
          padding-left: 0;
        }
        .legend li {
          border: 1px solid var(--line);
          border-radius: 10px;
          padding: 8px;
          display: grid;
          gap: 2px;
          background: #fff;
        }
        .legend-name {
          font-weight: 600;
          font-size: 13px;
        }
        .legend-meta {
          color: var(--muted);
          font-size: 12px;
        }
        code {
          font-family: "IBM Plex Mono", monospace;
          font-size: 12px;
          background: #eff6ff;
          padding: 2px 4px;
          border-radius: 4px;
        }
      </style>
    `);

    await page.waitForFunction(() => {
      const img = document.getElementById("basemap");
      return Boolean(img && img.complete && img.naturalWidth > 0 && img.naturalHeight > 0);
    });

    const screenshot = await captureEvidence(page, testInfo, story.id);
    const mapPanel = await captureMapPanel(page, testInfo, story.id);

    writeObservation(testInfo, story.id, {
      scenarioVersion: scenariosData.version || "unknown",
      storyTitle: story.title,
      persona: story.persona,
      question: story.question,
      decision: story.decision,
      tools: story.tools || [],
      overlayLayerCount: overlayLayers.length,
      overlayFeatureCounts: overlayLayers.map((layer) => ({
        id: layer.id,
        kind: layer.kind,
        count: layer.count,
        source: layer.source,
      })),
      mapUrl,
      screenshot,
      mapPanel,
      accessibility: {
        altText: `${story.title} layered map for ${story.persona}`,
      },
      ...latencyDetails(startedAt),
    });
  });
}
