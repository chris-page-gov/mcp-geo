import os from "os";
import path from "path";
import { mkdtemp, mkdir, rm, writeFile } from "fs/promises";

let cachedRoutePreflight = null;

async function readJson(response) {
  const bodyText = await response.text();
  let payload = null;
  if (bodyText) {
    try {
      payload = JSON.parse(bodyText);
    } catch (_error) {
      payload = { rawText: bodyText };
    }
  }
  return {
    ok: response.ok(),
    status: response.status(),
    payload,
  };
}

async function postTool(request, tool, args = {}) {
  const response = await request.post("/tools/call", {
    data: {
      tool,
      ...args,
    },
  });
  return readJson(response);
}

export async function getLiveRoutePreflight(request) {
  if (cachedRoutePreflight) {
    return cachedRoutePreflight;
  }

  const reasons = [];
  const healthResponse = await request.get("/health");
  if (!healthResponse.ok()) {
    cachedRoutePreflight = {
      ready: false,
      reason: `Live backend health check failed with ${healthResponse.status()}.`,
    };
    return cachedRoutePreflight;
  }

  const cacheStatus = await postTool(request, "ons_geo.cache_status");
  if (!cacheStatus.ok || cacheStatus.payload?.isError) {
    reasons.push("ONS cache status could not be read.");
  }

  const routeDescriptor = await postTool(request, "os_route.descriptor");
  if (!routeDescriptor.ok || routeDescriptor.payload?.isError) {
    reasons.push("Route descriptor failed.");
  } else if (!routeDescriptor.payload?.graph?.ready) {
    reasons.push("Seeded route graph is not ready.");
  }

  const placesProbe = await postTool(request, "os_places.search", {
    text: "Retford Library, 17 Churchgate, Retford, DN22 6PE",
    limit: 1,
  });
  if (!placesProbe.ok || placesProbe.payload?.isError) {
    const code = placesProbe.payload?.code;
    if (code === "NO_API_KEY") {
      reasons.push("OS_API_KEY is not available to the live backend.");
    } else {
      reasons.push(`OS Places probe failed${code ? ` (${code})` : ""}.`);
    }
  }

  cachedRoutePreflight = {
    ready: reasons.length === 0,
    reason: reasons.join(" "),
    details: {
      cacheStatus: cacheStatus.payload,
      routeDescriptor: routeDescriptor.payload,
      placesProbe: placesProbe.payload,
    },
  };
  return cachedRoutePreflight;
}

function writeJsonl(rows) {
  return `${rows.map((row) => JSON.stringify(row)).join("\n")}\n`;
}

export async function createAuditSmokeSession() {
  const sessionRoot = await mkdtemp(path.join(os.tmpdir(), "mcp-geo-live-audit-"));
  const sessionDir = path.join(sessionRoot, "session");
  await mkdir(sessionDir, { recursive: true });

  await writeFile(
    path.join(sessionDir, "session.json"),
    JSON.stringify(
      {
        sessionId: "playground-live-smoke",
        mode: "stdio",
        source: "codex",
        surface: "playwright",
        startedAt: "2026-03-11T09:00:00Z",
        endedAt: "2026-03-11T09:00:30Z",
        exitCode: 0,
      },
      null,
      2
    ),
    "utf8"
  );

  await writeFile(
    path.join(sessionDir, "mcp-stdio-trace.jsonl"),
    writeJsonl([
      {
        ts: 1773229200.1,
        direction: "client->server",
        json: {
          jsonrpc: "2.0",
          id: 1,
          method: "initialize",
          params: { capabilities: { tools: {} } },
        },
      },
      {
        ts: 1773229200.2,
        direction: "server->client",
        json: {
          jsonrpc: "2.0",
          id: 1,
          result: { protocolVersion: "2025-11-25" },
        },
      },
      {
        ts: 1773229200.3,
        direction: "client->server",
        json: {
          jsonrpc: "2.0",
          id: 2,
          method: "tools/call",
          params: {
            name: "os_places.by_postcode",
            arguments: { postcode: "SW1A 1AA" },
          },
        },
      },
      {
        ts: 1773229200.4,
        direction: "server->client",
        json: {
          jsonrpc: "2.0",
          id: 2,
          result: {
            data: {
              results: [{ postcode: "SW1A 1AA" }],
            },
          },
        },
      },
    ]),
    "utf8"
  );

  await writeFile(
    path.join(sessionDir, "transcript-visible.jsonl"),
    writeJsonl([
      {
        timestamp: "2026-03-11T09:00:05Z",
        role: "user",
        content: "Check Westminster postcode evidence.",
      },
      {
        timestamp: "2026-03-11T09:00:20Z",
        role: "assistant",
        content: "The postcode is SW1A 1AA.",
        isConclusion: true,
      },
    ]),
    "utf8"
  );

  await writeFile(
    path.join(sessionDir, "decision-log.jsonl"),
    writeJsonl([
      {
        timestamp: "2026-03-11T09:00:12Z",
        kind: "conclusion",
        content: "The answer was grounded in postcode evidence.",
      },
    ]),
    "utf8"
  );

  await writeFile(
    path.join(sessionDir, "source-http-trace.jsonl"),
    writeJsonl([
      {
        timestamp: "2026-03-11T09:00:06Z",
        direction: "request",
        sourceAccessId: "src-1",
        source: "os_places",
        method: "GET",
        url: "https://api.os.uk/search/places/v1/postcode?postcode=SW1A1AA",
        heldStatus: "held",
      },
      {
        timestamp: "2026-03-11T09:00:07Z",
        direction: "response",
        sourceAccessId: "src-1",
        source: "os_places",
        statusCode: 200,
        heldStatus: "held",
      },
    ]),
    "utf8"
  );

  return {
    sessionDir,
    cleanup: async () => {
      await rm(sessionRoot, { recursive: true, force: true });
    },
  };
}
