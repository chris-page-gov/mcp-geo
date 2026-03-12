import { expect, test } from "@playwright/test";

import { createUiPreviewSession } from "../src/lib/uiBridge.js";

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
