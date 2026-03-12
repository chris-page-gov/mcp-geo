export const UI_PROTOCOL_VERSION = "2026-01-26";
export const UI_RESOURCE_MIME = "text/html;profile=mcp-app";

const BRIDGE_ALLOWED_METHODS = new Set([
  "ping",
  "resources/read",
  "tools/call",
  "ui/initialize",
  "ui/message",
  "ui/open-link",
  "ui/request-display-mode",
  "ui/update-model-context",
  "ui/notifications/initialized",
  "ui/notifications/size-changed",
  "notifications/message",
]);

export function sanitizeBridgeName(name) {
  if (typeof name !== "string") {
    return "";
  }
  return name.replace(/[^A-Za-z0-9_-]/g, "_").slice(0, 64);
}

function buildToolAliasSet(tools) {
  const aliases = new Set();
  if (!Array.isArray(tools)) {
    return aliases;
  }
  tools.forEach((entry) => {
    const rawName = typeof entry?.name === "string" ? entry.name.trim() : "";
    const originalName =
      typeof entry?.annotations?.originalName === "string"
        ? entry.annotations.originalName.trim()
        : "";
    const schemaConst =
      typeof entry?.inputSchema?.properties?.tool?.const === "string"
        ? entry.inputSchema.properties.tool.const.trim()
        : typeof entry?.input_schema?.properties?.tool?.const === "string"
          ? entry.input_schema.properties.tool.const.trim()
          : "";
    [rawName, originalName, schemaConst].filter(Boolean).forEach((name) => {
      aliases.add(name);
      const sanitized = sanitizeBridgeName(name);
      if (sanitized) {
        aliases.add(sanitized);
      }
    });
  });
  return aliases;
}

function createSessionToken() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `preview-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function normalizeDomains(domains) {
  if (!Array.isArray(domains)) {
    return [];
  }
  return domains
    .map((domain) => (typeof domain === "string" ? domain.trim() : ""))
    .filter(Boolean);
}

function normalizeCspSource(source) {
  if (source === "self" || source === "'self'") {
    return "'self'";
  }
  return source;
}

export function getServerOrigin(serverUrl) {
  try {
    return new URL(serverUrl).origin;
  } catch (_error) {
    return "";
  }
}

export function buildCsp(meta, serverUrl) {
  const csp = meta?.ui?.csp;
  if (!csp) {
    return "";
  }

  const connectDomains = normalizeDomains(csp.connectDomains).map(normalizeCspSource);
  const resourceDomains = normalizeDomains(csp.resourceDomains).map(normalizeCspSource);
  const frameDomains = normalizeDomains(csp.frameDomains).map(normalizeCspSource);
  const baseUriDomains = normalizeDomains(csp.baseUriDomains).map(normalizeCspSource);
  const workerDomains = normalizeDomains(csp.workerDomains || csp.workerSrc).map(
    normalizeCspSource
  );

  const serverOrigin = getServerOrigin(serverUrl);
  const connectSet = new Set(connectDomains);
  const resourceSet = new Set(resourceDomains);
  if (serverOrigin) {
    connectSet.add(serverOrigin);
    resourceSet.add(serverOrigin);
  }

  const resourceList = Array.from(resourceSet);
  const scriptSources = ["'unsafe-inline'", ...resourceList];
  const styleSources = ["'unsafe-inline'", ...resourceList];
  const imgSources = ["data:", ...resourceList];
  const mediaSources = ["data:", ...resourceList];
  const fontSources = [...resourceList];
  const connectSrc = connectSet.size ? Array.from(connectSet).join(" ") : "'none'";
  const frameSrc = frameDomains.length ? frameDomains.join(" ") : "'none'";
  const baseSrc = baseUriDomains.length
    ? baseUriDomains.join(" ")
    : serverOrigin
      ? `'self' ${serverOrigin}`
      : "'self'";
  const workerSrc = workerDomains.length ? `worker-src ${workerDomains.join(" ")}` : "";

  return [
    "default-src 'none'",
    `script-src 'self' ${scriptSources.join(" ")}`.trim(),
    `style-src 'self' ${styleSources.join(" ")}`.trim(),
    `img-src 'self' ${imgSources.join(" ")}`.trim(),
    `font-src 'self' ${fontSources.join(" ")}`.trim(),
    `media-src 'self' ${mediaSources.join(" ")}`.trim(),
    `connect-src ${connectSrc}`,
    workerSrc,
    `frame-src ${frameSrc}`,
    `base-uri ${baseSrc}`,
    "object-src 'none'",
  ]
    .filter(Boolean)
    .join("; ");
}

export function injectPreviewBase(html, serverUrl) {
  if (!html) {
    return "";
  }
  if (/<base\b[^>]*data-mcp-preview-base=["']1["'][^>]*>/i.test(html)) {
    return html;
  }
  const serverOrigin = getServerOrigin(serverUrl);
  if (!serverOrigin) {
    return html;
  }
  const baseTag = `<base href="${serverOrigin}/ui/" data-mcp-preview-base="1">`;
  if (html.includes("</head>")) {
    return html.replace("</head>", `${baseTag}</head>`);
  }
  const headMatch = html.match(/<head\b[^>]*>/i);
  if (headMatch) {
    return html.replace(headMatch[0], `${headMatch[0]}${baseTag}`);
  }
  return `${baseTag}${html}`;
}

export function injectCsp(html, meta, serverUrl) {
  if (!html) {
    return "";
  }
  if (
    /<meta\b[^>]*(http-equiv\s*=\s*["']content-security-policy["']|content-security-policy)[^>]*>/i.test(
      html
    )
  ) {
    return html;
  }
  const csp = buildCsp(meta, serverUrl);
  if (!csp) {
    return html;
  }
  const metaTag = `<meta http-equiv="Content-Security-Policy" content="${csp}">`;
  if (html.includes("</head>")) {
    return html.replace("</head>", `${metaTag}</head>`);
  }
  const headMatch = html.match(/<head\b[^>]*>/i);
  if (headMatch) {
    return html.replace(headMatch[0], `${headMatch[0]}${metaTag}`);
  }
  return `${metaTag}${html}`;
}

export function wantsSameOrigin(permissions) {
  return Boolean(permissions?.sameOrigin || permissions?.allowSameOrigin);
}

export function allowSameOrigin(permissions, allowSameOriginFlag) {
  return wantsSameOrigin(permissions) && Boolean(allowSameOriginFlag);
}

export function sanitizeSandboxPermissions(permissions, allowSameOriginFlag) {
  if (!permissions || typeof permissions !== "object") {
    return {};
  }
  const next = { ...permissions };
  if (!allowSameOrigin(permissions, allowSameOriginFlag)) {
    delete next.sameOrigin;
    delete next.allowSameOrigin;
  }
  return next;
}

export function buildSandbox(meta, allowSameOriginFlag) {
  const permissions = meta?.ui?.permissions || {};
  const flags = ["allow-scripts"];
  if (allowSameOrigin(permissions, allowSameOriginFlag)) {
    flags.push("allow-same-origin");
  }
  return flags.join(" ");
}

export function buildAllow(meta) {
  const permissions = meta?.ui?.permissions || {};
  const allowList = [];
  if (permissions.camera) {
    allowList.push("camera");
  }
  if (permissions.microphone) {
    allowList.push("microphone");
  }
  if (permissions.geolocation) {
    allowList.push("geolocation");
  }
  if (permissions.clipboardWrite) {
    allowList.push("clipboard-write");
  }
  return allowList.join("; ");
}

export function buildHostContext({
  serverUrl,
  uiPreviewExpanded,
  uiHostViewportMode,
  uiCompactWidthPx,
  uiCompactHeightPx,
}) {
  const proxyBase = getServerOrigin(serverUrl) || "http://localhost:8000";
  const displayMode = uiPreviewExpanded ? "fullscreen" : "inline";
  let containerDimensions;
  if (uiHostViewportMode === "compact") {
    containerDimensions = {
      maxWidth: uiCompactWidthPx,
      maxHeight: uiCompactHeightPx,
      width: uiCompactWidthPx,
      height: uiCompactHeightPx,
    };
  } else if (uiHostViewportMode === "regular") {
    const regularWidth = Math.max(window.innerWidth || 1200, 1024);
    const regularHeight = Math.max(window.innerHeight || 900, 700);
    containerDimensions = {
      maxWidth: regularWidth,
      maxHeight: regularHeight,
      width: regularWidth,
      height: regularHeight,
    };
  } else if (uiPreviewExpanded) {
    containerDimensions = {
      maxWidth: window.innerWidth || 1200,
      maxHeight: window.innerHeight || 900,
      width: window.innerWidth || 1200,
      height: window.innerHeight || 900,
    };
  } else {
    containerDimensions = { maxWidth: 1200, maxHeight: 700, width: 1200, height: 700 };
  }
  return {
    displayMode,
    availableDisplayModes: ["inline", "fullscreen"],
    platform: "web",
    userAgent: "mcp-geo-playground",
    containerDimensions,
    mcpGeo: { proxyBase },
  };
}

export function buildHostCapabilities({ uiResourceMeta, uiAllowSameOrigin }) {
  const permissions = sanitizeSandboxPermissions(
    uiResourceMeta?.ui?.permissions || {},
    uiAllowSameOrigin
  );
  const csp = uiResourceMeta?.ui?.csp || {};
  const sandbox = {};
  if (Object.keys(permissions).length) {
    sandbox.permissions = permissions;
  }
  if (Object.keys(csp).length) {
    sandbox.csp = csp;
  }
  const capabilities = {
    serverTools: {},
    serverResources: {},
    logging: {},
    openLinks: {},
  };
  if (Object.keys(sandbox).length) {
    capabilities.sandbox = sandbox;
  }
  return capabilities;
}

export function createUiPreviewSession({
  resourceUri,
  uiAllowSameOrigin,
  uiResourceMeta,
  hostOrigin,
  tools = [],
  resources = [],
}) {
  const token = createSessionToken();
  const sameOrigin = allowSameOrigin(uiResourceMeta?.ui?.permissions || {}, uiAllowSameOrigin);
  return {
    id: `preview-${token}`,
    token,
    resourceUri: resourceUri || "",
    createdAt: new Date().toISOString(),
    allowSameOrigin: sameOrigin,
    expectedOrigin: sameOrigin ? hostOrigin : "null",
    allowedToolNames: buildToolAliasSet(tools),
    allowedResourceUris: Array.from(
      new Set([...resources.map((entry) => entry?.uri).filter(Boolean), resourceUri].filter(Boolean))
    ),
  };
}

export function buildBridgeEnvelope(previewSession, payload) {
  if (!previewSession) {
    return payload;
  }
  return {
    ...payload,
    __mcpGeoHost: {
      previewId: previewSession.id,
      sessionToken: previewSession.token,
      resourceUri: previewSession.resourceUri,
    },
  };
}

export function normalizeBridgeMessage(message) {
  if (!message || typeof message !== "object") {
    return null;
  }
  if (message.jsonrpc !== "2.0") {
    return null;
  }
  return message;
}

export function validateUiMessage({ event, message, previewSession }) {
  if (!previewSession) {
    return { ok: false, reason: "No active preview session", code: "NO_PREVIEW" };
  }
  if (!message || typeof message !== "object" || message.jsonrpc !== "2.0") {
    return { ok: false, reason: "Invalid JSON-RPC payload", code: "INVALID_PAYLOAD" };
  }
  if (event.origin !== previewSession.expectedOrigin) {
    return {
      ok: false,
      reason: `Unexpected widget origin: ${event.origin || "unknown"}`,
      code: "ORIGIN_MISMATCH",
    };
  }
  const method = message.method;
  if (!method) {
    return { ok: true };
  }
  if (!BRIDGE_ALLOWED_METHODS.has(method)) {
    return { ok: false, reason: `Blocked method: ${method}`, code: "METHOD_BLOCKED" };
  }
  if (method === "ui/initialize") {
    return { ok: true };
  }
  const bridgeMeta = message.__mcpGeoHost;
  const sessionToken = bridgeMeta?.sessionToken;
  if (sessionToken !== previewSession.token) {
    return {
      ok: false,
      reason: "Missing or invalid widget session token",
      code: "TOKEN_INVALID",
    };
  }
  if (method === "tools/call") {
    const toolName = message.params?.name || message.params?.tool;
    if (!previewSession.allowedToolNames.has(toolName)) {
      return {
        ok: false,
        reason: `Widget requested unknown tool: ${toolName || "unknown"}`,
        code: "TOOL_NOT_ALLOWED",
      };
    }
  }
  if (method === "resources/read") {
    const uri = message.params?.uri || message.params?.name;
    if (!previewSession.allowedResourceUris.includes(uri)) {
      return {
        ok: false,
        reason: `Widget requested unknown resource: ${uri || "unknown"}`,
        code: "RESOURCE_NOT_ALLOWED",
      };
    }
  }
  if (method === "ui/open-link") {
    const url = message.params?.url || message.params?.href;
    try {
      const parsed = new URL(url);
      if (!["http:", "https:"].includes(parsed.protocol)) {
        return { ok: false, reason: "Only http(s) links are allowed", code: "LINK_BLOCKED" };
      }
    } catch (_error) {
      return { ok: false, reason: "Invalid link URL", code: "LINK_INVALID" };
    }
  }
  return { ok: true };
}
