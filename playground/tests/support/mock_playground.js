import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO_ROOT = path.resolve(__dirname, "../../..");

const BENCHMARK_PACK = JSON.parse(
  fs.readFileSync(
    path.join(REPO_ROOT, "data/benchmarking/stakeholder_eval/benchmark_pack_v1.json"),
    "utf8"
  )
);
const BENCHMARK_LIVE = JSON.parse(
  fs.readFileSync(
    path.join(REPO_ROOT, "data/benchmarking/stakeholder_eval/live_run_2026-03-10.json"),
    "utf8"
  )
);

const UNIQUE_TOOLS = Array.from(
  new Set(
    ["os_mcp_descriptor", "os_route.descriptor", ...BENCHMARK_PACK.scenarios.flatMap((scenario) => scenario.mcpGeoTools)]
  )
).sort();

const TOOL_LIST = UNIQUE_TOOLS.map((name) => ({
  name,
  description: `${name} mock tool`,
  inputSchema: {
    type: "object",
    properties: {
      tool: { const: name },
    },
  },
  outputSchema: { type: "object" },
  annotations: { mock: true },
  version: "test",
}));

const RESOURCE_LIST = [
  {
    uri: "ui://mcp-geo/route-planner",
    name: "ui_route_planner",
    title: "Route Planner",
    description: "Mock route planner widget",
    mimeType: "text/html;profile=mcp-app",
    type: "ui",
  },
  {
    uri: "ui://mcp-geo/geography-selector",
    name: "ui_geography_selector",
    title: "Geography Selector",
    description: "Mock geography selector widget",
    mimeType: "text/html;profile=mcp-app",
    type: "ui",
  },
  {
    uri: "resource://mcp-geo/stakeholder-benchmark-pack",
    name: "data_stakeholder_benchmark_pack",
    title: "Stakeholder Benchmark Pack",
    description: "Mock benchmark pack resource",
    mimeType: "application/json",
    type: "data",
  },
  {
    uri: "resource://mcp-geo/stakeholder-benchmark-live-run-latest",
    name: "data_stakeholder_benchmark_live_run_latest",
    title: "Stakeholder Benchmark Live Run (Latest)",
    description: "Mock benchmark live resource",
    mimeType: "application/json",
    type: "data",
  },
];

const WIDGET_HTML = String.raw`<!DOCTYPE html>
<html lang="en">
  <body>
    <h1 id="widgetTitle">Mock MCP Widget</h1>
    <div id="widgetStatus">Booting</div>
    <button id="callAllowedTool">Call allowed tool</button>
    <button id="callBadTool">Send bad tool call</button>
    <button id="readBadResource">Send bad resource read</button>
    <pre id="receivedConfig"></pre>
    <pre id="lastResult"></pre>
    <script>
      const pendingCalls = new Map();
      let rpcId = 0;
      const bridgeState = { sessionToken: null };

      function capturePreviewToken(result) {
        const token =
          result &&
          (result.mcpGeoPreview?.sessionToken || result.hostContext?.mcpGeoPreview?.sessionToken);
        if (typeof token === "string" && token) {
          bridgeState.sessionToken = token;
        }
      }

      function hasValidPreviewToken(message) {
        if (!bridgeState.sessionToken) {
          return true;
        }
        return message?.__mcpGeoHost?.sessionToken === bridgeState.sessionToken;
      }

      function postToHost(message) {
        const payload =
          bridgeState.sessionToken
            ? {
                ...message,
                __mcpGeoHost: {
                  ...(message.__mcpGeoHost || {}),
                  sessionToken: bridgeState.sessionToken,
                },
              }
            : message;
        window.parent.postMessage(payload, "*");
      }

      function rpcCall(method, params) {
        rpcId += 1;
        const id = rpcId;
        postToHost({ jsonrpc: "2.0", id, method, params });
        return new Promise((resolve, reject) => {
          pendingCalls.set(id, { resolve, reject });
          setTimeout(() => {
            if (pendingCalls.has(id)) {
              pendingCalls.delete(id);
              reject(new Error("RPC timeout"));
            }
          }, 15000);
        });
      }

      function rpcNotify(method, params) {
        postToHost({ jsonrpc: "2.0", method, params });
      }

      window.addEventListener("message", (event) => {
        const message = event.data;
        if (!message || message.jsonrpc !== "2.0") {
          return;
        }
        if (!hasValidPreviewToken(message)) {
          return;
        }
        if (message.id !== undefined && (message.result !== undefined || message.error)) {
          const pending = pendingCalls.get(message.id);
          if (pending) {
            pendingCalls.delete(message.id);
            if (message.error) {
              pending.reject(new Error(message.error.message || "RPC error"));
            } else {
              capturePreviewToken(message.result);
              pending.resolve(message.result);
            }
          }
          return;
        }
        if (message.method === "ui/notifications/tool-input") {
          document.getElementById("receivedConfig").textContent = JSON.stringify(
            message.params?.arguments || message.params?.config || {},
            null,
            2
          );
        }
      });

      document.getElementById("callAllowedTool").addEventListener("click", async () => {
        const result = await rpcCall("tools/call", {
          name: "os_apps.render_route_planner",
          arguments: { tool: "os_apps.render_route_planner", origin: "Retford Library" },
        });
        document.getElementById("lastResult").textContent = JSON.stringify(result, null, 2);
      });

      document.getElementById("callBadTool").addEventListener("click", () => {
        window.parent.postMessage(
          {
            jsonrpc: "2.0",
            id: 991,
            method: "tools/call",
            params: {
              name: "os_apps.render_route_planner",
              arguments: { tool: "os_apps.render_route_planner", origin: "Retford Library" },
            },
          },
          "*"
        );
      });

      document.getElementById("readBadResource").addEventListener("click", () => {
        window.parent.postMessage(
          {
            jsonrpc: "2.0",
            id: 992,
            method: "resources/read",
            params: { uri: "resource://mcp-geo/not-allowed" },
          },
          "*"
        );
      });

      (async () => {
        const result = await rpcCall("ui/initialize", {
          appCapabilities: { availableDisplayModes: ["inline", "fullscreen"] },
        });
        capturePreviewToken(result);
        document.getElementById("widgetStatus").textContent = "Host connected";
        rpcNotify("ui/notifications/initialized", { widget: "mock" });
      })();
    </script>
  </body>
</html>`;

export async function installPlaygroundMocks(page) {
  await page.addInitScript(
    ({ benchmarkPack, benchmarkLive, tools, resources, widgetHtml }) => {
      const descriptor = {
        server: "mcp-geo",
        version: "test-playground",
        protocolVersion: "2026-02-20",
        supportedProtocolVersions: ["2026-02-20"],
        mcpAppsProtocolVersion: "2026-01-26",
        transport: "http",
        capabilities: {
          tools: { listChanged: true },
          resources: { subscribe: false },
          prompts: {},
        },
        toolSearch: {
          counts: {
            total: tools.length,
            always_loaded: tools.length,
          },
        },
      };

      function mockResourceContents(uri) {
        if (uri === "resource://mcp-geo/stakeholder-benchmark-pack") {
          return {
            contents: [{ text: JSON.stringify(benchmarkPack), mimeType: "application/json" }],
          };
        }
        if (uri === "resource://mcp-geo/stakeholder-benchmark-live-run-latest") {
          return {
            contents: [{ text: JSON.stringify(benchmarkLive), mimeType: "application/json" }],
          };
        }
        if (uri.startsWith("ui://")) {
          return {
            contents: [
              {
                text: widgetHtml,
                mimeType: "text/html;profile=mcp-app",
                _meta: {
                  ui: {
                    permissions: { sameOrigin: true },
                  },
                },
              },
            ],
          };
        }
        return {
          contents: [{ text: JSON.stringify({ uri, ok: true }), mimeType: "application/json" }],
        };
      }

      window.__MCP_PLAYGROUND_MOCK__ = {
        async connect() {
          return { capabilities: descriptor.capabilities };
        },
        async close() {},
        async request(request) {
          const method = request?.method;
          if (method === "tools/list") {
            return { tools };
          }
          if (method === "resources/list") {
            return { resources };
          }
          if (method === "resources/templates/list") {
            return { resourceTemplates: [] };
          }
          if (method === "prompts/list") {
            return {
              prompts: [
                { name: "benchmark_prompt", description: "Mock prompt for playground tests" },
              ],
            };
          }
          if (method === "resources/read") {
            return mockResourceContents(request.params?.uri);
          }
          if (method === "tools/call") {
            const name = request.params?.name || request.params?.tool;
            const args = request.params?.arguments || {};
            if (name === "os_mcp_descriptor") {
              return { data: descriptor };
            }
            if (name === "os_route.descriptor") {
              return { data: { graph: { ready: true, graphVersion: "benchmark-v1" } } };
            }
            if (name === "os_places.nearest") {
              return {
                data: {
                  address: "GOODWIN HALL, CHANCERY LANE, RETFORD, DN22 6DF",
                  lat: args.lat,
                  lon: args.lon,
                },
              };
            }
            if (name === "os_apps.render_route_planner") {
              return {
                status: "ready",
                resourceUri: "ui://mcp-geo/route-planner",
                uiResourceUris: ["ui://mcp-geo/route-planner"],
                config: args,
                _meta: { ui: { resourceUri: "ui://mcp-geo/route-planner" } },
              };
            }
            return {
              data: {
                ok: true,
                name,
                args,
              },
            };
          }
          throw new Error(`Unhandled mock request: ${method}`);
        },
      };
    },
    {
      benchmarkPack: BENCHMARK_PACK,
      benchmarkLive: BENCHMARK_LIVE,
      resources: RESOURCE_LIST,
      tools: TOOL_LIST,
      widgetHtml: WIDGET_HTML,
    }
  );
}

export async function installAuditMocks(page) {
  const packSummary = {
    packId: "pack-demo-001",
    scopeType: "conversation",
    retentionClass: "default_operational",
    legalHold: false,
    disclosures: [{ disclosureProfile: "internal_full" }],
  };
  const packDetail = {
    ...packSummary,
    bundleHash: { fileName: "DSAP-pack-demo-001.zip", sha256: "abc123" },
    completeness: { grade: "A" },
  };

  await page.route("**/audit/packs?limit=50", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ packs: [packSummary], nextPageToken: null }),
    });
  });

  await page.route("**/audit/normalise", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, path: "/tmp/event-ledger.jsonl", eventCount: 8 }),
    });
  });

  await page.route("**/audit/packs", async (route) => {
    if (route.request().method() !== "POST") {
      return route.continue();
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true, packId: "pack-demo-001", path: "/tmp/pack-demo-001" }),
    });
  });

  await page.route("**/audit/packs/pack-demo-001/bundle", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/zip",
      body: "PK",
    });
  });

  await page.route("**/audit/packs/pack-demo-001/bundle/hash", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ fileName: "DSAP-pack-demo-001.zip", sha256: "abc123" }),
    });
  });

  await page.route("**/audit/packs/pack-demo-001/verify", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ verified: true }),
    });
  });

  await page.route("**/audit/packs/pack-demo-001/redact", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        path: "/tmp/pack-demo-001-foi",
        disclosureProfile: "foi_redacted",
      }),
    });
  });

  await page.route("**/audit/packs/pack-demo-001/legal-hold", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        ok: true,
        packId: "pack-demo-001",
        retentionState: { legalHold: true },
      }),
    });
  });

  await page.route("**/audit/packs/pack-demo-001", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(packDetail),
    });
  });
}
