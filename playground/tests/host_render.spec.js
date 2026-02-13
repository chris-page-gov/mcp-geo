import { test, expect } from "@playwright/test";
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "../..");
const pythonPath = path.join(repoRoot, ".venv", "bin", "python");
const port = 8765 + Math.floor(Math.random() * 200);
const baseUrl = `http://127.0.0.1:${port}`;
const uiMime = "text/html;profile=mcp-app";

let serverProcess;

async function waitForServerReady() {
  for (let attempt = 0; attempt < 80; attempt += 1) {
    try {
      const resp = await fetch(`${baseUrl}/health`);
      if (resp.ok) {
        return;
      }
    } catch {
      // Wait and retry while uvicorn starts.
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Timed out waiting for MCP server at ${baseUrl}`);
}

async function mcpCall(request, { sessionId = null, id, method, params }) {
  const headers = { "content-type": "application/json" };
  if (sessionId) {
    headers["mcp-session-id"] = sessionId;
  }
  const resp = await request.post(`${baseUrl}/mcp`, {
    headers,
    data: { jsonrpc: "2.0", id, method, params },
  });
  expect(resp.ok()).toBeTruthy();
  const allHeaders = resp.headers();
  const nextSessionId = allHeaders["mcp-session-id"] || sessionId;
  const body = await resp.json();
  return { body, sessionId: nextSessionId };
}

test.beforeAll(async () => {
  serverProcess = spawn(
    pythonPath,
    [
      "-m",
      "uvicorn",
      "server.main:app",
      "--host",
      "127.0.0.1",
      "--port",
      String(port),
      "--log-level",
      "warning",
    ],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: repoRoot,
      },
      stdio: "ignore",
    }
  );
  await waitForServerReady();
});

test.afterAll(async () => {
  if (!serverProcess) {
    return;
  }
  serverProcess.kill("SIGTERM");
  await new Promise((resolve) => setTimeout(resolve, 300));
});

test("ui-capable host receives render payload without fallback", async ({ request }) => {
  const init = await mcpCall(request, {
    id: "init-ui",
    method: "initialize",
    params: {
      protocolVersion: "2025-11-25",
      capabilities: {
        extensions: {
          "io.modelcontextprotocol/ui": {
            mimeTypes: [uiMime],
          },
        },
      },
    },
  });

  const call = await mcpCall(request, {
    sessionId: init.sessionId,
    id: "call-ui",
    method: "tools/call",
    params: {
      name: "os_apps_render_geography_selector",
      arguments: {
        level: "ward",
        initialLat: 51.5,
        initialLng: -0.12,
        initialZoom: 14,
      },
    },
  });

  const result = call.body.result;
  expect(result.ok).toBeTruthy();
  expect(result.data.fallback).toBeUndefined();
  expect(result.data._meta.ui.resourceUri).toBe("ui://mcp-geo/geography-selector");
});

test("non-ui host receives deterministic static fallback payload", async ({ request }) => {
  const init = await mcpCall(request, {
    id: "init-no-ui",
    method: "initialize",
    params: {
      protocolVersion: "2025-11-25",
      capabilities: {},
    },
  });

  const call = await mcpCall(request, {
    sessionId: init.sessionId,
    id: "call-no-ui",
    method: "tools/call",
    params: {
      name: "os_apps_render_geography_selector",
      arguments: { initialLat: 52.0, initialLng: -1.0, initialZoom: 16 },
    },
  });

  const fallback = call.body.result.data.fallback;
  expect(fallback.type).toBe("static_map");
  expect(fallback.render).toBeTruthy();
  expect(fallback.center).toEqual({ lat: 52.0, lng: -1.0 });
});

test("sanitized and dotted tool names both resolve for render calls", async ({ request }) => {
  const init = await mcpCall(request, {
    id: "init-sanitized",
    method: "initialize",
    params: {
      protocolVersion: "2025-11-25",
      capabilities: {},
    },
  });

  const callSanitized = await mcpCall(request, {
    sessionId: init.sessionId,
    id: "call-sanitized",
    method: "tools/call",
    params: {
      name: "os_apps_render_statistics_dashboard",
      arguments: {
        areaCodes: ["E09000033"],
        dataset: "gdp",
        measure: "GDPV",
      },
    },
  });
  const callDotted = await mcpCall(request, {
    sessionId: init.sessionId,
    id: "call-dotted",
    method: "tools/call",
    params: {
      name: "os_apps.render_statistics_dashboard",
      arguments: {
        areaCodes: ["E09000033"],
        dataset: "gdp",
        measure: "GDPV",
      },
    },
  });

  const fallbackSanitized = callSanitized.body.result.data.fallback;
  const fallbackDotted = callDotted.body.result.data.fallback;
  expect(fallbackSanitized.type).toBe("statistics_dashboard");
  expect(fallbackDotted.type).toBe("statistics_dashboard");
  expect(fallbackSanitized.suggestedTools).toContain("nomis.query");
  expect(fallbackDotted.suggestedTools).toContain("nomis.query");
});
