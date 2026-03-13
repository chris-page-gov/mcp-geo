import { expect, test } from "@playwright/test";

import { buildCsp, createUiPreviewSession, injectCsp, validateUiMessage } from "../src/lib/uiBridge.js";

test("preview session only expects host origin when same-origin is effectively enabled", () => {
  const base = {
    resourceUri: "ui://mcp-geo/route-planner",
    uiAllowSameOrigin: true,
    hostOrigin: "http://127.0.0.1:4173",
    tools: [],
    resources: [],
  };

  const sandboxedSession = createUiPreviewSession({
    ...base,
    uiResourceMeta: { ui: { permissions: {} } },
  });
  expect(sandboxedSession.allowSameOrigin).toBe(false);
  expect(sandboxedSession.expectedOrigin).toBe("null");

  const sameOriginSession = createUiPreviewSession({
    ...base,
    uiResourceMeta: { ui: { permissions: { sameOrigin: true } } },
  });
  expect(sameOriginSession.allowSameOrigin).toBe(true);
  expect(sameOriginSession.expectedOrigin).toBe(base.hostOrigin);
});

test("missing widget CSP metadata does not inject a deny-all preview CSP", () => {
  const html = "<!DOCTYPE html><html><head></head><body><main>Map widget</main></body></html>";
  const serverUrl = "http://127.0.0.1:8000";

  expect(buildCsp({ ui: {} }, serverUrl)).toBe("");
  expect(injectCsp(html, { ui: {} }, serverUrl)).toBe(html);
});

test("refreshing an active preview can preserve the existing bridge session token", () => {
  const initialSession = createUiPreviewSession({
    resourceUri: "ui://mcp-geo/route-planner",
    uiAllowSameOrigin: false,
    uiResourceMeta: { ui: {} },
    hostOrigin: "http://127.0.0.1:4173",
    tools: [{ name: "os_route.get" }],
    resources: [{ uri: "ui://mcp-geo/route-planner" }],
  });

  const refreshedSession = createUiPreviewSession({
    resourceUri: "ui://mcp-geo/route-planner",
    uiAllowSameOrigin: false,
    uiResourceMeta: { ui: {} },
    hostOrigin: "http://127.0.0.1:4173",
    existingPreviewSession: initialSession,
    tools: [{ name: "os_route.get" }, { name: "os_route.descriptor" }],
    resources: [
      { uri: "ui://mcp-geo/route-planner" },
      { uri: "resource://mcp-geo/stakeholder-benchmark-pack" },
    ],
  });

  expect(refreshedSession.id).toBe(initialSession.id);
  expect(refreshedSession.token).toBe(initialSession.token);
  expect(refreshedSession.createdAt).toBe(initialSession.createdAt);
  expect(Array.from(refreshedSession.allowedToolNames)).toContain("os_route.descriptor");
});

test("preview session permits resources/read calls by resource name as well as uri", () => {
  const previewSession = createUiPreviewSession({
    resourceUri: "ui://mcp-geo/route-planner",
    uiAllowSameOrigin: false,
    uiResourceMeta: { ui: {} },
    hostOrigin: "http://127.0.0.1:4173",
    tools: [],
    resources: [
      {
        uri: "resource://mcp-geo/stakeholder-benchmark-pack",
        name: "stakeholder_benchmark_pack",
      },
    ],
  });

  const baseEvent = {
    origin: "null",
  };
  const baseMeta = {
    __mcpGeoHost: {
      sessionToken: previewSession.token,
    },
  };

  expect(
    validateUiMessage({
      event: baseEvent,
      message: {
        jsonrpc: "2.0",
        method: "resources/read",
        params: { uri: "resource://mcp-geo/stakeholder-benchmark-pack" },
        ...baseMeta,
      },
      previewSession,
    })
  ).toEqual({ ok: true });

  expect(
    validateUiMessage({
      event: baseEvent,
      message: {
        jsonrpc: "2.0",
        method: "resources/read",
        params: { name: "stakeholder_benchmark_pack" },
        ...baseMeta,
      },
      previewSession,
    })
  ).toEqual({ ok: true });
});
