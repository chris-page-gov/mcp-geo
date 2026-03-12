import { readFileSync } from "fs";
import http from "http";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../../..");
const UI_DIR = path.join(REPO_ROOT, "ui");
const SHARED_DIR = path.join(UI_DIR, "shared");
const VENDOR_DIR = path.join(UI_DIR, "vendor");
const BENCHMARK_PACK_PATH = path.join(
  REPO_ROOT,
  "data/benchmarking/stakeholder_eval/benchmark_pack_v1.json"
);
const BENCHMARK_LIVE_ALIAS_PATH = path.join(
  REPO_ROOT,
  "data/benchmarking/stakeholder_eval/live_run_latest.json"
);
const PNG_1X1 = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=",
  "base64"
);

const PORT = Number(process.env.PLAYGROUND_FIXTURE_PORT || 8787);
const SESSION_ID = "playground-fixture-session";
const SERVER_INFO = {
  name: "mcp-geo-playground-fixture",
  version: "2026-03-11",
};
const PROTOCOL_VERSION = "2025-11-25";
const MCP_APPS_PROTOCOL_VERSION = "2026-01-26";

function readJson(pathname) {
  return JSON.parse(readFileSync(pathname, "utf8"));
}

function sanitizeToolName(name) {
  return String(name || "")
    .replace(/[^A-Za-z0-9_-]/g, "_")
    .slice(0, 64);
}

function slugToResourceName(slug) {
  return `ui_${slug.replace(/-/g, "_")}`;
}

function uiMeta({ sameOrigin = false } = {}) {
  return {
    ui: {
      permissions: sameOrigin ? { sameOrigin: true } : {},
      csp: {
        connectDomains: ["self", `http://127.0.0.1:${PORT}`],
        resourceDomains: ["self", `http://127.0.0.1:${PORT}`],
        workerDomains: ["self", "blob:"],
      },
    },
  };
}

const UI_RESOURCES = [
  {
    slug: "route-planner",
    name: slugToResourceName("route-planner"),
    title: "Route Planner",
    description: "Deterministic route-planner MCP App fixture.",
    file: "route_planner.html",
    mimeType: "text/html;profile=mcp-app",
    type: "ui",
    _meta: uiMeta(),
  },
  {
    slug: "geography-selector",
    name: slugToResourceName("geography-selector"),
    title: "Geography Selector",
    description: "Deterministic geography-selector MCP App fixture.",
    file: "geography_selector.html",
    mimeType: "text/html;profile=mcp-app",
    type: "ui",
    _meta: uiMeta({ sameOrigin: true }),
  },
  {
    slug: "feature-inspector",
    name: slugToResourceName("feature-inspector"),
    title: "Feature Inspector",
    description: "Deterministic feature-inspector MCP App fixture.",
    file: "feature_inspector.html",
    mimeType: "text/html;profile=mcp-app",
    type: "ui",
    _meta: uiMeta(),
  },
  {
    slug: "statistics-dashboard",
    name: slugToResourceName("statistics-dashboard"),
    title: "Statistics Dashboard",
    description: "Deterministic statistics-dashboard MCP App fixture.",
    file: "statistics_dashboard.html",
    mimeType: "text/html;profile=mcp-app",
    type: "ui",
    _meta: uiMeta(),
  },
  {
    slug: "boundary-explorer",
    name: slugToResourceName("boundary-explorer"),
    title: "Map Lab",
    description: "Deterministic boundary-explorer MCP App fixture.",
    file: "boundary_explorer.html",
    mimeType: "text/html;profile=mcp-app",
    type: "ui",
    _meta: uiMeta({ sameOrigin: true }),
  },
];

const BENCHMARK_PACK = readJson(BENCHMARK_PACK_PATH);
const BENCHMARK_LIVE_ALIAS = readJson(BENCHMARK_LIVE_ALIAS_PATH);
const BENCHMARK_LIVE = readJson(
  path.join(path.dirname(BENCHMARK_LIVE_ALIAS_PATH), BENCHMARK_LIVE_ALIAS.aliasOf)
);
const UI_SHARED_COMPACT_CSS = readUiAsset(SHARED_DIR, "compact_contract.css");
const UI_SHARED_COMPACT_JS = readUiAsset(SHARED_DIR, "compact_contract.js");
const UI_VENDOR_MAPLIBRE_CSS = readUiAsset(VENDOR_DIR, "maplibre-gl.css");
const UI_VENDOR_MAPLIBRE_JS = readUiAsset(VENDOR_DIR, "maplibre-gl.js");
const UI_VENDOR_MAPLIBRE_WORKER_JS = readUiAsset(VENDOR_DIR, "maplibre-gl-csp-worker.js");
const UI_VENDOR_SHP_JS = readUiAsset(VENDOR_DIR, "shp.min.js");

const DATA_RESOURCES = [
  {
    uri: "resource://mcp-geo/stakeholder-benchmark-pack",
    name: "data_stakeholder_benchmark_pack",
    title: "Stakeholder Benchmark Pack",
    description: "Checked-in stakeholder benchmark pack fixture.",
    mimeType: "application/json",
    type: "data",
  },
  {
    uri: "resource://mcp-geo/stakeholder-benchmark-live-run-latest",
    name: "data_stakeholder_benchmark_live_run_latest",
    title: "Stakeholder Benchmark Live Run (Latest)",
    description: "Checked-in stakeholder live benchmark fixture.",
    mimeType: "application/json",
    type: "data",
  },
];

const RESOURCE_LIST = [
  ...UI_RESOURCES.map((resource) => ({
    uri: `ui://mcp-geo/${resource.slug}`,
    name: resource.name,
    title: resource.title,
    description: resource.description,
    mimeType: resource.mimeType,
    type: resource.type,
    _meta: resource._meta,
  })),
  ...DATA_RESOURCES,
];

function buildToolSchema(name) {
  return {
    type: "object",
    properties: {
      tool: { const: name },
    },
    additionalProperties: true,
  };
}

function buildTool(originalName, description) {
  return {
    name: sanitizeToolName(originalName),
    description,
    version: "fixture",
    inputSchema: buildToolSchema(originalName),
    outputSchema: { type: "object", additionalProperties: true },
    annotations: {
      originalName,
      mock: true,
    },
  };
}

const TOOLS = [
  buildTool("os_mcp.descriptor", "Fixture MCP descriptor"),
  buildTool("os_apps.render_route_planner", "Fixture route planner renderer"),
  buildTool("os_apps.render_geography_selector", "Fixture geography selector renderer"),
  buildTool("os_apps.render_feature_inspector", "Fixture feature inspector renderer"),
  buildTool("os_apps.render_statistics_dashboard", "Fixture statistics dashboard renderer"),
  buildTool("os_apps.render_boundary_explorer", "Fixture boundary explorer renderer"),
  buildTool("os_apps.log_event", "Fixture analytics sink"),
  buildTool("os_route.descriptor", "Fixture route descriptor"),
  buildTool("os_route.get", "Fixture route planner"),
  buildTool("os_places.search", "Fixture places search"),
  buildTool("os_places.nearest", "Fixture nearest places"),
  buildTool("os_places.by_postcode", "Fixture postcode lookup"),
  buildTool("os_places.by_uprn", "Fixture UPRN lookup"),
  buildTool("admin_lookup.find_by_name", "Fixture admin lookup by name"),
  buildTool("admin_lookup.containing_areas", "Fixture containing areas"),
  buildTool("admin_lookup.area_geometry", "Fixture area geometry"),
  buildTool("admin_lookup.get_cache_status", "Fixture admin cache status"),
  buildTool("ons_geo.cache_status", "Fixture ONS cache status"),
  buildTool("os_linked_ids.get", "Fixture linked IDs"),
  buildTool("ons_search.query", "Fixture ONS dataset search"),
  buildTool("ons_data.editions", "Fixture ONS editions"),
  buildTool("ons_data.versions", "Fixture ONS versions"),
  buildTool("ons_codes.list", "Fixture ONS code list"),
  buildTool("ons_codes.options", "Fixture ONS code options"),
  buildTool("ons_data.query", "Fixture ONS observations"),
  buildTool("os_map.inventory", "Fixture map inventory"),
  buildTool("os_map.export", "Fixture map export"),
  buildTool("os_map.get_export", "Fixture export status"),
];

const TOOL_ALIAS_MAP = new Map();
for (const tool of TOOLS) {
  TOOL_ALIAS_MAP.set(tool.name, tool.annotations.originalName);
  TOOL_ALIAS_MAP.set(tool.annotations.originalName, tool.annotations.originalName);
}

const STATE = {
  playEvents: [],
  toolCalls: [],
  auditPacks: [
    {
      packId: "pack-demo-001",
      scopeType: "conversation",
      retentionClass: "default_operational",
      legalHold: false,
      disclosures: [{ disclosureProfile: "internal_full" }],
      bundleHash: { fileName: "DSAP-pack-demo-001.zip", sha256: "abc123" },
      completeness: { grade: "A" },
    },
  ],
};

function sendJson(response, statusCode, payload, headers = {}) {
  response.writeHead(statusCode, {
    "content-type": "application/json",
    ...headers,
  });
  response.end(JSON.stringify(payload));
}

function sendBuffer(response, statusCode, body, contentType) {
  response.writeHead(statusCode, {
    "content-type": contentType,
    "cache-control": "public, max-age=300",
  });
  response.end(body);
}

function sendText(response, statusCode, body, contentType) {
  response.writeHead(statusCode, {
    "content-type": contentType,
    "cache-control": "public, max-age=300",
  });
  response.end(body);
}

async function readRequestBody(request) {
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function jsonRpcResult(id, result) {
  return { jsonrpc: "2.0", id, result };
}

function jsonRpcError(id, code, message, data = undefined) {
  const error = { code, message };
  if (data !== undefined) {
    error.data = data;
  }
  return { jsonrpc: "2.0", id, error };
}

function toolPayload(payload, meta = undefined) {
  return {
    data: payload,
    structuredContent: payload,
    content: [{ type: "json", json: payload }],
    ...(meta ? { _meta: meta } : {}),
  };
}

function readUiFile(fileName) {
  return readFileSync(path.join(UI_DIR, fileName), "utf8");
}

function readUiAsset(dirPath, assetName) {
  return readFileSync(path.join(dirPath, assetName));
}

function lookupUiResource(uriOrSlug) {
  const slug = String(uriOrSlug || "").replace(/^ui:\/\/mcp-geo\//, "");
  return UI_RESOURCES.find((resource) => resource.slug === slug) || null;
}

function lookupDataResource(uri) {
  return DATA_RESOURCES.find((resource) => resource.uri === uri) || null;
}

function resolveToolName(requestedName) {
  return TOOL_ALIAS_MAP.get(String(requestedName || "").trim()) || null;
}

function resolveRouteRequest(args = {}) {
  const stops = Array.isArray(args.stops) ? args.stops : [];
  const start = stops[0]?.query || stops[0]?.uprn || "";
  const end = stops[stops.length - 1]?.query || stops[stops.length - 1]?.uprn || "";
  const routeProfile = String(args.profile || "drive").toLowerCase();
  const blocked =
    String(start).includes("BLOCK_ROUTE") ||
    String(end).includes("BLOCK_ROUTE") ||
    (Array.isArray(args.constraints?.avoidIds) && args.constraints.avoidIds.includes("BLOCK_ROUTE"));
  if (blocked) {
    return {
      isError: true,
      code: "ROUTE_GRAPH_NOT_READY",
      message: "Route graph not ready for this seeded demonstration.",
      warnings: [{ message: "Run the seeded route-graph preflight before retrying." }],
      graph: { ready: false, reason: "ROUTE_GRAPH_NOT_READY" },
    };
  }
  return {
    profile: routeProfile,
    distanceMeters: 3200,
    durationSeconds: 480,
    resolvedStops: [
      {
        label: start || "Retford Library, 17 Churchgate, Retford, DN22 6PE",
        lat: 53.3221,
        lon: -0.9431,
      },
      {
        label: end || "Goodwin Hall, Chancery Lane, Retford, DN22 6DF",
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
      properties: { profile: routeProfile },
    },
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
      graphVersion: "mrn-fixture-2026-03-11",
      sourceReleaseDate: "2026-03-11",
    },
  };
}

function buildAppRenderPayload(slug, args = {}) {
  const resourceUri = `ui://mcp-geo/${slug}`;
  return {
    ok: true,
    resourceUri,
    uiResourceUris: [resourceUri],
    config: args,
    _meta: { ui: { resourceUri } },
  };
}

function buildToolCallResult(requestedName, args = {}) {
  const resolved = resolveToolName(requestedName);
  if (!resolved) {
    return { error: jsonRpcError(0, -32601, `Unknown tool: ${requestedName}`) };
  }

  if (requestedName === "os_places.search") {
    return {
      rpcError: {
        code: -32000,
        message: "Tool not found on server: os_places.search",
      },
    };
  }

  switch (resolved) {
    case "os_mcp.descriptor":
      return {
        result: toolPayload({
          server: SERVER_INFO.name,
          version: SERVER_INFO.version,
          protocolVersion: PROTOCOL_VERSION,
          supportedProtocolVersions: [PROTOCOL_VERSION],
          mcpAppsProtocolVersion: MCP_APPS_PROTOCOL_VERSION,
          transport: "streamable-http",
          capabilities: {
            tools: { listChanged: true },
            resources: { subscribe: false },
            prompts: {},
          },
          toolSearch: {
            counts: {
              total: TOOLS.length,
              always_loaded: TOOLS.length,
            },
          },
        }),
      };
    case "os_apps.render_route_planner":
      return { result: toolPayload(buildAppRenderPayload("route-planner", args)) };
    case "os_apps.render_geography_selector":
      return { result: toolPayload(buildAppRenderPayload("geography-selector", args)) };
    case "os_apps.render_feature_inspector":
      return { result: toolPayload(buildAppRenderPayload("feature-inspector", args)) };
    case "os_apps.render_statistics_dashboard":
      return { result: toolPayload(buildAppRenderPayload("statistics-dashboard", args)) };
    case "os_apps.render_boundary_explorer":
      return { result: toolPayload(buildAppRenderPayload("boundary-explorer", args)) };
    case "os_apps.log_event":
      return { result: toolPayload({ ok: true, logged: true, eventType: args.eventType || "unknown" }) };
    case "os_route.descriptor":
      return {
        result: toolPayload({
          ready: true,
          graphVersion: "mrn-fixture-2026-03-11",
          sourceReleaseDate: "2026-03-11",
          notes: ["Seeded deterministic route graph"],
        }),
      };
    case "os_route.get":
      return { result: toolPayload(resolveRouteRequest(args)) };
    case "os_places.search":
      return {
        result: toolPayload({
          results: [
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
              lat: 51.501,
              lon: -0.121,
              classificationDescription: "Residential",
            },
          ],
        }),
      };
    case "os_places.nearest":
      return {
        result: toolPayload({
          results: [
            {
              uprn: "1000000003",
              address: "Nottinghamshire Fire & Rescue Service, Fire Station, Wharf Road, Retford, DN22 6EN",
              lat: 53.3219807,
              lon: -0.9451639,
              classificationDescription: "Emergency service",
            },
          ],
          note: "Nearest responder candidate",
        }),
      };
    case "os_places.by_postcode":
      return {
        result: toolPayload({
          postcode: args.postcode || "DN22 6PE",
          results: [
            {
              uprn: "1000000004",
              address: "17 Churchgate, Retford, DN22 6PE",
              lat: 53.3221,
              lon: -0.9431,
            },
          ],
        }),
      };
    case "os_places.by_uprn":
      return {
        result: toolPayload({
          uprn: args.uprn || "1000000004",
          address: "17 Churchgate, Retford, DN22 6PE",
          lat: 53.3221,
          lon: -0.9431,
        }),
      };
    case "admin_lookup.find_by_name":
      return {
        result: toolPayload({
          results: [
            {
              id: "E08000026",
              name: "Coventry",
              type: "local-authority-district",
            },
          ],
        }),
      };
    case "admin_lookup.containing_areas":
      return {
        result: toolPayload({
          results: [
            {
              id: "E08000026",
              name: "Coventry",
              type: "local-authority-district",
            },
          ],
        }),
      };
    case "admin_lookup.area_geometry":
      return {
        result: toolPayload({
          id: args.id || "E08000026",
          name: "Coventry",
          type: "Feature",
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [-1.6, 52.36],
                [-1.4, 52.36],
                [-1.4, 52.48],
                [-1.6, 52.48],
                [-1.6, 52.36],
              ],
            ],
          },
        }),
      };
    case "admin_lookup.get_cache_status":
      return {
        result: toolPayload({
          configured: true,
          ready: true,
          entries: 42,
          source: "fixture",
        }),
      };
    case "ons_geo.cache_status":
      return {
        result: toolPayload({
          configured: true,
          ready: true,
          entries: 24,
          source: "fixture",
        }),
      };
    case "os_linked_ids.get":
      return {
        result: toolPayload({
          identifier: args.identifier || "1000000001",
          links: {
            uprn: "1000000001",
            usrn: "2000000001",
            toid: "osgb1000000001",
          },
        }),
      };
    case "ons_search.query":
      return {
        result: toolPayload({
          items: [
            {
              dataset: "housing-affordability",
              title: "Housing affordability ratio",
              description: "Fixture ONS dataset result",
            },
          ],
        }),
      };
    case "ons_data.editions":
      return { result: toolPayload({ items: ["time-series"] }) };
    case "ons_data.versions":
      return { result: toolPayload({ items: ["2025"] }) };
    case "ons_codes.list":
      return {
        result: toolPayload({
          items: [
            { code: "E08000026", label: "Coventry" },
            { code: "K02000001", label: "United Kingdom" },
          ],
        }),
      };
    case "ons_codes.options":
      return {
        result: toolPayload({
          items: [
            { code: "E08000026", label: "Coventry" },
            { code: "all", label: "All" },
          ],
        }),
      };
    case "ons_data.query":
      return {
        result: toolPayload({
          observations: [
            {
              geography: "E08000026",
              geographyLabel: "Coventry",
              time: "2025",
              measure: "median",
              value: 8.7,
            },
          ],
          dimensions: {
            geography: "geography",
            time: "time",
            measure: "measure",
          },
        }),
      };
    case "os_map.inventory":
      return {
        result: toolPayload({
          features: [
            {
              id: "feat-001",
              properties: { title: "Fixture feature" },
              geometry: { type: "Point", coordinates: [-1.5, 52.4] },
            },
          ],
        }),
      };
    case "os_map.export":
      return { result: toolPayload({ exportId: "export-001", status: "queued" }) };
    case "os_map.get_export":
      return {
        result: toolPayload({
          exportId: args.exportId || "export-001",
          status: "ready",
          downloadUrl: `http://127.0.0.1:${PORT}/audit/packs/pack-demo-001/bundle`,
        }),
      };
    default:
      return {
        result: toolPayload({
          ok: true,
          name: resolved,
          args,
        }),
      };
  }
}

async function handleMcp(request, response) {
  if (request.method === "GET" || request.method === "DELETE") {
    response.writeHead(405);
    response.end();
    return;
  }
  if (request.method !== "POST") {
    response.writeHead(405);
    response.end();
    return;
  }

  const rawBody = await readRequestBody(request);
  const message = JSON.parse(rawBody);
  const rpcMessage = Array.isArray(message) ? message[0] : message;
  const { id, method, params = {} } = rpcMessage;

  if (method === "notifications/initialized" || (id === undefined && method)) {
    response.writeHead(202);
    response.end();
    return;
  }

  if (method === "initialize") {
    sendJson(
      response,
      200,
      jsonRpcResult(id, {
        protocolVersion: PROTOCOL_VERSION,
        capabilities: {
          tools: { listChanged: true },
          resources: { subscribe: false },
          prompts: {},
        },
        serverInfo: SERVER_INFO,
        instructions: "Deterministic playground fixture server.",
      }),
      { "mcp-session-id": SESSION_ID }
    );
    return;
  }

  if (method === "tools/list") {
    sendJson(response, 200, jsonRpcResult(id, { tools: TOOLS }));
    return;
  }

  if (method === "resources/list") {
    sendJson(response, 200, jsonRpcResult(id, { resources: RESOURCE_LIST }));
    return;
  }

  if (method === "resources/templates/list") {
    sendJson(response, 200, jsonRpcResult(id, { resourceTemplates: [] }));
    return;
  }

  if (method === "prompts/list") {
    sendJson(
      response,
      200,
      jsonRpcResult(id, {
        prompts: [
          {
            name: "benchmark_prompt",
            description: "Fixture benchmark prompt entry",
          },
        ],
      })
    );
    return;
  }

  if (method === "resources/read") {
    const uri = params.uri || params.name;
    const uiResource = lookupUiResource(uri);
    if (uiResource) {
      sendJson(
        response,
        200,
        jsonRpcResult(id, {
          contents: [
            {
              uri: `ui://mcp-geo/${uiResource.slug}`,
              text: readUiFile(uiResource.file),
              mimeType: uiResource.mimeType,
              _meta: uiResource._meta,
            },
          ],
        })
      );
      return;
    }
    const dataResource = lookupDataResource(uri);
    if (dataResource) {
      const text =
        dataResource.uri === "resource://mcp-geo/stakeholder-benchmark-pack"
          ? JSON.stringify(BENCHMARK_PACK)
          : JSON.stringify(BENCHMARK_LIVE);
      sendJson(
        response,
        200,
        jsonRpcResult(id, {
          contents: [
            {
              uri: dataResource.uri,
              text,
              mimeType: dataResource.mimeType,
            },
          ],
        })
      );
      return;
    }
    sendJson(response, 200, jsonRpcError(id, -32000, `Unknown resource: ${uri}`));
    return;
  }

  if (method === "tools/call") {
    STATE.toolCalls.push({
      at: new Date().toISOString(),
      name: params.name || params.tool,
      arguments: params.arguments || {},
    });
    const outcome = buildToolCallResult(params.name || params.tool, params.arguments || {});
    if (outcome.rpcError) {
      sendJson(response, 200, jsonRpcError(id, outcome.rpcError.code, outcome.rpcError.message));
      return;
    }
    sendJson(response, 200, jsonRpcResult(id, outcome.result));
    return;
  }

  sendJson(response, 200, jsonRpcError(id, -32601, `Method not found: ${method}`));
}

function currentAuditPack() {
  return STATE.auditPacks[0];
}

async function handleAudit(request, response, pathname) {
  if (request.method === "GET" && pathname === "/audit/packs") {
    sendJson(response, 200, {
      packs: STATE.auditPacks.map((pack) => ({
        packId: pack.packId,
        scopeType: pack.scopeType,
        retentionClass: pack.retentionClass,
        legalHold: pack.legalHold,
        disclosures: pack.disclosures,
      })),
      nextPageToken: null,
    });
    return;
  }

  if (request.method === "POST" && pathname === "/audit/normalise") {
    sendJson(response, 200, {
      ok: true,
      path: "/tmp/event-ledger.jsonl",
      eventCount: 8,
    });
    return;
  }

  if (request.method === "POST" && pathname === "/audit/packs") {
    const pack = currentAuditPack();
    sendJson(response, 200, {
      ok: true,
      packId: pack.packId,
      path: `/tmp/${pack.packId}`,
    });
    return;
  }

  const match = pathname.match(/^\/audit\/packs\/([^/]+)(?:\/(bundle\/hash|bundle|verify|redact|legal-hold))?$/);
  if (!match) {
    sendJson(response, 404, { isError: true, message: "Not found" });
    return;
  }

  const packId = decodeURIComponent(match[1]);
  const action = match[2] || "";
  const pack = STATE.auditPacks.find((entry) => entry.packId === packId);
  if (!pack) {
    sendJson(response, 404, { isError: true, message: "Pack not found" });
    return;
  }

  if (!action && request.method === "GET") {
    sendJson(response, 200, pack);
    return;
  }

  if (action === "verify" && request.method === "POST") {
    sendJson(response, 200, { verified: true, packId });
    return;
  }

  if (action === "redact" && request.method === "POST") {
    const disclosure = "foi_redacted";
    if (!pack.disclosures.some((entry) => entry.disclosureProfile === disclosure)) {
      pack.disclosures = [...pack.disclosures, { disclosureProfile: disclosure }];
    }
    sendJson(response, 200, {
      ok: true,
      path: `/tmp/${packId}-foi`,
      disclosureProfile: disclosure,
    });
    return;
  }

  if (action === "legal-hold" && request.method === "POST") {
    const rawBody = await readRequestBody(request);
    const payload = rawBody ? JSON.parse(rawBody) : {};
    pack.legalHold = Boolean(payload.legalHold);
    sendJson(response, 200, {
      ok: true,
      packId,
      retentionState: { legalHold: pack.legalHold },
    });
    return;
  }

  if (action === "bundle" && request.method === "GET") {
    sendBuffer(response, 200, Buffer.from("PK"), "application/zip");
    return;
  }

  if (action === "bundle/hash" && request.method === "GET") {
    sendJson(response, 200, pack.bundleHash);
    return;
  }

  sendJson(response, 405, { isError: true, message: "Method not allowed" });
}

async function handlePlayground(request, response, pathname) {
  if (request.method !== "POST") {
    sendJson(response, 405, { isError: true, message: "Method not allowed" });
    return;
  }
  const rawBody = await readRequestBody(request);
  const payload = rawBody ? JSON.parse(rawBody) : {};
  STATE.playEvents.push({
    at: new Date().toISOString(),
    path: pathname,
    payload,
  });
  sendJson(response, 200, { ok: true });
}

function handleUiAsset(response, pathname) {
  if (pathname === "/ui/shared/compact_contract.css") {
    sendBuffer(response, 200, UI_SHARED_COMPACT_CSS, "text/css");
    return true;
  }
  if (pathname === "/ui/shared/compact_contract.js") {
    sendBuffer(response, 200, UI_SHARED_COMPACT_JS, "application/javascript");
    return true;
  }
  if (pathname === "/ui/vendor/maplibre-gl.css") {
    sendBuffer(response, 200, UI_VENDOR_MAPLIBRE_CSS, "text/css");
    return true;
  }
  if (pathname === "/ui/vendor/maplibre-gl.js") {
    sendBuffer(response, 200, UI_VENDOR_MAPLIBRE_JS, "application/javascript");
    return true;
  }
  if (pathname === "/ui/vendor/maplibre-gl-csp-worker.js") {
    sendBuffer(response, 200, UI_VENDOR_MAPLIBRE_WORKER_JS, "application/javascript");
    return true;
  }
  if (pathname === "/ui/vendor/shp.min.js") {
    sendBuffer(response, 200, UI_VENDOR_SHP_JS, "application/javascript");
    return true;
  }
  if (pathname.startsWith("/ui/")) {
    const resource = lookupUiResource(pathname.slice("/ui/".length));
    if (!resource) {
      return false;
    }
    sendText(response, 200, readUiFile(resource.file), "text/html");
    return true;
  }
  return false;
}

function handleMaps(response, pathname, searchParams) {
  if (pathname === "/maps/worker/maplibre-gl-csp-worker.js") {
    sendBuffer(response, 200, UI_VENDOR_MAPLIBRE_WORKER_JS, "application/javascript");
    return true;
  }
  if (pathname === "/maps/vector/vts/resources/styles") {
    const styleName = searchParams.get("style") || "OS_VTS_3857_Light.json";
    sendJson(response, 200, {
      version: 8,
      name: styleName,
      sources: {},
      layers: [
        {
          id: "background",
          type: "background",
          paint: { "background-color": "#eff3ea" },
        },
      ],
    });
    return true;
  }
  if (pathname.startsWith("/maps/raster/osm/")) {
    sendBuffer(response, 200, PNG_1X1, "image/png");
    return true;
  }
  return false;
}

const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url || "/", `http://127.0.0.1:${PORT}`);
    const pathname = url.pathname;

    if (pathname === "/health") {
      sendJson(response, 200, { ok: true, fixture: true });
      return;
    }
    if (pathname === "/mcp") {
      await handleMcp(request, response);
      return;
    }
    if (pathname.startsWith("/audit/")) {
      await handleAudit(request, response, pathname);
      return;
    }
    if (pathname.startsWith("/playground/")) {
      await handlePlayground(request, response, pathname);
      return;
    }
    if (handleUiAsset(response, pathname)) {
      return;
    }
    if (handleMaps(response, pathname, url.searchParams)) {
      return;
    }

    sendJson(response, 404, { isError: true, message: "Not found" });
  } catch {
    console.error("[fixture-server] unhandled request error");
    sendJson(response, 500, {
      isError: true,
      message: "Internal server error",
    });
  }
});

server.listen(PORT, "127.0.0.1", () => {
  process.stdout.write(`playground fixture server listening on http://127.0.0.1:${PORT}\n`);
});
