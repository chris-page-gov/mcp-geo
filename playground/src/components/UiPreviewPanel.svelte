<script>
  export let compactHeightMax = 900;
  export let compactHeightMin = 360;
  export let compactWidthMax = 520;
  export let compactWidthMin = 280;
  export let iframeRef = null;
  export let onCompactHeightInput = () => {};
  export let onCompactWidthInput = () => {};
  export let onDismissInstructions = () => {};
  export let onLoad = () => {};
  export let onTogglePreview = () => {};
  export let onViewportModeChange = () => {};
  export let resourceLabel = "UI preview";
  export let selectedResourceUri = "";
  export let uiCompactHeight = 500;
  export let uiCompactHeightPx = 500;
  export let uiCompactWidth = 320;
  export let uiCompactWidthPx = 320;
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
</script>

<div class="detail-block">
  <h4>{resourceLabel}</h4>
  <div class="actions">
    <button class="ghost" on:click={onLoad}>Load UI HTML</button>
  </div>
  <div class="preview-controls">
    <div class="preview-control-grid">
      <label>
        Host viewport mode
        <select bind:value={uiHostViewportMode} on:change={onViewportModeChange} data-testid="host-viewport-mode">
          <option value="auto">Auto (host default)</option>
          <option value="compact">Force compact window</option>
          <option value="regular">Force regular window</option>
        </select>
      </label>
      {#if uiHostViewportMode === "compact"}
        <label>
          Compact width (px)
          <input
            type="number"
            min={compactWidthMin}
            max={compactWidthMax}
            step="10"
            bind:value={uiCompactWidth}
            on:input={onCompactWidthInput}
            data-testid="host-compact-width"
          />
        </label>
        <label>
          Compact height (px)
          <input
            type="number"
            min={compactHeightMin}
            max={compactHeightMax}
            step="10"
            bind:value={uiCompactHeight}
            on:input={onCompactHeightInput}
            data-testid="host-compact-height"
          />
        </label>
      {/if}
    </div>
    <p class="muted">Updates <code>hostContext.containerDimensions</code> used by the widget.</p>
  </div>
  {#if uiResourceError}
    <div class="error">{uiResourceError}</div>
  {/if}
  {#if uiResourceText && uiResourceMime.includes("text/html")}
    <div
      class={`preview-frame ${uiPreviewExpanded ? "expanded" : ""} ${uiHostViewportMode === "compact" ? "compact-inline" : ""}`}
      style={uiPreviewInlineStyle}
    >
      <div class="preview-toolbar">
        <span>{resourceLabel}</span>
        <button
          class="icon-button"
          on:click={onTogglePreview}
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
            <button class="primary" on:click={onDismissInstructions}>
              {uiPreviewReady ? "Close instructions" : "Dismiss while loading"}
            </button>
          </div>
        </div>
      {/if}
      <div class="preview-content">
        <iframe
          bind:this={iframeRef}
          title={resourceLabel}
          sandbox={uiIframeSandbox}
          allow={uiIframeAllow}
          srcdoc={uiResourceHtml}
        ></iframe>
        {#if uiPreviewExpanded && uiHostViewportMode === "compact"}
          <aside class="compact-preview-info">
            <h4>Compact focus</h4>
            <p>
              Compact viewport is preserved while maximised so you can compare host-side context and
              workflow notes side-by-side.
            </p>
            <div class="meta-grid">
              <div>
                <div class="label">Mode</div>
                <div class="value">{uiHostViewportMode}</div>
              </div>
              <div>
                <div class="label">Size</div>
                <div class="value">{uiCompactWidthPx}x{uiCompactHeightPx}</div>
              </div>
              <div>
                <div class="label">Resource</div>
                <div class="value">{selectedResourceUri || "n/a"}</div>
              </div>
            </div>
            <p class="muted">Use the widget's own controls, then return to the Debug workbench for host diagnostics.</p>
          </aside>
        {/if}
      </div>
    </div>
  {/if}
</div>
