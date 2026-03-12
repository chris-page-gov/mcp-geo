<script>
  import UiPreviewPanel from "./UiPreviewPanel.svelte";

  export let capabilities = null;
  export let COMPACT_HEIGHT_MAX = 900;
  export let COMPACT_HEIGHT_MIN = 360;
  export let COMPACT_WIDTH_MAX = 520;
  export let COMPACT_WIDTH_MIN = 280;
  export let connect = () => {};
  export let copyText = async () => {};
  export let coreProtocolVersion = "n/a";
  export let descriptorJson = "";
  export let descriptorMeta = null;
  export let descriptorSizeLabel = "0 KB";
  export let descriptorWarn = false;
  export let disconnect = () => {};
  export let error = "";
  export let fetchDescriptor = () => {};
  export let filteredPrompts = [];
  export let filteredResources = [];
  export let filteredTools = [];
  export let formatTracePayload = (value) => JSON.stringify(value, null, 2);
  export let history = [];
  export let loadUiResource = () => {};
  export let logPrompt = () => {};
  export let MCP_SDK_VERSION = "unknown";
  export let mcpAppsProtocolVersion = "n/a";
  export let onCompactHeightInput = () => {};
  export let onCompactWidthInput = () => {};
  export let onDismissUiInstructions = () => {};
  export let onPlaygroundUrlInput = () => {};
  export let onServerUrlInput = () => {};
  export let onToggleSameOrigin = () => {};
  export let onViewportModeChange = () => {};
  export let playgroundUrl = "";
  export let PLAYGROUND_CLIENT_INFO = { version: "0.1.0" };
  export let promptContext = "";
  export let promptFilter = "";
  export let promptText = "";
  export let prompts = [];
  export let promptsError = "";
  export let refreshLists = () => {};
  export let resourceFilter = "";
  export let resourceTemplates = [];
  export let runSuggestedUiTool = () => {};
  export let selectedPrompt = null;
  export let selectedResource = null;
  export let selectedTool = null;
  export let selectPrompt = () => {};
  export let selectResource = () => {};
  export let selectTool = () => {};
  export let serverUrl = "";
  export let serverVersion = "n/a";
  export let status = "disconnected";
  export let supportedProtocolVersions = "n/a";
  export let toolArgs = "{}";
  export let toolFilter = "";
  export let toolResult = "";
  export let tools = [];
  export let toolsLoaded = 0;
  export let toolsTotal = 0;
  export let traceRedact = true;
  export let uiAllowSameOrigin = false;
  export let uiCompactHeight = 500;
  export let uiCompactHeightPx = 500;
  export let uiCompactWidth = 320;
  export let uiCompactWidthPx = 320;
  export let uiExampleCall = "";
  export let uiGuidance = null;
  export let uiHostViewportMode = "auto";
  export let uiIframeAllow = "";
  export let uiIframeSandbox = "allow-scripts";
  export let uiInstructionsVisible = false;
  export let uiPreviewExpanded = false;
  export let uiPreviewInlineStyle = "";
  export let uiPreviewReady = false;
  export let uiResourceError = "";
  export let uiResourceHtml = "";
  export let uiResourceMime = "";
  export let uiResourceText = "";
  export let uiSameOriginRequested = false;
  export let uiToolResult = "";
  export let toggleUiPreview = () => {};
  export let callTool = () => {};
  export let BUILD_INFO = { dev: false };
  export let uiIframe = null;
</script>

<section class="grid">
  <div class="card">
    <h2>Connection</h2>
    <label>
      Server URL
      <input type="url" bind:value={serverUrl} on:input={onServerUrlInput} />
    </label>
    <label>
      Playground API
      <input type="url" bind:value={playgroundUrl} on:input={onPlaygroundUrlInput} />
    </label>
    <div class="actions">
      <button class="primary" on:click={connect} disabled={status === "connecting" || status === "connected"}>
        Connect
      </button>
      <button class="ghost" on:click={disconnect} disabled={status !== "connected"}>
        Disconnect
      </button>
      <button class="ghost" on:click={refreshLists} disabled={status !== "connected"}>
        Refresh
      </button>
      <button class="ghost" on:click={fetchDescriptor} disabled={status !== "connected"}>
        Reload descriptor
      </button>
    </div>
    {#if error}
      <div class="error">{error}</div>
    {/if}
  </div>

  <div class="card">
    <h2>Descriptor and protocol matrix</h2>
    <div class="version-grid">
      <div class="version-item">
        <div class="label">Server package</div>
        <div class="value">{serverVersion}</div>
      </div>
      <div class="version-item">
        <div class="label">MCP core (active)</div>
        <div class="value">{coreProtocolVersion}</div>
      </div>
      <div class="version-item">
        <div class="label">MCP core (supported)</div>
        <div class="value">{supportedProtocolVersions}</div>
      </div>
      <div class="version-item">
        <div class="label">MCP Apps protocol (server)</div>
        <div class="value">{mcpAppsProtocolVersion}</div>
      </div>
      <div class="version-item">
        <div class="label">Playground client</div>
        <div class="value">{PLAYGROUND_CLIENT_INFO.version}</div>
      </div>
      <div class="version-item">
        <div class="label">MCP SDK dependency</div>
        <div class="value">{MCP_SDK_VERSION}</div>
      </div>
    </div>
    {#if descriptorMeta}
      <div class="descriptor-meta">
        <div>
          <div class="label">Server</div>
          <div class="value">{descriptorMeta.server} · v{descriptorMeta.version}</div>
        </div>
        <div>
          <div class="label">Transport</div>
          <div class="value">{descriptorMeta.transport || "http"}</div>
        </div>
        <div>
          <div class="label">Descriptor size</div>
          <div class={`value ${descriptorWarn ? "warn" : ""}`}>{descriptorSizeLabel}</div>
        </div>
        <div>
          <div class="label">Capabilities loaded</div>
          <div class="value">{capabilities ? Object.keys(capabilities).length : 0}</div>
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

<section class="split">
  <div class="pane">
    <div class="pane-header">
      <div class="pane-tabs">
        <span class="badge">Tools {toolsLoaded}/{toolsTotal}</span>
        <span class="badge badge-ghost">Resources {filteredResources.length}/{tools.length ? filteredResources.length : filteredResources.length}</span>
        <span class="badge badge-ghost">Prompts {prompts.length}</span>
        <span class="badge badge-ghost">Templates {resourceTemplates.length}</span>
      </div>
      <div class="pane-actions">
        <button class="ghost" on:click={refreshLists} disabled={status !== "connected"}>Refresh</button>
      </div>
    </div>
    <div class="pane-body">
      <div class="catalog-grid">
        <section class="catalog-column">
          <label>
            Filter tools
            <input type="text" bind:value={toolFilter} placeholder="Filter tools" />
          </label>
          {#each filteredTools as tool}
            <button
              class:selected={selectedTool?.name === tool.name}
              class="list-item"
              title={tool.annotations ? JSON.stringify(tool.annotations, null, 2) : "No annotations"}
              on:click={() => selectTool(tool)}
            >
              <div class="list-title">{tool.name}</div>
              <div class="list-sub">{tool.description}</div>
            </button>
          {/each}
        </section>

        <section class="catalog-column">
          <label>
            Filter resources
            <input type="text" bind:value={resourceFilter} placeholder="Filter resources" />
          </label>
          {#each filteredResources as resource}
            <button
              class:selected={selectedResource?.uri === resource.uri}
              class="list-item"
              on:click={() => selectResource(resource)}
            >
              <div class="list-title">{resource.name}</div>
              <div class="list-sub">{resource.uri}</div>
            </button>
          {/each}
        </section>

        <section class="catalog-column">
          <label>
            Filter prompts
            <input type="text" bind:value={promptFilter} placeholder="Filter prompts" />
          </label>
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
          {#if resourceTemplates.length}
            <details class="details-block">
              <summary>Templates</summary>
              {#each resourceTemplates as template}
                <div class="template-entry">
                  <strong>{template.name}</strong>
                  <div class="list-sub">{template.uriTemplate}</div>
                </div>
              {/each}
            </details>
          {/if}
        </section>
      </div>
    </div>
  </div>

  <div class="pane">
    <div class="pane-header alt">
      <div class="pane-title">Details</div>
    </div>
    <div class="pane-body">
      {#if selectedTool}
        <div class="detail-block">
          <h3>{selectedTool.name}</h3>
          <p class="muted">{selectedTool.description}</p>
          <details class="details-block" open>
            <summary>Input schema</summary>
            <pre>{JSON.stringify(selectedTool.inputSchema || selectedTool.input_schema, null, 2)}</pre>
          </details>
          <details class="details-block">
            <summary>Output schema</summary>
            <pre>{JSON.stringify(selectedTool.outputSchema || selectedTool.output_schema, null, 2)}</pre>
          </details>
          <h4>Example call</h4>
          <textarea rows="10" bind:value={toolArgs}></textarea>
          <div class="actions">
            <button class="primary" on:click={callTool} disabled={status !== "connected"}>Run tool</button>
            <button class="ghost" on:click={() => copyText(toolArgs)}>Copy payload</button>
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
              <h4>UI resource</h4>
              <p class="muted">The host loads the widget HTML and brokers approved tool and resource calls back to the MCP server.</p>
              {#if uiGuidance?.tool}
                <div class="example-block">
                  <div class="label">Suggested tool call</div>
                  <pre>{uiExampleCall}</pre>
                  <div class="actions">
                    <button class="ghost" on:click={() => copyText(uiExampleCall)}>Copy example</button>
                    <button class="primary" on:click={runSuggestedUiTool} disabled={status !== "connected"}>
                      Run suggested tool
                    </button>
                  </div>
                </div>
              {/if}
            </div>
            {#if uiSameOriginRequested}
              <div class="info-card">
                <h4>Sandbox posture</h4>
                <p>
                  Same-origin access stays off by default. Enable it only for trusted widget debugging.
                </p>
                <label class="toggle">
                  <input type="checkbox" bind:checked={uiAllowSameOrigin} on:change={onToggleSameOrigin} />
                  <span>Allow same-origin for this UI (unsafe)</span>
                </label>
                {#if BUILD_INFO.dev}
                  <p class="muted">Dev mode no longer enables this automatically.</p>
                {/if}
              </div>
            {/if}
            <UiPreviewPanel
              bind:iframeRef={uiIframe}
              {COMPACT_HEIGHT_MAX}
              {COMPACT_HEIGHT_MIN}
              {COMPACT_WIDTH_MAX}
              {COMPACT_WIDTH_MIN}
              onLoad={loadUiResource}
              {onCompactHeightInput}
              {onCompactWidthInput}
              onDismissInstructions={onDismissUiInstructions}
              {onViewportModeChange}
              resourceLabel="UI content preview"
              selectedResourceUri={selectedResource.uri}
              onTogglePreview={toggleUiPreview}
              bind:uiCompactHeight
              {uiCompactHeightPx}
              bind:uiCompactWidth
              {uiCompactWidthPx}
              bind:uiHostViewportMode
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

<section class="split">
  <div class="pane">
    <div class="pane-header">
      <div class="pane-title">Trace capture</div>
    </div>
    <div class="pane-body">
      <label class="toggle">
        <input type="checkbox" bind:checked={traceRedact} />
        <span>Redact trace payloads</span>
      </label>
      <label>
        Prompt
        <textarea rows="6" bind:value={promptText}></textarea>
      </label>
      <label>
        Context (optional)
        <input type="text" bind:value={promptContext} />
      </label>
      <div class="actions">
        <button class="primary" on:click={logPrompt}>Log prompt</button>
      </div>
    </div>
  </div>

  <div class="pane">
    <div class="pane-header alt">
      <div class="pane-title">Request history</div>
    </div>
    <div class="pane-body">
      {#if history.length === 0}
        <p class="muted">No MCP or host interactions captured yet.</p>
      {:else}
        {#each history as entry}
          <div class="history">
            <strong>{entry.at}</strong>
            <pre>{formatTracePayload(entry.request)}</pre>
            <pre>{formatTracePayload(entry.response)}</pre>
          </div>
        {/each}
      {/if}
      {#if uiToolResult}
        <details class="details-block">
          <summary>Last UI tool output</summary>
          <pre>{uiToolResult}</pre>
        </details>
      {/if}
    </div>
  </div>
</section>

<style>
  .catalog-grid {
    display: grid;
    gap: 16px;
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .catalog-column {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .version-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 10px;
  }

  .version-item {
    background: #f4ecdf;
    border-radius: 10px;
    padding: 10px;
  }

  .descriptor-meta {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    background: #efe3d4;
    padding: 12px;
    border-radius: 12px;
  }

  .template-entry {
    padding: 8px 0;
    border-top: 1px solid #e2d8cc;
  }

  .template-entry:first-child {
    border-top: 0;
  }

  @media (max-width: 1100px) {
    .catalog-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
