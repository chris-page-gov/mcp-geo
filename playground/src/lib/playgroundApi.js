import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";

function getMockApi() {
  if (typeof window === "undefined") {
    return null;
  }
  return window.__MCP_PLAYGROUND_MOCK__ || null;
}

export async function createPlaygroundSession({
  serverUrl,
  clientInfo,
  uiResourceMime,
}) {
  const mock = getMockApi();
  if (mock) {
    const capabilityPayload = await mock.connect?.({
      serverUrl,
      clientInfo,
      capabilities: {
        tools: {},
        resources: {},
        prompts: {},
        extensions: {
          "io.modelcontextprotocol/ui": { mimeTypes: [uiResourceMime] },
        },
      },
    });
    return {
      request(request) {
        return mock.request(request);
      },
      async close() {
        await mock.close?.();
      },
      getServerCapabilities() {
        return capabilityPayload?.capabilities ?? capabilityPayload ?? null;
      },
    };
  }

  const client = new Client(clientInfo, {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {},
      extensions: {
        "io.modelcontextprotocol/ui": { mimeTypes: [uiResourceMime] },
      },
    },
  });
  const transport = new StreamableHTTPClientTransport(new URL(serverUrl), {});
  await client.connect(transport);
  return {
    request(request, schema) {
      return client.request(request, schema);
    },
    close() {
      return client.close();
    },
    getServerCapabilities() {
      return client.getServerCapabilities?.() ?? null;
    },
  };
}

async function readJsonResponse(response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  return response.json();
}

export async function recordPlaygroundToolCall(playgroundUrl, payload) {
  await fetch(`${playgroundUrl}/tool_call`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function recordPlaygroundEvent(playgroundUrl, payload) {
  await fetch(`${playgroundUrl}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchAuditJson(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  return readJsonResponse(response);
}

export async function fetchAuditBlob(path) {
  const response = await fetch(path);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  return response.blob();
}
