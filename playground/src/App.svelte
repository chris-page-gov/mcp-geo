<script>
  import {
    CompatibilityCallToolResultSchema,
    ListResourcesResultSchema,
    ListResourceTemplatesResultSchema,
    ListToolsResultSchema,
  } from "@modelcontextprotocol/sdk/types.js";
  import { onMount } from "svelte";
  import { z } from "zod";
  import packageInfo from "../package.json";
  import AuditWorkbench from "./components/AuditWorkbench.svelte";
  import BenchmarkWorkbench from "./components/BenchmarkWorkbench.svelte";
  import DebugWorkbench from "./components/DebugWorkbench.svelte";
  import ExplorerWorkbench from "./components/ExplorerWorkbench.svelte";
  import RoutingWorkbench from "./components/RoutingWorkbench.svelte";
  import {
    buildSecretAudit,
    DEBUG_LOG_LIMIT,
    formatTracePayload,
    redactErrorMessage,
    redactStringSecrets,
    redactValue,
    scrubSecretsValue,
  } from "./lib/debug.js";
  import {
    buildAllow,
    buildBridgeEnvelope,
    buildHostCapabilities,
    buildHostContext,
    buildSandbox,
    createUiPreviewSession,
    getServerOrigin,
    injectCsp,
    injectPreviewBase,
    normalizeBridgeMessage,
    sanitizeBridgeName,
    UI_PROTOCOL_VERSION,
    UI_RESOURCE_MIME,
    validateUiMessage,
    wantsSameOrigin,
  } from "./lib/uiBridge.js";
  import {
    createPlaygroundSession,
    fetchAuditBlob,
    fetchAuditJson,
    recordPlaygroundEvent,
    recordPlaygroundToolCall,
  } from "./lib/playgroundApi.js";

  const AnySchema = z.object({}).passthrough();

  const defaultOrigin =
    typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "http://localhost:5173";

  const PLAYGROUND_CLIENT_INFO = {
    name: "mcp-geo-playground",
    version: packageInfo?.version || "0.1.0",
  };
  const MCP_SDK_VERSION =
    packageInfo?.dependencies?.["@modelcontextprotocol/sdk"] || "unknown";
  const BUILD_INFO = {
    mode: import.meta?.env?.MODE || "unknown",
    dev: Boolean(import.meta?.env?.DEV),
    prod: Boolean(import.meta?.env?.PROD),
  };
  const UI_BOOT_AT = new Date().toISOString();
  const COMPACT_WIDTH_MIN = 280;
  const COMPACT_WIDTH_MAX = 520;
  const COMPACT_HEIGHT_MIN = 360;
  const COMPACT_HEIGHT_MAX = 900;

  const TAB_HELP = {
    explorer: {
      title: "Explorer",
      text: "Connect to the MCP server, inspect tools/resources/prompts, and host MCP App widgets safely.",
    },
    routing: {
      title: "Routing",
      text: "Guided route-planner demonstrations for SG03 and SG12 with graph readiness and widget preview.",
    },
    audit: {
      title: "Audit / FOI",
      text: "Use the DSAP audit endpoints directly for normalise, pack build, verify, redact, and legal-hold workflows.",
    },
    benchmarks: {
      title: "Benchmarks",
      text: "Browse all 20 stakeholder scenarios with reference, live, and blocked-evidence views.",
    },
    debug: {
      title: "Debug",
      text: "Inspect host state, audit REST activity, redacted logs, and rejected widget-bridge events.",
    },
  };

  const uiToolMap = [
    {
      match: "boundary-explorer",
      tool: "os_apps.render_boundary_explorer",
      args: { tool: "os_apps.render_boundary_explorer" },
    },
    {
      match: "feature-inspector",
      tool: "os_apps.render_feature_inspector",
      args: { tool: "os_apps.render_feature_inspector" },
    },
    {
      match: "geography-selector",
      tool: "os_apps.render_geography_selector",
      args: {
        tool: "os_apps.render_geography_selector",
        searchTerm: "Coventry",
        level: "LSOA",
      },
    },
    {
      match: "route-planner",
      tool: "os_apps.render_route_planner",
      args: { tool: "os_apps.render_route_planner" },
    },
    {
      match: "statistics-dashboard",
      tool: "os_apps.render_statistics_dashboard",
      args: { tool: "os_apps.render_statistics_dashboard" },
    },
  ];

  let serverUrl = `${defaultOrigin}/mcp`;
  let playgroundUrl = `${defaultOrigin}/playground`;
  let status = "disconnected";
  let error = "";
  let session = null;
  let capabilities = null;
  let tools = [];
  let resources = [];
  let resourceTemplates = [];
  let prompts = [];
  let promptsError = "";
  let toolFilter = "";
  let resourceFilter = "";
  let promptFilter = "";
  let toolName = "os_mcp_descriptor";
  let toolArgs = '{\n  "tool": "os_mcp.descriptor"\n}';
  let toolResult = "";
  let promptText = "";
  let promptContext = "";
  let descriptorRaw = null;
  let descriptorMeta = null;
  let history = [];
  let activeTab = "explorer";
  let selectedTool = null;
  let selectedResource = null;
  let selectedPrompt = null;

  let uiPreviewResource = null;
  let uiPreviewSource = "explorer";
  let uiToolResult = "";
  let uiResourceText = "";
  let uiResourceMime = "";
  let uiResourceMeta = null;
  let uiResourceError = "";
  let uiPreviewExpanded = false;
  let uiHostViewportMode = "auto";
  let uiCompactWidth = 320;
  let uiCompactHeight = 500;
  let uiCompactWidthPx = 320;
  let uiCompactHeightPx = 500;
  let uiPreviewInlineStyle = "";
  let uiIframe = null;
  let uiPreviewReady = false;
  let uiInstructionsVisible = false;
  let uiInstructionsTimer = null;
  let uiResourceHtml = "";
  let uiIframeSandbox = "allow-scripts";
  let uiIframeAllow = "";
  let uiAllowSameOrigin = false;
  let uiAppInitialized = false;
  let uiPreviewSession = null;
  let pendingUiConfig = null;

  let debugEnabled = false;
  let debugEntries = [];
  let traceRedact = true;
  let lastRequestAt = "";
  let lastResponseAt = "";
  let lastErrorAt = "";
  let lastErrorMessage = "";
  let lastErrorDetail = null;
  let debugSnapshotText = "";
  let hmrUpdateCount = 0;
  let hmrLastUpdate = "";
  let hmrStatus = "disabled";
  let rejectedBridgeEvents = [];
  let auditRestLog = [];

  let auditPacks = [];
  let auditSelectedPack = null;
  let auditResult = null;
  let auditError = "";
  let auditForm = {
    sessionDir: "",
    outputRoot: "",
    scopeType: "conversation",
    episodeId: "",
    episodeTitle: "",
    episodeStartSequence: "",
    episodeEndSequence: "",
    retentionClass: "default_operational",
    legalHold: false,
  };

  let benchmarkPack = null;
  let benchmarkScenarios = [];
  let benchmarkLiveRun = null;
  let benchmarkFilterId = "";
  let benchmarkFilterSupport = "all";
  let benchmarkFilterToolFamily = "all";
  let selectedBenchmarkId = "";

  let routeScenarioId = "SG03";
  let routeDescriptorState = null;
  let routingResult = null;

  function normalizeDimension(value, fallback, min, max) {
    const asNumber = Number(value);
    if (!Number.isFinite(asNumber)) {
      return fallback;
    }
    return Math.min(max, Math.max(min, Math.round(asNumber)));
  }

  function recordHistory(entry) {
    history = [scrubSecretsValue(entry), ...history].slice(0, 60);
  }

  function logDebug(message, detail = null, level = "info") {
    const entry = {
      at: new Date().toISOString(),
      level,
      message: redactStringSecrets(message),
      detail: detail ? redactValue(detail) : null,
    };
    debugEntries = [entry, ...debugEntries].slice(0, DEBUG_LOG_LIMIT);
    if (debugEnabled && typeof console !== "undefined") {
      const payload = entry.detail ? entry.detail : "";
      if (level === "error") {
        console.error("[playground]", entry.message, payload);
      } else if (level === "warn") {
        console.warn("[playground]", entry.message, payload);
      } else {
        console.debug("[playground]", entry.message, payload);
      }
    }
  }

  function setLastError(message, detail = null) {
    lastErrorAt = new Date().toISOString();
    lastErrorMessage = redactErrorMessage(message);
    lastErrorDetail = redactValue(detail ?? { error: message });
  }

  function clearUiInstructionsTimer() {
    if (uiInstructionsTimer) {
      clearTimeout(uiInstructionsTimer);
      uiInstructionsTimer = null;
    }
  }

  function scheduleUiInstructions() {
    clearUiInstructionsTimer();
    uiInstructionsTimer = setTimeout(() => {
      if (!uiPreviewReady && uiResourceText) {
        uiInstructionsVisible = true;
      }
    }, 2000);
  }

  function resetUiPreviewState({ keepResource = true, keepPendingConfig = false } = {}) {
    clearUiInstructionsTimer();
    uiToolResult = "";
    uiResourceText = "";
    uiResourceMime = "";
    uiResourceMeta = null;
    uiResourceError = "";
    uiResourceHtml = "";
    uiPreviewReady = false;
    uiInstructionsVisible = false;
    uiAppInitialized = false;
    if (!keepPendingConfig) {
      pendingUiConfig = null;
    }
    uiPreviewSession = keepResource && uiPreviewResource
      ? createUiPreviewSession({
          resourceUri: uiPreviewResource.uri,
          uiAllowSameOrigin,
          uiResourceMeta: uiPreviewResource._meta || null,
          hostOrigin: window.location.origin,
          existingPreviewSession:
            uiPreviewSession?.resourceUri === uiPreviewResource.uri ? uiPreviewSession : null,
          tools,
          resources,
        })
      : null;
  }

  function clearUiPreview() {
    uiPreviewResource = null;
    resetUiPreviewState({ keepResource: false });
  }

  function setUiPreviewResource(resource, source = "explorer") {
    uiPreviewSource = source;
    uiPreviewResource = resource;
    resetUiPreviewState({ keepResource: Boolean(resource) });
  }

  function rejectBridgeEvent(reason, code, detail) {
    const entry = {
      at: new Date().toISOString(),
      code,
      reason,
      detail: redactValue(detail),
    };
    rejectedBridgeEvents = [entry, ...rejectedBridgeEvents].slice(0, 40);
    logDebug("Widget bridge event rejected", entry, "warn");
  }

  function extractToolPayload(result) {
    if (!result || typeof result !== "object") {
      return result;
    }
    if (result.data && typeof result.data === "object") {
      return result.data;
    }
    if (result.structuredContent && typeof result.structuredContent === "object") {
      return result.structuredContent;
    }
    if (Array.isArray(result.content)) {
      for (const block of result.content) {
        if (!block || typeof block !== "object") {
          continue;
        }
        if (block.type === "json" && block.json && typeof block.json === "object") {
          return block.json;
        }
        if (block.type === "text" && typeof block.text === "string") {
          const text = block.text.trim();
          if (text.startsWith("{") || text.startsWith("[")) {
            try {
              const parsed = JSON.parse(text);
              if (parsed && typeof parsed === "object") {
                return parsed;
              }
            } catch (_error) {
              // Ignore invalid JSON text blocks.
            }
          }
        }
      }
    }
    return result;
  }

  async function sendRequest(request, schema = AnySchema) {
    if (!session) {
      throw new Error("MCP client not connected");
    }
    lastRequestAt = new Date().toISOString();
    logDebug("MCP request", { method: request?.method, params: request?.params });
    try {
      const response = await session.request(request, schema);
      lastResponseAt = new Date().toISOString();
      recordHistory({ request, response, at: new Date().toISOString() });
      logDebug(
        "MCP response",
        {
          method: request?.method,
          ok: response?.ok,
          isError: response?.isError,
        },
        response?.isError ? "warn" : "info"
      );
      return response;
    } catch (err) {
      const message = redactErrorMessage(err?.message || String(err));
      setLastError(message, err);
      logDebug("MCP request failed", { method: request?.method, error: message }, "error");
      throw err;
    }
  }

  async function sendRequestSafe(request, schema = AnySchema) {
    try {
      return await sendRequest(request, schema);
    } catch (_error) {
      return null;
    }
  }

  function buildTemplateFromSchema(schema) {
    if (!schema || schema.type !== "object") {
      return {};
    }
    const properties = schema.properties || {};
    const required = new Set(schema.required || []);
    const payload = {};

    Object.entries(properties).forEach(([key, definition]) => {
      if (key === "tool" && definition && definition.const) {
        payload[key] = definition.const;
        return;
      }
      if (!required.has(key) && key !== "tool") {
        return;
      }
      if (definition && definition.const !== undefined) {
        payload[key] = definition.const;
        return;
      }
      if (definition && Array.isArray(definition.enum) && definition.enum.length > 0) {
        payload[key] = definition.enum[0];
        return;
      }
      switch (definition?.type) {
        case "string":
          payload[key] = "";
          break;
        case "number":
        case "integer":
          payload[key] = 0;
          break;
        case "boolean":
          payload[key] = false;
          break;
        case "array":
          payload[key] = [];
          break;
        case "object":
          payload[key] = {};
          break;
        default:
          payload[key] = null;
      }
    });

    return payload;
  }

  async function fetchDescriptor() {
    if (!session) {
      return;
    }
    try {
      const response = await sendRequest(
        {
          method: "tools/call",
          params: { name: "os_mcp_descriptor", arguments: { tool: "os_mcp.descriptor" } },
        },
        CompatibilityCallToolResultSchema
      );
      descriptorRaw = response;
      descriptorMeta = extractToolPayload(response) ?? null;
      logDebug("Descriptor fetched", {
        server: descriptorMeta?.server,
        version: descriptorMeta?.version,
      });
    } catch (err) {
      error = redactErrorMessage(err?.message || String(err));
    }
  }

  async function refreshLists() {
    if (!session) {
      return;
    }
    try {
      const toolsResponse = await sendRequest(
        { method: "tools/list", params: {} },
        ListToolsResultSchema
      );
      tools = toolsResponse.tools || [];
      const resourcesResponse = await sendRequest(
        { method: "resources/list", params: {} },
        ListResourcesResultSchema
      );
      resources = resourcesResponse.resources || [];
      const templatesResponse = await sendRequest(
        { method: "resources/templates/list", params: {} },
        ListResourceTemplatesResultSchema
      );
      resourceTemplates = templatesResponse.resourceTemplates || [];
      const promptResponse = await sendRequestSafe(
        { method: "prompts/list", params: {} },
        AnySchema
      );
      if (promptResponse && Array.isArray(promptResponse.prompts)) {
        prompts = promptResponse.prompts;
        promptsError = "";
      } else if (promptResponse) {
        prompts = [];
        promptsError = "Prompts response missing 'prompts'";
      } else {
        prompts = [];
        promptsError = "Prompts not supported";
      }
      if (selectedTool) {
        selectedTool = tools.find((entry) => entry.name === selectedTool.name) || selectedTool;
      }
      if (selectedResource) {
        selectedResource =
          resources.find((entry) => entry.uri === selectedResource.uri) || selectedResource;
      }
      if (uiPreviewResource) {
        uiPreviewResource =
          resources.find((entry) => entry.uri === uiPreviewResource.uri) || uiPreviewResource;
        uiPreviewSession = createUiPreviewSession({
          resourceUri: uiPreviewResource?.uri,
          uiAllowSameOrigin,
          uiResourceMeta: uiResourceMeta || uiPreviewResource?._meta || null,
          hostOrigin: window.location.origin,
          existingPreviewSession: uiPreviewSession,
          tools,
          resources,
        });
      }
      logDebug("Refreshed tools/resources/prompts", {
        tools: tools.length,
        resources: resources.length,
        templates: resourceTemplates.length,
        prompts: prompts.length,
      });
    } catch (err) {
      error = redactErrorMessage(err?.message || String(err));
      setLastError(error, err);
    }
  }

  async function fetchResourceJson(uri) {
    const response = await sendRequest({ method: "resources/read", params: { uri } }, AnySchema);
    const contents = response?.contents || response?.content || [];
    const first = contents[0] || {};
    if (first.json && typeof first.json === "object") {
      return first.json;
    }
    if (typeof first.text === "string") {
      return JSON.parse(first.text);
    }
    return first;
  }

  async function loadBenchmarks() {
    if (!session) {
      return;
    }
    try {
      benchmarkPack = await fetchResourceJson("resource://mcp-geo/stakeholder-benchmark-pack");
      benchmarkScenarios = Array.isArray(benchmarkPack?.scenarios) ? benchmarkPack.scenarios : [];
      benchmarkLiveRun = await fetchResourceJson(
        "resource://mcp-geo/stakeholder-benchmark-live-run-latest"
      );
      if (!selectedBenchmarkId && benchmarkScenarios.length) {
        selectedBenchmarkId = benchmarkScenarios[0].id;
      }
      if (!routeScenarioId && benchmarkScenarios.length) {
        routeScenarioId = "SG03";
      }
      logDebug("Benchmark resources loaded", {
        scenarios: benchmarkScenarios.length,
        liveResults: benchmarkLiveRun?.results?.length || 0,
      });
    } catch (err) {
      logDebug(
        "Failed to load benchmark resources",
        { error: err?.message || String(err) },
        "warn"
      );
    }
  }

  async function connect() {
    error = "";
    if (status === "connected" && session) {
      return;
    }
    status = "connecting";
    try {
      session = await createPlaygroundSession({
        serverUrl,
        clientInfo: PLAYGROUND_CLIENT_INFO,
        uiResourceMime: UI_RESOURCE_MIME,
      });
      status = "connected";
      capabilities = session.getServerCapabilities?.() ?? null;
      await refreshLists();
      await fetchDescriptor();
      await loadBenchmarks();
      await refreshAuditPacks();
      activeTab = "explorer";
      logDebug("Connected to MCP server", { serverUrl });
    } catch (err) {
      status = "error";
      error = redactErrorMessage(err?.message || String(err));
      session = null;
      setLastError(error, err);
      logDebug("Failed to connect", { serverUrl, error }, "error");
    }
  }

  async function disconnect() {
    if (session) {
      await session.close();
    }
    session = null;
    status = "disconnected";
    capabilities = null;
    tools = [];
    resources = [];
    resourceTemplates = [];
    prompts = [];
    descriptorRaw = null;
    descriptorMeta = null;
    clearUiPreview();
    logDebug("Disconnected from MCP server");
  }

  function selectTool(tool) {
    selectedTool = tool;
    selectedResource = null;
    selectedPrompt = null;
    toolName = tool.name;
    toolArgs = JSON.stringify(buildTemplateFromSchema(tool.inputSchema || tool.input_schema), null, 2);
    toolResult = "";
    activeTab = "explorer";
  }

  function selectResource(resource) {
    selectedResource = resource;
    selectedTool = null;
    selectedPrompt = null;
    if (resource?.uri?.startsWith("ui://")) {
      setUiPreviewResource(resource, "explorer");
    }
    activeTab = "explorer";
  }

  function selectPrompt(prompt) {
    selectedPrompt = prompt;
    selectedTool = null;
    selectedResource = null;
    activeTab = "explorer";
  }

  async function callTool() {
    let parsedArgs = {};
    try {
      parsedArgs = toolArgs ? JSON.parse(toolArgs) : {};
    } catch (err) {
      error = redactErrorMessage(err?.message || String(err));
      setLastError(error, err);
      return;
    }
    try {
      const response = await sendRequest(
        {
          method: "tools/call",
          params: { name: toolName, arguments: parsedArgs },
        },
        CompatibilityCallToolResultSchema
      );
      toolResult = JSON.stringify(response, null, 2);
      await recordPlaygroundToolCall(playgroundUrl, {
        tool: toolName,
        input: parsedArgs,
        output: response,
      });
    } catch (err) {
      error = redactErrorMessage(err?.message || String(err));
      setLastError(error, err);
    }
  }

  async function logPrompt() {
    if (!promptText.trim()) {
      return;
    }
    try {
      await recordPlaygroundEvent(playgroundUrl, {
        eventType: "prompt",
        payload: { text: promptText, context: promptContext },
      });
      promptText = "";
      promptContext = "";
      logDebug("Prompt logged", { playgroundUrl });
    } catch (err) {
      error = redactErrorMessage(err?.message || String(err));
      setLastError(error, err);
    }
  }

  async function copyText(value) {
    if (!value) {
      return;
    }
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
    }
  }

  function toggleUiPreview() {
    uiPreviewExpanded = !uiPreviewExpanded;
    notifyHostContextChange();
  }

  function queueUiConfig(config) {
    pendingUiConfig = config ? scrubSecretsValue(normalizeUiConfig(config, uiPreviewResource?.uri)) : null;
  }

  function normalizeRouteMode(mode) {
    if (typeof mode !== "string") {
      return null;
    }
    const normalized = mode.trim().toLowerCase();
    if (!normalized) {
      return null;
    }
    if (normalized === "emergency") {
      return "emergency";
    }
    if (normalized === "drive" || normalized === "driving") {
      return "drive";
    }
    if (normalized === "walk" || normalized === "walking") {
      return "walk";
    }
    if (normalized === "cycle" || normalized === "cycling" || normalized === "bike") {
      return "cycle";
    }
    return normalized;
  }

  function normalizeRouteStop(stop) {
    if (!stop) {
      return null;
    }
    if (typeof stop === "string") {
      const trimmed = stop.trim();
      return trimmed ? { query: trimmed } : null;
    }
    if (typeof stop !== "object") {
      return null;
    }
    if (typeof stop.query === "string" && stop.query.trim()) {
      return { query: stop.query.trim() };
    }
    if (typeof stop.uprn === "string" && stop.uprn.trim()) {
      return { uprn: stop.uprn.trim() };
    }
    if (Array.isArray(stop.coordinates) && stop.coordinates.length === 2) {
      return { coordinates: stop.coordinates };
    }
    return null;
  }

  function normalizeRouteWidgetConfig(config) {
    if (!config || typeof config !== "object") {
      return {};
    }
    const next = { ...config };
    if (!Array.isArray(next.stops) || next.stops.length < 2) {
      const originStop = normalizeRouteStop(next.origin);
      const destinationStop = normalizeRouteStop(next.destination);
      const viaStops = Array.isArray(next.via)
        ? next.via.map(normalizeRouteStop).filter(Boolean)
        : [];
      if (originStop && destinationStop) {
        next.stops = [originStop, ...viaStops, destinationStop];
      }
    }
    if (typeof next.profile !== "string" || !next.profile.trim()) {
      const routeMode = normalizeRouteMode(next.routeMode);
      if (routeMode) {
        next.profile = routeMode;
      }
    } else {
      next.profile = normalizeRouteMode(next.profile) || next.profile;
    }
    return next;
  }

  function normalizeUiConfig(config, resourceUri) {
    if (!config || typeof config !== "object") {
      return config;
    }
    if (resourceUri && resourceUri.includes("route-planner")) {
      return normalizeRouteWidgetConfig(config);
    }
    return config;
  }

  async function runSuggestedUiTool() {
    if (!uiGuidance?.tool) {
      return;
    }
    try {
      queueUiConfig(normalizeUiConfig(uiGuidance.args || {}, uiPreviewResource?.uri || selectedResource?.uri));
      if (uiAppInitialized) {
        sendUiNotification("ui/notifications/tool-input", {
          arguments: pendingUiConfig || {},
          config: pendingUiConfig || {},
        });
      }
      const response = await sendRequest(
        {
          method: "tools/call",
          params: { name: uiGuidance.tool, arguments: uiGuidance.args || {} },
        },
        CompatibilityCallToolResultSchema
      );
      uiToolResult = JSON.stringify(response, null, 2);
      if (uiAppInitialized) {
        sendUiNotification("ui/notifications/tool-result", response);
      }
    } catch (err) {
      uiToolResult = "";
      uiResourceError = redactErrorMessage(err?.message || String(err));
      setLastError(uiResourceError, err);
    }
  }

  async function loadUiResource(
    resource = uiPreviewResource || selectedResource,
    { source = uiPreviewSource, keepPendingConfig = false } = {}
  ) {
    if (!resource?.uri) {
      return;
    }
    uiPreviewSource = source;
    uiPreviewResource = resource;
    resetUiPreviewState({ keepResource: true, keepPendingConfig });
    try {
      const response = await sendRequest(
        { method: "resources/read", params: { uri: resource.uri } },
        AnySchema
      );
      const contents = response?.contents || response?.content || [];
      const first = contents[0] || {};
      uiResourceText = first.text || "";
      uiResourceMime = first.mimeType || first.mime_type || "";
      uiResourceMeta = first._meta || resource._meta || null;
      uiPreviewSession = createUiPreviewSession({
        resourceUri: resource.uri,
        uiAllowSameOrigin,
        uiResourceMeta: first._meta || resource._meta || null,
        hostOrigin: window.location.origin,
        tools,
        resources,
      });
      if (!uiResourceText) {
        uiResourceError = "No HTML payload returned for this UI resource.";
      } else {
        scheduleUiInstructions();
      }
      logDebug("UI resource loaded", { uri: resource.uri, mime: uiResourceMime });
    } catch (err) {
      uiResourceError = redactErrorMessage(err?.message || String(err));
      setLastError(uiResourceError, err);
    }
  }

  function postToUi(payload) {
    if (!uiIframe?.contentWindow) {
      return;
    }
    uiIframe.contentWindow.postMessage(buildBridgeEnvelope(uiPreviewSession, payload), "*");
  }

  function sendUiNotification(method, params) {
    postToUi({ jsonrpc: "2.0", method, params });
  }

  function respondToUi(id, result, errorPayload) {
    if (errorPayload) {
      postToUi({ jsonrpc: "2.0", id, error: errorPayload });
    } else {
      postToUi({ jsonrpc: "2.0", id, result });
    }
  }

  async function handleUiRequest(message) {
    const { id, method, params } = message;
    if (method === "ui/initialize") {
      const hostContext = buildHostContext({
        serverUrl,
        uiPreviewExpanded,
        uiHostViewportMode,
        uiCompactWidthPx,
        uiCompactHeightPx,
      });
      const previewMeta = {
        previewId: uiPreviewSession?.id,
        resourceUri: uiPreviewSession?.resourceUri,
        sessionToken: uiPreviewSession?.token,
      };
      respondToUi(id, {
        protocolVersion: UI_PROTOCOL_VERSION,
        hostInfo: PLAYGROUND_CLIENT_INFO,
        hostCapabilities: buildHostCapabilities({ uiResourceMeta, uiAllowSameOrigin }),
        hostContext: { ...hostContext, mcpGeoPreview: previewMeta },
        mcpGeoPreview: previewMeta,
      });
      return;
    }

    if (message.id === undefined || message.id === null) {
      return;
    }

    if (method === "ui/request-display-mode") {
      uiPreviewExpanded = params?.mode === "fullscreen";
      respondToUi(id, { mode: uiPreviewExpanded ? "fullscreen" : "inline" });
      notifyHostContextChange();
      return;
    }

    if (method === "ui/open-link") {
      const url = params?.url || params?.href;
      if (url) {
        window.open(url, "_blank", "noopener,noreferrer");
      }
      respondToUi(id, {});
      return;
    }

    if (method === "ui/message" || method === "ui/update-model-context") {
      recordHistory({ request: message, response: {}, at: new Date().toISOString() });
      respondToUi(id, {});
      return;
    }

    if (method === "tools/call") {
      try {
        const response = await sendRequest(
          { method: "tools/call", params },
          CompatibilityCallToolResultSchema
        );
        respondToUi(id, response);
        if (debugEnabled) {
          logDebug("UI tools/call bridged", { tool: params?.name || params?.tool });
        }
      } catch (err) {
        respondToUi(id, null, { code: -32000, message: err?.message || String(err) });
      }
      return;
    }

    if (method === "resources/read") {
      try {
        const response = await sendRequest({ method: "resources/read", params }, AnySchema);
        respondToUi(id, response);
      } catch (err) {
        respondToUi(id, null, { code: -32000, message: err?.message || String(err) });
      }
      return;
    }

    if (method === "ping") {
      respondToUi(id, {});
      return;
    }

    respondToUi(id, null, { code: -32601, message: `Method not found: ${method}` });
  }

  function notifyHostContextChange() {
    if (!uiAppInitialized) {
      return;
    }
    sendUiNotification(
      "ui/notifications/host-context-changed",
      buildHostContext({
        serverUrl,
        uiPreviewExpanded,
        uiHostViewportMode,
        uiCompactWidthPx,
        uiCompactHeightPx,
      })
    );
  }

  async function prefillToolFromScenario(scenario) {
    if (!scenario?.demo?.primaryTool) {
      return;
    }
    const requestedName = scenario.demo.primaryTool;
    const tool = tools.find((entry) => {
      const names = new Set(
        [
          entry?.name,
          entry?.annotations?.originalName,
          entry?.inputSchema?.properties?.tool?.const,
          entry?.input_schema?.properties?.tool?.const,
        ]
          .filter((value) => typeof value === "string" && value.trim())
          .flatMap((value) => [value, sanitizeBridgeName(value)])
      );
      return names.has(requestedName);
    });
    if (tool) {
      selectTool(tool);
    } else {
      selectedTool = null;
      toolName = requestedName;
    }
    toolArgs = JSON.stringify(
      scenario.demo.presetArgs || { tool: scenario.demo.primaryTool },
      null,
      2
    );
    activeTab = "explorer";
  }

  async function openScenarioWidget(scenario, { switchTab = true } = {}) {
    const widgetUri = scenario?.demo?.widget;
    if (!widgetUri) {
      return;
    }
    const resource = resources.find((entry) => entry.uri === widgetUri);
    if (!resource) {
      uiResourceError = `Widget resource not listed: ${widgetUri}`;
      return;
    }
    queueUiConfig(normalizeUiConfig(scenario.demo.widgetArgs || scenario.demo.presetArgs || {}, widgetUri));
    selectedResource = resource;
    const source = widgetUri.includes("route-planner") ? "routing" : "benchmark";
    if (switchTab) {
      activeTab = widgetUri.includes("route-planner") ? "routing" : "explorer";
    }
    await loadUiResource(resource, { source, keepPendingConfig: true });
  }

  async function runRouteDemo() {
    const scenario = routeScenarios.find((entry) => entry.id === routeScenarioId);
    if (!scenario) {
      return;
    }
    routeDescriptorState = null;
    routingResult = null;
    if (scenario.demo?.widget) {
      await openScenarioWidget(scenario, { switchTab: false });
    }
    try {
      const descriptor = await sendRequest(
        {
          method: "tools/call",
          params: { name: "os_route.descriptor", arguments: { tool: "os_route.descriptor" } },
        },
        CompatibilityCallToolResultSchema
      );
      routeDescriptorState = extractToolPayload(descriptor);
    } catch (err) {
      routeDescriptorState = { isError: true, message: err?.message || String(err) };
    }
    try {
      const result = await sendRequest(
        {
          method: "tools/call",
          params: {
            name: scenario.demo.primaryTool,
            arguments: scenario.demo.presetArgs || {},
          },
        },
        CompatibilityCallToolResultSchema
      );
      routingResult = extractToolPayload(result);
      uiToolResult = JSON.stringify(result, null, 2);
    } catch (err) {
      routingResult = { isError: true, message: err?.message || String(err) };
    }
  }

  async function auditJsonRequest(method, path, payload = null) {
    try {
      const result = await fetchAuditJson(path, {
        method,
        body: payload ? JSON.stringify(payload) : undefined,
      });
      auditRestLog = [
        {
          at: new Date().toISOString(),
          method,
          path,
          status: "ok",
          payload: scrubSecretsValue(result),
        },
        ...auditRestLog,
      ].slice(0, 40);
      return result;
    } catch (err) {
      auditRestLog = [
        {
          at: new Date().toISOString(),
          method,
          path,
          status: "error",
          payload: scrubSecretsValue({
            request: payload,
            error: err?.message || String(err),
          }),
        },
        ...auditRestLog,
      ].slice(0, 40);
      throw err;
    }
  }

  async function refreshAuditPacks() {
    try {
      const result = await auditJsonRequest("GET", "/audit/packs?limit=50");
      auditPacks = result.packs || [];
      if (!auditSelectedPack && auditPacks.length) {
        await selectAuditPack(auditPacks[0].packId);
      }
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  async function selectAuditPack(packId) {
    try {
      auditSelectedPack = await auditJsonRequest("GET", `/audit/packs/${packId}`);
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  async function normaliseAuditSession() {
    auditError = "";
    try {
      auditResult = await auditJsonRequest("POST", "/audit/normalise", {
        sessionDir: auditForm.sessionDir,
      });
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  async function createAuditPack() {
    auditError = "";
    const payload = {
      sessionDir: auditForm.sessionDir,
      outputRoot: auditForm.outputRoot || undefined,
      scopeType: auditForm.scopeType,
      episodeId: auditForm.episodeId || undefined,
      episodeTitle: auditForm.episodeTitle || undefined,
      episodeStartSequence: auditForm.episodeStartSequence
        ? Number(auditForm.episodeStartSequence)
        : undefined,
      episodeEndSequence: auditForm.episodeEndSequence
        ? Number(auditForm.episodeEndSequence)
        : undefined,
      retentionClass: auditForm.retentionClass,
      legalHold: Boolean(auditForm.legalHold),
    };
    try {
      auditResult = await auditJsonRequest("POST", "/audit/packs", payload);
      await refreshAuditPacks();
      if (auditResult?.packId) {
        await selectAuditPack(auditResult.packId);
      }
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  async function verifyAuditPack() {
    if (!auditSelectedPack?.packId) {
      return;
    }
    try {
      auditResult = await auditJsonRequest(
        "POST",
        `/audit/packs/${auditSelectedPack.packId}/verify`
      );
      await selectAuditPack(auditSelectedPack.packId);
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  async function redactAuditPack(disclosureProfile = "foi_redacted") {
    if (!auditSelectedPack?.packId) {
      return;
    }
    try {
      auditResult = await auditJsonRequest(
        "POST",
        `/audit/packs/${auditSelectedPack.packId}/redact`,
        { disclosureProfile }
      );
      await selectAuditPack(auditSelectedPack.packId);
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  async function toggleAuditLegalHold() {
    if (!auditSelectedPack?.packId) {
      return;
    }
    try {
      auditResult = await auditJsonRequest(
        "POST",
        `/audit/packs/${auditSelectedPack.packId}/legal-hold`,
        {
          legalHold: !auditSelectedPack.legalHold,
          retentionClass: auditSelectedPack.retentionClass,
          reason: auditSelectedPack.legalHold ? "Released from playground" : "Applied from playground",
        }
      );
      await selectAuditPack(auditSelectedPack.packId);
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  function downloadBlob(filename, blob) {
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(href);
  }

  async function downloadAuditBundle() {
    if (!auditSelectedPack?.packId) {
      return;
    }
    try {
      const blob = await fetchAuditBlob(`/audit/packs/${auditSelectedPack.packId}/bundle`);
      downloadBlob(`DSAP-${auditSelectedPack.packId}.zip`, blob);
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  async function downloadAuditHash() {
    if (!auditSelectedPack?.packId) {
      return;
    }
    try {
      const payload = await auditJsonRequest(
        "GET",
        `/audit/packs/${auditSelectedPack.packId}/bundle/hash`
      );
      downloadBlob(
        `DSAP-${auditSelectedPack.packId}.zip.sha256.json`,
        new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" })
      );
    } catch (err) {
      auditError = redactErrorMessage(err?.message || String(err));
    }
  }

  function scenarioToolFamily(scenario) {
    const toolsForScenario = scenario?.mcpGeoTools || [];
    if (toolsForScenario.some((name) => name.startsWith("os_route") || name.includes(".route"))) {
      return "routing";
    }
    if (toolsForScenario.some((name) => name.startsWith("os_apps"))) {
      return "apps";
    }
    if (toolsForScenario.some((name) => name.startsWith("os_places"))) {
      return "places";
    }
    if (toolsForScenario.some((name) => name.startsWith("os_features"))) {
      return "features";
    }
    if (toolsForScenario.some((name) => name.startsWith("admin_"))) {
      return "admin";
    }
    return "other";
  }

  function selectBenchmarkScenario(id) {
    selectedBenchmarkId = id;
    if (id === "SG03" || id === "SG12") {
      routeScenarioId = id;
    }
  }

  function viewLatestEvidence() {
    if (selectedBenchmark?.demo?.widget) {
      openScenarioWidget(selectedBenchmark);
    }
  }

  function dismissUiInstructions() {
    uiInstructionsVisible = false;
  }

  function handleSameOriginToggle() {
    uiAllowSameOrigin = !uiAllowSameOrigin;
    if (uiPreviewResource) {
      void loadUiResource(uiPreviewResource);
    }
  }

  function handleViewportModeChange() {
    notifyHostContextChange();
  }

  function handleCompactWidthInput() {
    notifyHostContextChange();
  }

  function handleCompactHeightInput() {
    notifyHostContextChange();
  }

  if (import.meta?.hot) {
    hmrStatus = "listening";
    import.meta.hot.on("vite:afterUpdate", (payload) => {
      hmrUpdateCount += 1;
      hmrLastUpdate = new Date().toISOString();
      logDebug("HMR update applied", { updates: payload?.updates?.length || 0 });
    });
    import.meta.hot.on("vite:beforeFullReload", () => {
      hmrUpdateCount += 1;
      hmrLastUpdate = new Date().toISOString();
      logDebug("HMR full reload triggered", null, "warn");
    });
  }

  onMount(() => {
    const handler = async (event) => {
      if (!uiIframe?.contentWindow || event.source !== uiIframe.contentWindow) {
        return;
      }
      const message = normalizeBridgeMessage(event.data);
      if (!message) {
        return;
      }
      const validation = validateUiMessage({
        event,
        message,
        previewSession: uiPreviewSession,
      });
      if (!validation.ok) {
        rejectBridgeEvent(validation.reason, validation.code, message);
        return;
      }

      if (message.method && message.id === undefined) {
        if (message.method === "ui/notifications/initialized") {
          uiAppInitialized = true;
          uiPreviewReady = true;
          uiInstructionsVisible = false;
          clearUiInstructionsTimer();
          recordHistory({ request: message, response: null, at: new Date().toISOString() });
          if (pendingUiConfig) {
            sendUiNotification("ui/notifications/tool-input", {
              arguments: pendingUiConfig,
              config: pendingUiConfig,
            });
          }
          return;
        }
        if (message.method === "ui/notifications/size-changed") {
          const height = message.params?.height;
          if (uiIframe && typeof height === "number" && height > 0) {
            uiIframe.style.height = `${height}px`;
          }
          return;
        }
        if (message.method === "notifications/message") {
          recordHistory({ request: message, response: null, at: new Date().toISOString() });
          return;
        }
      }

      if (message.method) {
        await handleUiRequest(message);
      }
    };

    window.addEventListener("message", handler);
    requestAnimationFrame(() => {
      window.dispatchEvent(new CustomEvent("mcp-playground-ready"));
    });
    return () => {
      clearUiInstructionsTimer();
      window.removeEventListener("message", handler);
    };
  });

  $: if (typeof document !== "undefined") {
    document.body.style.overflow = uiPreviewExpanded ? "hidden" : "";
  }

  $: uiCompactWidthPx = normalizeDimension(
    uiCompactWidth,
    320,
    COMPACT_WIDTH_MIN,
    COMPACT_WIDTH_MAX
  );
  $: uiCompactHeightPx = normalizeDimension(
    uiCompactHeight,
    500,
    COMPACT_HEIGHT_MIN,
    COMPACT_HEIGHT_MAX
  );
  $: uiPreviewInlineStyle =
    uiHostViewportMode === "compact"
      ? `--preview-inline-width:${uiCompactWidthPx}px; --preview-inline-height:${uiCompactHeightPx}px;`
      : "";
  $: uiResourceHtml = uiResourceText
    ? injectPreviewBase(injectCsp(uiResourceText, uiResourceMeta, serverUrl), serverUrl)
    : "";
  $: uiIframeSandbox = buildSandbox(uiResourceMeta, uiAllowSameOrigin);
  $: uiIframeAllow = buildAllow(uiResourceMeta);
  $: uiSameOriginRequested = wantsSameOrigin(uiResourceMeta?.ui?.permissions || {});

  $: descriptorJson = descriptorRaw ? JSON.stringify(descriptorRaw, null, 2) : "";
  $: descriptorSizeBytes = descriptorRaw
    ? new TextEncoder().encode(JSON.stringify(descriptorRaw)).length
    : 0;
  $: descriptorSizeLabel = descriptorSizeBytes ? `${(descriptorSizeBytes / 1024).toFixed(1)} KB` : "0 KB";
  $: descriptorWarn = descriptorSizeBytes > 50 * 1024;
  $: serverVersion = descriptorMeta?.version || "n/a";
  $: coreProtocolVersion = descriptorMeta?.protocolVersion || "n/a";
  $: supportedProtocolVersions = Array.isArray(descriptorMeta?.supportedProtocolVersions)
    ? descriptorMeta.supportedProtocolVersions.join(", ")
    : "n/a";
  $: mcpAppsProtocolVersion = descriptorMeta?.mcpAppsProtocolVersion || "n/a";
  $: filteredTools = tools.filter((tool) =>
    tool.name.toLowerCase().includes(toolFilter.toLowerCase())
  );
  $: filteredResources = resources.filter((resource) =>
    resource.name.toLowerCase().includes(resourceFilter.toLowerCase())
  );
  $: filteredPrompts = prompts.filter((prompt) =>
    (prompt.name || "").toLowerCase().includes(promptFilter.toLowerCase())
  );
  $: toolsTotal = descriptorMeta?.toolSearch?.counts?.total || tools.length;
  $: toolsLoaded =
    descriptorMeta?.toolSearch?.counts?.always_loaded || Math.min(tools.length, toolsTotal);
  $: uiGuidance = (() => {
    if (!selectedResource?.uri?.startsWith("ui://")) {
      return null;
    }
    return uiToolMap.find((entry) => selectedResource.uri.includes(entry.match)) || null;
  })();
  $: uiExampleCall = uiGuidance
    ? JSON.stringify({ name: uiGuidance.tool, arguments: uiGuidance.args }, null, 2)
    : "";
  $: currentHelp = TAB_HELP[activeTab] || TAB_HELP.explorer;
  $: selectedBenchmark =
    benchmarkScenarios.find((scenario) => scenario.id === selectedBenchmarkId) || null;
  $: benchmarkReferenceView = selectedBenchmark?.referenceOutput || null;
  $: benchmarkLiveView =
    benchmarkLiveRun?.results?.find((entry) => entry.scenarioId === selectedBenchmark?.id) || null;
  $: filteredBenchmarks = benchmarkScenarios.filter((scenario) => {
    const idMatch = !benchmarkFilterId
      || scenario.id.toLowerCase().includes(benchmarkFilterId.toLowerCase())
      || scenario.title.toLowerCase().includes(benchmarkFilterId.toLowerCase());
    const supportMatch =
      benchmarkFilterSupport === "all" || scenario.supportLevel === benchmarkFilterSupport;
    const familyMatch =
      benchmarkFilterToolFamily === "all"
      || scenarioToolFamily(scenario) === benchmarkFilterToolFamily;
    return idMatch && supportMatch && familyMatch;
  });
  $: routeScenarios = benchmarkScenarios.filter((scenario) => ["SG03", "SG12"].includes(scenario.id));
  $: if (!routeScenarios.find((entry) => entry.id === routeScenarioId) && routeScenarios.length) {
    routeScenarioId = routeScenarios[0].id;
  }
  $: debugSnapshotText = JSON.stringify(
    redactValue({
      status,
      serverUrl,
      playgroundUrl,
      capabilities,
      selectedTool: selectedTool?.name,
      selectedResource: selectedResource?.uri,
      selectedPrompt: selectedPrompt?.name,
      selectedBenchmark: selectedBenchmark?.id,
      lastRequestAt,
      lastResponseAt,
      lastErrorAt,
      ui: {
        previewResource: uiPreviewResource?.uri,
        previewReady: uiPreviewReady,
        sandbox: uiIframeSandbox,
        sessionId: uiPreviewSession?.id,
      },
      audit: {
        selectedPack: auditSelectedPack?.packId,
        packs: auditPacks.length,
      },
      hmr: {
        status: hmrStatus,
        updates: hmrUpdateCount,
        lastUpdate: hmrLastUpdate,
      },
      build: BUILD_INFO,
    }),
    null,
    2
  );
  $: secretAudit = buildSecretAudit({
    debugEntries,
    history,
    lastErrorMessage,
    lastErrorDetail,
    error,
    uiResourceError,
    auditRestLog,
    rejectedBridgeEvents,
  });
</script>

<svelte:head>
  <style>
    @import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Spectral:wght@400;600&display=swap");
  </style>
</svelte:head>

<div class="page">
  <header class="hero">
    <div>
      <p class="eyebrow">MCP Geo Playground</p>
      <h1>Playground security hardening and demo workbench</h1>
      <p class="sub">
        Explore MCP tools, route workflows, DSAP audit packs, and benchmark evidence from one
        host shell.
      </p>
    </div>
    <div class="status-card">
      <span class={`dot ${status}`}></span>
      <div>
        <div class="label">Status</div>
        <div class="value">{status}</div>
      </div>
    </div>
  </header>

  <div class="tabs-toolbar">
    <nav class="tabs">
      <button class:active={activeTab === "explorer"} on:click={() => (activeTab = "explorer")}>
        Explorer
      </button>
      <button class:active={activeTab === "routing"} on:click={() => (activeTab = "routing")}>
        Routing
      </button>
      <button class:active={activeTab === "audit"} on:click={() => (activeTab = "audit")}>
        Audit / FOI
      </button>
      <button class:active={activeTab === "benchmarks"} on:click={() => (activeTab = "benchmarks")}>
        Benchmarks
      </button>
      <button class:active={activeTab === "debug"} on:click={() => (activeTab = "debug")}>
        Debug
      </button>
    </nav>
    <div class="tab-help" data-testid="tab-help">
      <strong>{currentHelp.title}</strong>
      <span>{currentHelp.text}</span>
    </div>
  </div>

  {#if activeTab === "explorer"}
    <ExplorerWorkbench
      bind:playgroundUrl
      bind:promptContext
      bind:promptFilter
      bind:promptText
      bind:resourceFilter
      bind:serverUrl
      bind:toolArgs
      bind:toolFilter
      bind:traceRedact
      bind:uiAllowSameOrigin
      bind:uiCompactHeight
      bind:uiCompactWidth
      bind:uiHostViewportMode
      bind:uiIframe
      {BUILD_INFO}
      {capabilities}
      connect={connect}
      {COMPACT_HEIGHT_MAX}
      {COMPACT_HEIGHT_MIN}
      {COMPACT_WIDTH_MAX}
      {COMPACT_WIDTH_MIN}
      copyText={copyText}
      {coreProtocolVersion}
      {descriptorJson}
      {descriptorMeta}
      {descriptorSizeLabel}
      {descriptorWarn}
      disconnect={disconnect}
      {error}
      fetchDescriptor={fetchDescriptor}
      {filteredPrompts}
      {filteredResources}
      {filteredTools}
      formatTracePayload={(payload) => formatTracePayload(payload, traceRedact)}
      {history}
      loadUiResource={() => loadUiResource(selectedResource)}
      logPrompt={logPrompt}
      {MCP_SDK_VERSION}
      {mcpAppsProtocolVersion}
      onCompactHeightInput={handleCompactHeightInput}
      onCompactWidthInput={handleCompactWidthInput}
      onDismissUiInstructions={dismissUiInstructions}
      onPlaygroundUrlInput={() => {}}
      onServerUrlInput={() => {}}
      onToggleSameOrigin={handleSameOriginToggle}
      onViewportModeChange={handleViewportModeChange}
      {PLAYGROUND_CLIENT_INFO}
      {prompts}
      {promptsError}
      refreshLists={refreshLists}
      runSuggestedUiTool={runSuggestedUiTool}
      {selectedPrompt}
      {selectedResource}
      {selectedTool}
      selectPrompt={selectPrompt}
      selectResource={selectResource}
      selectTool={selectTool}
      {serverVersion}
      {status}
      {supportedProtocolVersions}
      toggleUiPreview={toggleUiPreview}
      {toolResult}
      callTool={callTool}
      {tools}
      {toolsLoaded}
      {toolsTotal}
      {uiExampleCall}
      {uiGuidance}
      {uiIframeAllow}
      {uiIframeSandbox}
      {uiInstructionsVisible}
      {uiPreviewExpanded}
      {uiPreviewInlineStyle}
      {uiPreviewReady}
      {uiResourceError}
      {uiResourceHtml}
      {uiResourceMime}
      {uiResourceText}
      {uiSameOriginRequested}
      {uiToolResult}
      {uiCompactHeightPx}
      {uiCompactWidthPx}
      {resourceTemplates}
    />
  {/if}

  {#if activeTab === "routing"}
    <RoutingWorkbench
      bind:routeScenarioId
      bind:uiCompactHeight
      bind:uiCompactWidth
      bind:uiHostViewportMode
      bind:uiIframe
      compactHeightMax={COMPACT_HEIGHT_MAX}
      compactHeightMin={COMPACT_HEIGHT_MIN}
      compactWidthMax={COMPACT_WIDTH_MAX}
      compactWidthMin={COMPACT_WIDTH_MIN}
      descriptorState={routeDescriptorState}
      onCompactHeightInput={handleCompactHeightInput}
      onCompactWidthInput={handleCompactWidthInput}
      onDismissUiInstructions={dismissUiInstructions}
      onLoadPreview={() => openScenarioWidget(routeScenarios.find((entry) => entry.id === routeScenarioId), { switchTab: false })}
      onOpenWidget={() => openScenarioWidget(routeScenarios.find((entry) => entry.id === routeScenarioId), { switchTab: false })}
      onPrefillTool={() => prefillToolFromScenario(routeScenarios.find((entry) => entry.id === routeScenarioId))}
      onRunDemo={runRouteDemo}
      onSelectScenario={(id) => (routeScenarioId = id)}
      onTogglePreview={toggleUiPreview}
      onViewportModeChange={handleViewportModeChange}
      {routingResult}
      {routeScenarios}
      {status}
      {uiCompactHeightPx}
      {uiCompactWidthPx}
      {uiIframeAllow}
      {uiIframeSandbox}
      {uiInstructionsVisible}
      {uiPreviewExpanded}
      {uiPreviewInlineStyle}
      {uiPreviewReady}
      {uiResourceError}
      {uiResourceHtml}
      {uiResourceMime}
      {uiResourceText}
    />
  {/if}

  {#if activeTab === "audit"}
    <AuditWorkbench
      {auditError}
      {auditForm}
      {auditPacks}
      {auditResult}
      {auditSelectedPack}
      onCreatePack={createAuditPack}
      onDownloadBundle={downloadAuditBundle}
      onDownloadHash={downloadAuditHash}
      onNormaliseSession={normaliseAuditSession}
      onRedactPack={redactAuditPack}
      onRefreshPacks={refreshAuditPacks}
      onSelectPack={selectAuditPack}
      onToggleLegalHold={toggleAuditLegalHold}
      onVerifyPack={verifyAuditPack}
      {status}
    />
  {/if}

  {#if activeTab === "benchmarks"}
    <BenchmarkWorkbench
      bind:benchmarkFilterId
      bind:benchmarkFilterSupport
      bind:benchmarkFilterToolFamily
      {benchmarkLiveView}
      {benchmarkReferenceView}
      {filteredBenchmarks}
      onOpenWidget={() => openScenarioWidget(selectedBenchmark)}
      onPrefillTool={() => prefillToolFromScenario(selectedBenchmark)}
      onSelectScenario={selectBenchmarkScenario}
      onViewLatestEvidence={viewLatestEvidence}
      {selectedBenchmark}
      {status}
    />
  {/if}

  {#if activeTab === "debug"}
    <DebugWorkbench
      {auditRestLog}
      bootedAt={UI_BOOT_AT}
      {BUILD_INFO}
      clearDebugLog={() => (debugEntries = [])}
      clearHistory={() => (history = [])}
      bind:debugEnabled
      {debugEntries}
      {debugSnapshotText}
      {hmrLastUpdate}
      {hmrStatus}
      {hmrUpdateCount}
      {lastErrorAt}
      {lastErrorDetail}
      {lastErrorMessage}
      {lastRequestAt}
      {lastResponseAt}
      {rejectedBridgeEvents}
      {secretAudit}
      selectedResourceUri={uiPreviewResource?.uri || selectedResource?.uri || ""}
      {uiIframeSandbox}
      {uiPreviewReady}
      {uiResourceError}
      {uiResourceText}
    />
  {/if}
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: "Space Grotesk", sans-serif;
    background: radial-gradient(circle at top, #f9f5ef 0%, #efe5d7 45%, #e1d4c5 100%);
    color: #1c1c1c;
  }

  .page {
    padding: 28px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .hero {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
    background: #0b1f21;
    color: #f7f4ef;
    padding: 16px 20px;
    border-radius: 20px;
    box-shadow: 0 12px 30px rgba(11, 31, 33, 0.2);
  }

  .hero h1 {
    margin: 4px 0;
    font-size: 1.4rem;
    line-height: 1.25;
  }

  .eyebrow {
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #7fdac9;
  }

  .sub {
    margin: 0;
    font-family: "Spectral", serif;
    max-width: 640px;
    font-size: 0.94rem;
  }

  .status-card {
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(255, 255, 255, 0.12);
    padding: 12px 16px;
    border-radius: 12px;
  }

  .dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #9aa5a6;
  }

  .dot.connected {
    background: #5ad19a;
  }

  .dot.connecting {
    background: #f4c95d;
  }

  .dot.error {
    background: #ef6b6b;
  }

  .tabs-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .tabs {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
  }

  .tabs button {
    border: 1px solid #0b1f21;
    background: transparent;
    padding: 8px 16px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
  }

  .tabs button.active {
    background: #0b1f21;
    color: #f7f4ef;
  }

  .tab-help {
    display: inline-flex;
    align-items: baseline;
    gap: 8px;
    background: #fffaf2;
    border: 1px solid #d7d0c5;
    border-radius: 999px;
    padding: 8px 12px;
    font-size: 0.82rem;
    color: #4b3b2d;
    max-width: min(860px, 70vw);
  }

  .tab-help strong {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.68rem;
    color: #2e7d6b;
  }

  :global(.grid) {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }

  :global(.split) {
    display: grid;
    grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
    gap: 20px;
  }

  :global(.card),
  :global(.pane) {
    background: #fdfbf7;
    border-radius: 16px;
    box-shadow: 0 8px 20px rgba(15, 42, 45, 0.08);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  :global(.card) {
    padding: 20px;
    gap: 12px;
  }

  :global(.pane-header) {
    background: #f2e9dd;
    padding: 12px 16px;
    border-bottom: 1px solid #e0d3c5;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  :global(.pane-header.alt) {
    background: #efe3d4;
  }

  :global(.pane-title) {
    font-weight: 700;
  }

  :global(.pane-body) {
    padding: 16px;
    overflow: auto;
    max-height: 70vh;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  :global(label) {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.85rem;
    color: #34424a;
  }

  :global(input),
  :global(textarea),
  :global(select) {
    border: 1px solid #d7d0c5;
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.9rem;
    background: #fffaf2;
    font-family: inherit;
  }

  :global(textarea) {
    min-height: 96px;
  }

  :global(button) {
    border: none;
    padding: 10px 16px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
  }

  :global(button.primary) {
    background: #2e7d6b;
    color: #fff;
  }

  :global(button.ghost) {
    background: transparent;
    border: 1px solid #2e7d6b;
    color: #2e7d6b;
  }

  :global(button:disabled) {
    opacity: 0.6;
    cursor: not-allowed;
  }

  :global(.actions) {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  :global(.label) {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #5a4a3a;
  }

  :global(.value) {
    font-size: 1rem;
    font-weight: 600;
  }

  :global(.value.warn) {
    color: #b46a1f;
  }

  :global(.muted) {
    color: #7a7a7a;
    font-size: 0.85rem;
  }

  :global(.error) {
    background: #fce4e4;
    color: #9a1f1f;
    padding: 10px 12px;
    border-radius: 10px;
  }

  :global(.badge) {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    background: #0b1f21;
    color: #f7f4ef;
    padding: 2px 8px;
    border-radius: 999px;
  }

  :global(.badge-ok) {
    background: #1f7a4f;
  }

  :global(.badge-warn) {
    background: #b84b4b;
  }

  :global(.badge-ghost) {
    background: transparent;
    color: #0b1f21;
    border: 1px solid #0b1f21;
  }

  :global(.list-item) {
    text-align: left;
    border: 1px solid #e0d3c5;
    border-radius: 12px;
    padding: 12px;
    background: #fffaf2;
  }

  :global(.list-item.selected) {
    border-color: #2e7d6b;
    background: #e6f3ee;
  }

  :global(.list-title) {
    font-weight: 600;
  }

  :global(.list-sub) {
    color: #567;
    font-size: 0.85rem;
    margin-top: 4px;
  }

  :global(.list-badges) {
    display: flex;
    gap: 6px;
    margin-top: 8px;
    flex-wrap: wrap;
  }

  :global(.meta-grid) {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 10px;
    margin: 12px 0;
  }

  :global(.details-block) {
    margin-top: 12px;
    background: #fffaf2;
    border-radius: 10px;
    padding: 10px;
  }

  :global(.details-block summary) {
    cursor: pointer;
    font-weight: 600;
  }

  :global(pre) {
    background: #0d1a1c;
    color: #e0efe8;
    padding: 12px;
    border-radius: 12px;
    overflow: auto;
    font-size: 0.75rem;
  }

  :global(.history) {
    display: flex;
    flex-direction: column;
    gap: 8px;
    border: 1px solid #e2d8cc;
    padding: 10px;
    border-radius: 12px;
    background: #fff;
  }

  :global(.info-card) {
    background: #fffaf2;
    border: 1px solid #e0d3c5;
    border-radius: 12px;
    padding: 12px;
    margin: 12px 0;
  }

  :global(.toggle) {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: #34424a;
  }

  :global(.preview-frame) {
    border: 1px solid #e2d8cc;
    border-radius: 12px;
    overflow: hidden;
    background: #fff;
    width: 100%;
    max-width: 100%;
    position: relative;
  }

  :global(.preview-frame.compact-inline) {
    max-width: var(--preview-inline-width, 320px);
  }

  :global(.preview-toolbar) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: #efe3d4;
    border-bottom: 1px solid #e2d8cc;
    font-weight: 600;
  }

  :global(.icon-button) {
    background: transparent;
    border: 1px solid #2e7d6b;
    color: #2e7d6b;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 600;
  }

  :global(.preview-overlay) {
    position: absolute;
    inset: 50px;
    z-index: 6;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  :global(.overlay-card) {
    background: rgba(255, 250, 242, 0.98);
    border: 1px solid #e2d8cc;
    border-radius: 16px;
    padding: 20px;
    max-width: 420px;
    box-shadow: 0 16px 30px rgba(0, 0, 0, 0.15);
  }

  :global(.preview-content) {
    display: block;
  }

  :global(.preview-frame iframe) {
    width: 100%;
    height: var(--preview-inline-height, 360px);
    border: none;
  }

  :global(.preview-frame.expanded) {
    position: fixed;
    inset: 20px;
    z-index: 50;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  }

  :global(.preview-frame.expanded iframe) {
    height: calc(100vh - 96px);
  }

  :global(.preview-frame.expanded.compact-inline .preview-content) {
    display: grid;
    grid-template-columns: minmax(280px, var(--preview-inline-width, 320px)) minmax(0, 1fr);
    height: calc(100vh - 96px);
  }

  :global(.compact-preview-info) {
    border-left: 1px solid #e2d8cc;
    padding: 14px;
    background: #fffaf2;
    overflow: auto;
  }

  :global(.preview-controls) {
    margin-top: 10px;
    padding: 10px;
    border: 1px dashed #d2c4b4;
    border-radius: 10px;
    background: #fffaf2;
  }

  :global(.preview-control-grid) {
    display: grid;
    gap: 8px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  @media (max-width: 960px) {
    .tabs-toolbar {
      flex-direction: column;
      align-items: stretch;
    }

    .tab-help {
      max-width: 100%;
    }

    :global(.split) {
      grid-template-columns: 1fr;
    }

    :global(.pane-body) {
      max-height: none;
    }
  }
</style>
