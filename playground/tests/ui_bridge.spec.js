import { expect, test } from "@playwright/test";

import { buildCsp, createUiPreviewSession, injectCsp } from "../src/lib/uiBridge.js";

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
