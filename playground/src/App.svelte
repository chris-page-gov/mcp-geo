<script>
  import { Client } from "@modelcontextprotocol/sdk/client/index.js";
  import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
  import {
    CompatibilityCallToolResultSchema,
    ListResourcesResultSchema,
    ListResourceTemplatesResultSchema,
    ListToolsResultSchema
  } from "@modelcontextprotocol/sdk/types.js";
  import { onMount } from "svelte";
  import { z } from "zod";

  const AnySchema = z.object({}).passthrough();

  let serverUrl = "http://localhost:8000/mcp";
  let playgroundUrl = "http://localhost:8000/playground";
  let status = "disconnected";
  let error = "";
  let client = null;
  let transport = null;
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
  let activeTab = "setup";
  let testSection = "tools";
  let selectedTool = null;
  let selectedResource = null;
  let selectedPrompt = null;
  let capabilities = null;
  let uiToolResult = "";
  let uiResourceText = "";
  let uiResourceMime = "";
  let uiResourceMeta = null;
  let uiResourceError = "";
  let uiPreviewExpanded = false;
  let uiIframe = null;
  let uiPreviewReady = false;
  let uiInstructionsVisible = false;
  let uiResourceHtml = "";
  let uiIframeSandbox = "allow-scripts";
  let uiIframeAllow = "";
  let uiAppInitialized = false;

  const UI_PROTOCOL_VERSION = "2026-01-26";
  const UI_RESOURCE_MIME = "text/html;profile=mcp-app";

  const uiToolMap = [
    {
      match: "geography-selector",
      tool: "os_apps.render_geography_selector",
      args: {
        tool: "os_apps.render_geography_selector",
        searchTerm: "Coventry",
        level: "LSOA"
      }
    },
    {
      match: "statistics-dashboard",
      tool: "os_apps.render_statistics_dashboard",
      args: { tool: "os_apps.render_statistics_dashboard" }
    },
    {
      match: "feature-inspector",
      tool: "os_apps.render_feature_inspector",
      args: { tool: "os_apps.render_feature_inspector" }
    },
    {
      match: "route-planner",
      tool: "os_apps.render_route_planner",
      args: { tool: "os_apps.render_route_planner" }
    }
  ];

  const recordHistory = (entry) => {
    history = [entry, ...history].slice(0, 50);
  };

  const normalizeDomains = (domains) => {
    if (!Array.isArray(domains)) {
      return [];
    }
    return domains
      .map((domain) => (typeof domain === "string" ? domain.trim() : ""))
      .filter(Boolean);
  };

  const normalizeCspSource = (source) => {
    if (source === "self" || source === "'self'") {
      return "'self'";
    }
    return source;
  };

  const buildCsp = (meta) => {
    const csp = meta?.ui?.csp;
    if (!csp) {
      return [
        "default-src 'none'",
        "script-src 'self' 'unsafe-inline'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "media-src 'self' data:",
        "connect-src 'none'",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-src 'none'"
      ].join("; ");
    }
    const connectDomains = normalizeDomains(csp.connectDomains).map(normalizeCspSource);
    const resourceDomains = normalizeDomains(csp.resourceDomains).map(normalizeCspSource);
    const frameDomains = normalizeDomains(csp.frameDomains).map(normalizeCspSource);
    const baseUriDomains = normalizeDomains(csp.baseUriDomains).map(normalizeCspSource);

    const scriptSources = ["'unsafe-inline'", ...resourceDomains];
    const styleSources = ["'unsafe-inline'", ...resourceDomains];
    const imgSources = ["data:", ...resourceDomains];
    const mediaSources = ["data:", ...resourceDomains];
    const fontSources = [...resourceDomains];

    const connectSrc = connectDomains.length ? connectDomains.join(" ") : "'none'";
    const frameSrc = frameDomains.length ? frameDomains.join(" ") : "'none'";
    const baseSrc = baseUriDomains.length ? baseUriDomains.join(" ") : "'self'";

    return [
      "default-src 'none'",
      `script-src 'self' ${scriptSources.join(" ")}`.trim(),
      `style-src 'self' ${styleSources.join(" ")}`.trim(),
      `img-src 'self' ${imgSources.join(" ")}`.trim(),
      `font-src 'self' ${fontSources.join(" ")}`.trim(),
      `media-src 'self' ${mediaSources.join(" ")}`.trim(),
      `connect-src ${connectSrc}`,
      `frame-src ${frameSrc}`,
      `base-uri ${baseSrc}`,
      "object-src 'none'"
    ].join("; ");
  };

  const injectCsp = (html, meta) => {
    if (!html) {
      return "";
    }
    if (html.includes("Content-Security-Policy")) {
      return html;
    }
    const csp = buildCsp(meta);
    if (!csp) {
      return html;
    }
    const metaTag = `<meta http-equiv="Content-Security-Policy" content="${csp}">`;
    if (html.includes("</head>")) {
      return html.replace("</head>", `${metaTag}</head>`);
    }
    if (html.includes("<head")) {
      return html.replace("<head>", `<head>${metaTag}`);
    }
    return `${metaTag}${html}`;
  };

  const buildSandbox = () => "allow-scripts";

  const buildAllow = (meta) => {
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
  };

  const sendRequest = async (request, schema) => {
    if (!client) {
      throw new Error("MCP client not connected");
    }
    const response = await client.request(request, schema);
    recordHistory({ request, response, at: new Date().toISOString() });
    return response;
  };

  const sendRequestSafe = async (request, schema) => {
    try {
      return await sendRequest(request, schema);
    } catch (err) {
      return null;
    }
  };

  const connect = async () => {
    error = "";
    status = "connecting";
    try {
      client = new Client(
        { name: "mcp-geo-playground", version: "0.1.0" },
        {
          capabilities: {
            tools: {},
            resources: {},
            prompts: {},
            extensions: {
              "io.modelcontextprotocol/ui": { mimeTypes: [UI_RESOURCE_MIME] }
            }
          }
        }
      );
      transport = new StreamableHTTPClientTransport(new URL(serverUrl), {});
      await client.connect(transport);
      status = "connected";
      capabilities = client.getServerCapabilities?.() ?? null;
      await refreshLists();
      await fetchDescriptor();
      activeTab = "setup";
    } catch (err) {
      status = "error";
      error = err?.message || String(err);
      client = null;
      transport = null;
    }
  };

  const disconnect = async () => {
    if (client) {
      await client.close();
    }
    status = "disconnected";
    client = null;
    transport = null;
  };

  const refreshLists = async () => {
    if (!client) {
      return;
    }
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
  };

  const fetchDescriptor = async () => {
    if (!client) {
      return;
    }
    const response = await sendRequest(
      {
        method: "tools/call",
        params: { name: "os_mcp_descriptor", arguments: { tool: "os_mcp.descriptor" } }
      },
      CompatibilityCallToolResultSchema
    );
    descriptorRaw = response;
    descriptorMeta = response?.data ?? null;
  };

  const buildTemplateFromSchema = (schema) => {
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
  };

  const selectTool = (tool) => {
    selectedTool = tool;
    selectedResource = null;
    selectedPrompt = null;
    toolName = tool.name;
    const template = buildTemplateFromSchema(tool.inputSchema || tool.input_schema);
    toolArgs = JSON.stringify(template, null, 2);
    toolResult = "";
  };

  const selectResource = (resource) => {
    selectedResource = resource;
    selectedTool = null;
    selectedPrompt = null;
    uiToolResult = "";
    uiResourceText = "";
    uiResourceMime = "";
    uiResourceMeta = null;
    uiResourceError = "";
    uiPreviewExpanded = false;
    uiPreviewReady = false;
    uiInstructionsVisible = false;
    uiAppInitialized = false;
  };

  const selectPrompt = (prompt) => {
    selectedPrompt = prompt;
    selectedTool = null;
    selectedResource = null;
  };

  const callTool = async () => {
    error = "";
    try {
      const parsedArgs = toolArgs ? JSON.parse(toolArgs) : {};
      const response = await sendRequest(
        {
          method: "tools/call",
          params: { name: toolName, arguments: parsedArgs }
        },
        CompatibilityCallToolResultSchema
      );
      toolResult = JSON.stringify(response, null, 2);
      await fetch(`${playgroundUrl}/tool_call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool: toolName,
          input: parsedArgs,
          output: response
        })
      });
    } catch (err) {
      error = err?.message || String(err);
    }
  };

  const logPrompt = async () => {
    if (!promptText.trim()) {
      return;
    }
    await fetch(`${playgroundUrl}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        eventType: "prompt",
        payload: {
          text: promptText,
          context: promptContext
        }
      })
    });
    promptText = "";
    promptContext = "";
  };

  const copyText = async (value) => {
    if (!value) {
      return;
    }
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
    }
  };

  const toggleUiPreview = () => {
    uiPreviewExpanded = !uiPreviewExpanded;
    notifyHostContextChange();
  };

  const runSuggestedUiTool = async () => {
    if (!uiGuidance?.tool) {
      return;
    }
    error = "";
    try {
      if (uiAppInitialized) {
        sendUiNotification("ui/notifications/tool-input", {
          arguments: uiGuidance.args || {}
        });
      }
      const response = await sendRequest(
        {
          method: "tools/call",
          params: { name: uiToolName, arguments: uiGuidance.args }
        },
        CompatibilityCallToolResultSchema
      );
      uiToolResult = JSON.stringify(response, null, 2);
      if (uiAppInitialized) {
        sendUiNotification("ui/notifications/tool-result", response);
      }
    } catch (err) {
      error = err?.message || String(err);
      uiToolResult = "";
      if (uiAppInitialized) {
        sendUiNotification("ui/notifications/tool-cancelled", {
          reason: err?.message || String(err)
        });
      }
    }
  };

  const loadUiResource = async () => {
    if (!selectedResource?.uri) {
      return;
    }
    uiResourceError = "";
    uiPreviewReady = false;
    uiInstructionsVisible = false;
    uiAppInitialized = false;
    try {
      const response = await sendRequest(
        { method: "resources/read", params: { uri: selectedResource.uri } },
        AnySchema
      );
      const contents = response?.contents || response?.content || [];
      const first = contents[0] || {};
      uiResourceText = first.text || "";
      uiResourceMime = first.mimeType || first.mime_type || "";
      uiResourceMeta = first._meta || null;
      if (!uiResourceText) {
        uiResourceError = "No HTML payload returned for this UI resource.";
      } else {
        uiInstructionsVisible = true;
      }
    } catch (err) {
      uiResourceError = err?.message || String(err);
    }
  };

  const postToUi = (payload) => {
    if (!uiIframe?.contentWindow) {
      return;
    }
    uiIframe.contentWindow.postMessage(payload, "*");
  };

  const sendUiNotification = (method, params) => {
    postToUi({ jsonrpc: "2.0", method, params });
  };

  const respondToUi = (id, result, error) => {
    if (error) {
      postToUi({ jsonrpc: "2.0", id, error });
    } else {
      postToUi({ jsonrpc: "2.0", id, result });
    }
  };

  const buildHostContext = () => {
    let proxyBase = "http://localhost:8000";
    try {
      proxyBase = new URL(serverUrl).origin;
    } catch (err) {
      // keep default
    }
    const displayMode = uiPreviewExpanded ? "fullscreen" : "inline";
    return {
      displayMode,
      availableDisplayModes: ["inline", "fullscreen"],
      platform: "web",
      userAgent: "mcp-geo-playground",
      containerDimensions: uiPreviewExpanded
        ? { maxHeight: window.innerHeight }
        : { maxHeight: 700 },
      mcpGeo: { proxyBase }
    };
  };

  const buildHostCapabilities = () => {
    const permissions = uiResourceMeta?.ui?.permissions || {};
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
      openLinks: {}
    };
    if (Object.keys(sandbox).length) {
      capabilities.sandbox = sandbox;
    }
    return capabilities;
  };

  const handleUiRequest = async (message) => {
    const { id, method, params } = message;
    if (!id) {
      return;
    }
    if (method === "ui/initialize") {
      respondToUi(id, {
        protocolVersion: UI_PROTOCOL_VERSION,
        hostInfo: { name: "mcp-geo-playground", version: "0.1.0" },
        hostCapabilities: buildHostCapabilities(),
        hostContext: buildHostContext()
      });
      return;
    }
    if (method === "ui/request-display-mode") {
      const requested = params?.mode;
      const nextMode = requested === "fullscreen" ? "fullscreen" : "inline";
      uiPreviewExpanded = nextMode === "fullscreen";
      respondToUi(id, { mode: nextMode });
      if (uiAppInitialized) {
        sendUiNotification("ui/notifications/host-context-changed", buildHostContext());
      }
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
    if (method === "ui/message") {
      recordHistory({ request: message, response: {}, at: new Date().toISOString() });
      respondToUi(id, {});
      return;
    }
    if (method === "ui/update-model-context") {
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
  };

  const notifyHostContextChange = () => {
    if (!uiAppInitialized) {
      return;
    }
    sendUiNotification("ui/notifications/host-context-changed", buildHostContext());
  };

  onMount(() => {
    const handler = async (event) => {
      if (!uiIframe?.contentWindow || event.source !== uiIframe.contentWindow) {
        return;
      }
      const message = event.data;
      if (!message || typeof message !== "object" || message.jsonrpc !== "2.0") {
        return;
      }
      if (message.method && message.id === undefined) {
        if (message.method === "ui/notifications/initialized") {
          uiAppInitialized = true;
          uiPreviewReady = true;
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
    return () => window.removeEventListener("message", handler);
  });

  $: if (typeof document !== "undefined") {
    document.body.style.overflow = uiPreviewExpanded ? "hidden" : "";
  }

  $: uiResourceHtml = uiResourceText ? injectCsp(uiResourceText, uiResourceMeta) : "";
  $: uiIframeSandbox = buildSandbox(uiResourceMeta);
  $: uiIframeAllow = buildAllow(uiResourceMeta);

  $: descriptorJson = descriptorRaw ? JSON.stringify(descriptorRaw, null, 2) : "";
  $: descriptorSizeBytes = descriptorRaw
    ? new TextEncoder().encode(JSON.stringify(descriptorRaw)).length
    : 0;
  $: descriptorSizeLabel = descriptorSizeBytes
    ? `${(descriptorSizeBytes / 1024).toFixed(1)} KB`
    : "0 KB";
  $: descriptorWarn = descriptorSizeBytes > 50 * 1024;

  $: toolCounts = descriptorMeta?.toolSearch?.counts || {};
  $: toolsTotal = toolCounts.total || tools.length;
  $: toolsLoaded = toolCounts.always_loaded || Math.min(tools.length, toolsTotal);

  $: filteredTools = tools.filter((tool) =>
    tool.name.toLowerCase().includes(toolFilter.toLowerCase())
  );
  $: filteredResources = resources.filter((resource) =>
    resource.name.toLowerCase().includes(resourceFilter.toLowerCase())
  );
  $: filteredPrompts = prompts.filter((prompt) =>
    (prompt.name || "").toLowerCase().includes(promptFilter.toLowerCase())
  );

  $: uiGuidance = (() => {
    if (!selectedResource?.uri?.startsWith("ui://")) {
      return null;
    }
    const match = uiToolMap.find((entry) => selectedResource.uri.includes(entry.match));
    if (!match) {
      return { tool: null, args: null };
    }
    return match;
  })();

  $: uiToolName = uiGuidance?.tool ? uiGuidance.tool.replace(/\./g, "_") : "";
  $: uiExampleCall = uiGuidance?.tool
    ? JSON.stringify({ name: uiToolName, arguments: uiGuidance.args }, null, 2)
    : "";
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
      <h1>Testing + tracing cockpit for MCP Geo.</h1>
      <p class="sub">Expose what the model sees, then drill into tools, resources, and outputs.</p>
    </div>
    <div class="status">
      <span class={`dot ${status}`}></span>
      <div>
        <div class="label">Status</div>
        <div class="value">{status}</div>
      </div>
    </div>
  </header>

  <nav class="tabs">
    <button class:active={activeTab === "setup"} on:click={() => (activeTab = "setup")}>Setup</button>
    <button class:active={activeTab === "test"} on:click={() => (activeTab = "test")}>Test</button>
    <button class:active={activeTab === "trace"} on:click={() => (activeTab = "trace")}>Trace</button>
  </nav>

  {#if activeTab === "setup"}
    <section class="grid">
      <div class="card">
        <h2>Connection</h2>
        <label>
          Server URL
          <input type="url" bind:value={serverUrl} />
        </label>
        <label>
          Playground API
          <input type="url" bind:value={playgroundUrl} />
        </label>
        <div class="actions">
          <button class="primary" on:click={connect} disabled={status === "connecting"}>
            Connect
          </button>
          <button class="ghost" on:click={disconnect} disabled={status !== "connected"}>
            Disconnect
          </button>
          <button class="ghost" on:click={refreshLists} disabled={status !== "connected"}>
            Refresh
          </button>
        </div>
        {#if error}
          <div class="error">{error}</div>
        {/if}
      </div>

      <div class="card">
        <h2>Descriptor (initial view)</h2>
        {#if descriptorMeta}
          <div class="descriptor-meta">
            <div>
              <div class="label">Server</div>
              <div class="value">{descriptorMeta.server} · v{descriptorMeta.version}</div>
            </div>
            <div>
              <div class="label">Protocol</div>
              <div class="value">{descriptorMeta.protocolVersion || "n/a"}</div>
            </div>
            <div>
              <div class="label">Transport</div>
              <div class="value">{descriptorMeta.transport || "http"}</div>
            </div>
            <div>
              <div class="label">Descriptor size</div>
              <div class={`value ${descriptorWarn ? "warn" : ""}`}>{descriptorSizeLabel}</div>
            </div>
          </div>
          <div class="caps">
            <h3>Capabilities</h3>
            <div class="cap-grid">
              {#if descriptorMeta.capabilities}
                {#each Object.entries(descriptorMeta.capabilities) as [key, value]}
                  <div class="cap">
                    <strong>{key}</strong>
                    <span>{JSON.stringify(value)}</span>
                  </div>
                {/each}
              {:else}
                <p class="muted">No capability metadata yet.</p>
              {/if}
            </div>
          </div>
          <details class="details-block">
            <summary>Full descriptor payload</summary>
            <pre>{descriptorJson}</pre>
          </details>
        {:else}
          <p class="muted">Connect to fetch server metadata.</p>
        {/if}
      </div>
    </section>
  {/if}

  {#if activeTab === "test"}
    <section class="split">
      <div class="pane">
        <div class="pane-header">
          <div class="pane-tabs">
            <button class:active={testSection === "tools"} on:click={() => (testSection = "tools")}>
              Tools ({toolsLoaded}/{toolsTotal})
            </button>
            <button class:active={testSection === "resources"} on:click={() => (testSection = "resources")}>
              Resources ({resources.length})
            </button>
            <button class:active={testSection === "prompts"} on:click={() => (testSection = "prompts")}>
              Prompts ({prompts.length})
            </button>
            <button class:active={testSection === "templates"} on:click={() => (testSection = "templates")}>
              Templates ({resourceTemplates.length})
            </button>
          </div>
          <div class="pane-filters">
            {#if testSection === "tools"}
              <input type="text" placeholder="Filter tools" bind:value={toolFilter} />
            {:else if testSection === "resources"}
              <input type="text" placeholder="Filter resources" bind:value={resourceFilter} />
            {:else if testSection === "prompts"}
              <input type="text" placeholder="Filter prompts" bind:value={promptFilter} />
            {/if}
          </div>
        </div>

        <div class="pane-body">
          <div class="help-card">
            <strong>How to use Test</strong>
            <p>Browse Tools/Resources/Prompts, then select an item to see schemas and metadata.</p>
            <p>For tools, edit the example payload and run it to capture output.</p>
            <p>For ui:// resources, load the HTML to preview the UI surface.</p>
          </div>
          {#if testSection === "tools"}
            {#each filteredTools as tool}
              <button
                class:selected={selectedTool?.name === tool.name}
                class="list-item"
                title={tool.annotations ? JSON.stringify(tool.annotations, null, 2) : "No annotations"}
                on:click={() => selectTool(tool)}
              >
                <div class="list-title">{tool.name}</div>
                <div class="list-sub">{tool.description}</div>
                <div class="list-badges">
                  {#if tool.defer_loading || tool.deferLoading}
                    <span class="badge">deferred</span>
                  {/if}
                  {#if tool.category}
                    <span class="badge badge-ghost">{tool.category}</span>
                  {/if}
                  {#if tool.version}
                    <span class="badge badge-ghost">v{tool.version}</span>
                  {/if}
                </div>
              </button>
            {/each}
          {:else if testSection === "resources"}
            {#each filteredResources as resource}
              <button
                class:selected={selectedResource?.uri === resource.uri}
                class="list-item"
                on:click={() => selectResource(resource)}
              >
                <div class="list-title">{resource.name}</div>
                <div class="list-sub">{resource.uri}</div>
                <div class="list-badges">
                  <span class="badge badge-ghost">{resource.type || resource.mimeType}</span>
                </div>
              </button>
            {/each}
          {:else if testSection === "templates"}
            {#if resourceTemplates.length === 0}
              <p class="muted">No templates advertised.</p>
            {:else}
              {#each resourceTemplates as template}
                <div class="list-item static">
                  <div class="list-title">{template.name}</div>
                  <div class="list-sub">{template.uriTemplate}</div>
                </div>
              {/each}
            {/if}
          {:else}
            {#if promptsError}
              <p class="muted">{promptsError}</p>
            {:else}
              {#each filteredPrompts as prompt}
                <button
                  class:selected={selectedPrompt?.name === prompt.name}
                  class="list-item"
                  on:click={() => selectPrompt(prompt)}
                >
                  <div class="list-title">{prompt.name}</div>
                  <div class="list-sub">{prompt.description || ""}</div>
                </button>
              {/each}
            {/if}
          {/if}
        </div>
      </div>

      <div class="pane">
        <div class="pane-header alt">
          <div class="pane-title">Details</div>
          <div class="pane-actions">
            <button class="ghost" on:click={refreshLists} disabled={status !== "connected"}>
              Refresh
            </button>
          </div>
        </div>
        <div class="pane-body">
          {#if selectedTool}
            <div class="detail-block">
              <h3>{selectedTool.name}</h3>
              <p class="muted">{selectedTool.description}</p>
              <div class="meta-grid">
                <div>
                  <div class="label">Category</div>
                  <div class="value">{selectedTool.category || "n/a"}</div>
                </div>
                <div>
                  <div class="label">Version</div>
                  <div class="value">{selectedTool.version || "n/a"}</div>
                </div>
                <div>
                  <div class="label">Deferred</div>
                  <div class="value">{(selectedTool.defer_loading || selectedTool.deferLoading) ? "yes" : "no"}</div>
                </div>
              </div>
              <details class="details-block" open>
                <summary>Input schema</summary>
                <pre>{JSON.stringify(selectedTool.inputSchema || selectedTool.input_schema, null, 2)}</pre>
              </details>
              <details class="details-block">
                <summary>Output schema</summary>
                <pre>{JSON.stringify(selectedTool.outputSchema || selectedTool.output_schema, null, 2)}</pre>
              </details>
              <details class="details-block">
                <summary>Annotations</summary>
                <pre>{JSON.stringify(selectedTool.annotations || {}, null, 2)}</pre>
              </details>
              <div class="detail-block">
                <h4>Example call</h4>
                <textarea rows="10" bind:value={toolArgs}></textarea>
                <div class="actions">
                  <button class="primary" on:click={callTool} disabled={status !== "connected"}>
                    Run Tool
                  </button>
                </div>
              </div>
              {#if toolResult}
                <details class="details-block" open>
                  <summary>Tool output</summary>
                  <pre>{toolResult}</pre>
                </details>
              {/if}
            </div>
          {:else if selectedResource}
            <div class="detail-block">
              <h3>{selectedResource.name}</h3>
              <p class="muted">{selectedResource.description || ""}</p>
              {#if selectedResource.uri?.startsWith("ui://")}
                <div class="info-card">
                  <h4>UI resource (MCP Apps)</h4>
                  <ul>
                    <li>ui:// is an MCP Apps scheme, not HTTP/HTTPS.</li>
                    <li>Rendered by the client UI; no response payload or API body.</li>
                    <li>Meaning comes from UI events that trigger tool calls or state updates.</li>
                  </ul>
                  {#if uiGuidance?.tool}
                    <div class="example-block">
                      <div class="label">Suggested tool call</div>
                      <pre>{uiExampleCall}</pre>
                      <div class="actions">
                        <button class="ghost" on:click={() => copyText(uiExampleCall)}>
                          Copy example
                        </button>
                        <button class="primary" on:click={runSuggestedUiTool}>
                          Run suggested tool
                        </button>
                      </div>
                    </div>
                  {:else}
                    <p class="muted">No tool mapping available for this UI resource yet.</p>
                  {/if}
                </div>
                <div class="detail-block">
                  <h4>UI content preview</h4>
                  <div class="actions">
                    <button class="ghost" on:click={loadUiResource}>Load UI HTML</button>
                  </div>
                  {#if uiResourceError}
                    <div class="error">{uiResourceError}</div>
                  {/if}
                  {#if uiResourceText}
                    {#if uiResourceMime.includes("text/html")}
                      <div class={`preview-frame ${uiPreviewExpanded ? "expanded" : ""}`}>
                        <div class="preview-toolbar">
                          <span>UI preview</span>
                          <button
                            class="icon-button"
                            on:click={toggleUiPreview}
                            aria-label={uiPreviewExpanded ? "Minimize preview" : "Maximize preview"}
                          >
                            {uiPreviewExpanded ? "Minimize" : "Maximize"}
                          </button>
                        </div>
                        {#if uiInstructionsVisible}
                          <div class="preview-overlay">
                            <div class="overlay-card">
                              <h4>Loading MCP App UI</h4>
                              <p>This UI is served by the MCP server and can take time to initialize.</p>
                              <p>It lets you explore workflows and trigger tool calls from the interface.</p>
                              <p class="muted">Close this once the UI appears.</p>
                              <button class="primary" on:click={() => (uiInstructionsVisible = false)}>
                                {uiPreviewReady ? "Close instructions" : "Dismiss while loading"}
                              </button>
                            </div>
                          </div>
                        {/if}
                        <iframe
                          bind:this={uiIframe}
                          title="UI preview"
                          sandbox={uiIframeSandbox}
                          allow={uiIframeAllow}
                          srcdoc={uiResourceHtml}
                        ></iframe>
                      </div>
                    {/if}
                    <details class="details-block" open>
                      <summary>Raw HTML</summary>
                      <pre>{uiResourceText}</pre>
                    </details>
                  {/if}
                </div>
                {#if uiToolResult}
                  <details class="details-block" open>
                    <summary>UI tool output</summary>
                    <pre>{uiToolResult}</pre>
                  </details>
                {/if}
              {/if}
              <div class="meta-grid">
                <div>
                  <div class="label">URI</div>
                  <div class="value">{selectedResource.uri}</div>
                </div>
                <div>
                  <div class="label">Type</div>
                  <div class="value">{selectedResource.type || selectedResource.mimeType}</div>
                </div>
              </div>
              <div class="actions">
                <button class="ghost" on:click={() => copyText(selectedResource.uri)}>Copy URI</button>
              </div>
              <details class="details-block" open>
                <summary>Resource metadata</summary>
                <pre>{JSON.stringify(selectedResource, null, 2)}</pre>
              </details>
            </div>
          {:else if selectedPrompt}
            <div class="detail-block">
              <h3>{selectedPrompt.name}</h3>
              <p class="muted">{selectedPrompt.description || ""}</p>
              <details class="details-block" open>
                <summary>Prompt metadata</summary>
                <pre>{JSON.stringify(selectedPrompt, null, 2)}</pre>
              </details>
            </div>
          {:else}
            <p class="muted">Select a tool, resource, or prompt to view details.</p>
          {/if}
        </div>
      </div>
    </section>
  {/if}

  {#if activeTab === "trace"}
    <section class="split">
      <div class="pane">
        <div class="pane-header">
          <div class="pane-title">Prompt capture</div>
        </div>
        <div class="pane-body">
          <div class="help-card">
            <strong>How to use Trace</strong>
            <p>Log prompts before tool runs to capture intent and context.</p>
            <p>The history pane shows every MCP request/response while connected.</p>
          </div>
          <label>
            Prompt
            <textarea rows="6" bind:value={promptText}></textarea>
          </label>
          <label>
            Context (optional)
            <input type="text" bind:value={promptContext} />
          </label>
          <div class="actions">
            <button class="primary" on:click={logPrompt}>Log Prompt</button>
          </div>
          <p class="muted">Capture user prompts before tool runs to track intent + context.</p>
        </div>
      </div>

      <div class="pane">
        <div class="pane-header alt">
          <div class="pane-title">Request history</div>
        </div>
        <div class="pane-body">
          {#each history as entry}
            <div class="history">
              <strong>{entry.at}</strong>
              <pre>{JSON.stringify(entry.request, null, 2)}</pre>
              <pre>{JSON.stringify(entry.response, null, 2)}</pre>
            </div>
          {/each}
        </div>
      </div>
    </section>
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
    padding: 26px;
    border-radius: 20px;
    box-shadow: 0 12px 30px rgba(11, 31, 33, 0.2);
  }

  .hero h1 {
    margin: 8px 0 12px;
    font-size: 2rem;
    line-height: 1.2;
  }

  .eyebrow {
    font-size: 0.75rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #7fdac9;
  }

  .sub {
    font-family: "Spectral", serif;
    max-width: 460px;
  }

  .status {
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

  .label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: rgba(255, 255, 255, 0.7);
  }

  .value {
    font-size: 1.05rem;
    font-weight: 600;
  }

  .value.warn {
    color: #f4c95d;
  }

  .tabs {
    display: flex;
    gap: 12px;
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

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }

  .split {
    display: grid;
    grid-template-columns: minmax(280px, 1fr) minmax(320px, 1.3fr);
    gap: 20px;
  }

  .card,
  .pane {
    background: #fdfbf7;
    border-radius: 16px;
    box-shadow: 0 8px 20px rgba(15, 42, 45, 0.08);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .card {
    padding: 20px;
    gap: 12px;
  }

  .pane-header {
    position: sticky;
    top: 0;
    z-index: 2;
    background: #f2e9dd;
    padding: 12px 16px;
    border-bottom: 1px solid #e0d3c5;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .pane-header.alt {
    background: #efe3d4;
  }

  .pane-title {
    font-weight: 700;
  }

  .pane-tabs {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .pane-tabs button {
    border: none;
    background: #fffaf2;
    border-radius: 999px;
    padding: 6px 12px;
    font-weight: 600;
    cursor: pointer;
  }

  .pane-tabs button.active {
    background: #0b1f21;
    color: #f7f4ef;
  }

  .pane-filters input {
    border-radius: 999px;
    padding: 6px 12px;
    border: 1px solid #d7d0c5;
    background: #fffaf2;
  }

  .pane-body {
    padding: 16px;
    overflow: auto;
    max-height: 65vh;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .card h2 {
    margin: 0;
    font-size: 1.1rem;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.85rem;
    color: #34424a;
  }

  input,
  textarea {
    border: 1px solid #d7d0c5;
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 0.9rem;
    background: #fffaf2;
  }

  textarea {
    font-family: "Space Grotesk", sans-serif;
  }

  .actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  button {
    border: none;
    padding: 10px 16px;
    border-radius: 999px;
    font-weight: 600;
    cursor: pointer;
  }

  button.primary {
    background: #2e7d6b;
    color: #fff;
  }

  button.ghost {
    background: transparent;
    border: 1px solid #2e7d6b;
    color: #2e7d6b;
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .descriptor-meta {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 12px;
    background: #efe3d4;
    padding: 12px;
    border-radius: 12px;
  }

  .descriptor-meta .label {
    color: #4b3b2d;
  }

  .caps {
    margin-top: 12px;
  }

  .cap-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 8px;
  }

  .cap {
    background: #fffaf2;
    border-radius: 10px;
    padding: 8px;
  }

  .details-block {
    margin-top: 12px;
    background: #fffaf2;
    border-radius: 10px;
    padding: 10px;
  }

  .details-block summary {
    cursor: pointer;
    font-weight: 600;
  }

  .list-item {
    text-align: left;
    border: 1px solid #e0d3c5;
    border-radius: 12px;
    padding: 12px;
    background: #fffaf2;
  }

  .list-item.selected {
    border-color: #2e7d6b;
    background: #e6f3ee;
  }

  .list-item.static {
    border-style: dashed;
  }

  .list-title {
    font-weight: 600;
  }

  .list-sub {
    color: #567;
    font-size: 0.85rem;
    margin-top: 4px;
  }

  .list-badges {
    display: flex;
    gap: 6px;
    margin-top: 8px;
    flex-wrap: wrap;
  }

  .badge {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    background: #0b1f21;
    color: #f7f4ef;
    padding: 2px 8px;
    border-radius: 999px;
  }

  .badge-ghost {
    background: transparent;
    color: #0b1f21;
    border: 1px solid #0b1f21;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 10px;
    margin: 12px 0;
  }

  pre {
    background: #0d1a1c;
    color: #e0efe8;
    padding: 12px;
    border-radius: 12px;
    overflow: auto;
    font-size: 0.75rem;
  }

  .muted {
    color: #7a7a7a;
    font-size: 0.85rem;
  }

  .error {
    background: #fce4e4;
    color: #9a1f1f;
    padding: 10px 12px;
    border-radius: 10px;
  }

  .history {
    display: flex;
    flex-direction: column;
    gap: 8px;
    border: 1px solid #e2d8cc;
    padding: 10px;
    border-radius: 12px;
    background: #fff;
  }

  .info-card {
    background: #fffaf2;
    border: 1px solid #e0d3c5;
    border-radius: 12px;
    padding: 12px;
    margin: 12px 0;
  }

  .info-card h4 {
    margin: 0 0 8px;
  }

  .info-card ul {
    margin: 0 0 10px;
    padding-left: 18px;
    color: #4b3b2d;
  }

  .example-block {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .help-card {
    background: #fffaf2;
    border: 1px dashed #d2c4b4;
    border-radius: 12px;
    padding: 12px;
    color: #4b3b2d;
  }

  .help-card p {
    margin: 6px 0 0;
  }

  .pane .label {
    color: #5a4a3a;
  }

  .preview-frame {
    border: 1px solid #e2d8cc;
    border-radius: 12px;
    overflow: hidden;
    background: #fff;
  }

  .preview-overlay {
    position: absolute;
    inset: 50px;
    z-index: 6;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: auto;
  }

  .overlay-card {
    background: rgba(255, 250, 242, 0.98);
    border: 1px solid #e2d8cc;
    border-radius: 16px;
    padding: 20px;
    max-width: 420px;
    box-shadow: 0 16px 30px rgba(0, 0, 0, 0.15);
    text-align: left;
  }

  .overlay-card h4 {
    margin: 0 0 8px;
  }

  .preview-frame.expanded {
    position: fixed;
    inset: 20px;
    z-index: 50;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  }

  .preview-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: #efe3d4;
    border-bottom: 1px solid #e2d8cc;
    font-weight: 600;
  }

  .icon-button {
    background: transparent;
    border: 1px solid #2e7d6b;
    color: #2e7d6b;
    padding: 6px 10px;
    border-radius: 999px;
    font-weight: 600;
  }

  .preview-frame iframe {
    width: 100%;
    height: 360px;
    border: none;
  }

  .preview-frame.expanded iframe {
    height: calc(100vh - 96px);
  }

  @media (max-width: 900px) {
    .split {
      grid-template-columns: 1fr;
    }
    .pane-body {
      max-height: none;
    }
  }
</style>
