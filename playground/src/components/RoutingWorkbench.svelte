<script>
  import UiPreviewPanel from "./UiPreviewPanel.svelte";

  export let compactHeightMax = 900;
  export let compactHeightMin = 360;
  export let compactWidthMax = 520;
  export let compactWidthMin = 280;
  export let descriptorState = null;
  export let onCompactHeightInput = () => {};
  export let onCompactWidthInput = () => {};
  export let onDismissUiInstructions = () => {};
  export let onLoadPreview = () => {};
  export let onOpenWidget = () => {};
  export let onPrefillTool = () => {};
  export let onRunDemo = () => {};
  export let onSelectScenario = () => {};
  export let onTogglePreview = () => {};
  export let onViewportModeChange = () => {};
  export let routingResult = null;
  export let routeScenarioId = "";
  export let routeScenarios = [];
  export let status = "disconnected";
  export let uiCompactHeight = 500;
  export let uiCompactHeightPx = 500;
  export let uiCompactWidth = 320;
  export let uiCompactWidthPx = 320;
  export let uiHostViewportMode = "auto";
  export let uiIframe = null;
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

  $: selectedScenario =
    routeScenarios.find((scenario) => scenario.id === routeScenarioId) || routeScenarios[0] || null;
</script>

<section class="split">
  <div class="pane">
    <div class="pane-header">
      <div class="pane-title">Routing scenarios</div>
      <span class="badge">{routeScenarios.length} seeded demos</span>
    </div>
    <div class="pane-body">
      {#each routeScenarios as scenario}
        <button
          class:selected={selectedScenario?.id === scenario.id}
          class="list-item"
          on:click={() => onSelectScenario(scenario.id)}
        >
          <div class="list-title">{scenario.id} · {scenario.title}</div>
          <div class="list-sub">{scenario.comparatorSummary}</div>
          <div class="list-badges">
            <span class="badge badge-ghost">{scenario.supportLevel}</span>
            <span class="badge badge-ghost">{scenario.demo?.primaryTool || "n/a"}</span>
          </div>
        </button>
      {/each}
    </div>
  </div>

  <div class="pane">
    <div class="pane-header alt">
      <div class="pane-title">Route planner demo</div>
      <div class="actions">
        <button class="ghost" on:click={onPrefillTool} disabled={!selectedScenario || status !== "connected"}>
          Prefill tool
        </button>
        <button class="ghost" on:click={onOpenWidget} disabled={!selectedScenario || status !== "connected"}>
          Open widget
        </button>
        <button class="primary" on:click={onRunDemo} disabled={!selectedScenario || status !== "connected"}>
          Load demo guidance
        </button>
      </div>
    </div>
    <div class="pane-body">
      {#if selectedScenario}
        <div class="detail-block">
          <h3>{selectedScenario.title}</h3>
          <p class="muted">{selectedScenario.comparatorSummary}</p>
          <div class="meta-grid">
            <div>
              <div class="label">Support level</div>
              <div class="value">{selectedScenario.supportLevel}</div>
            </div>
            <div>
              <div class="label">Demo tool</div>
              <div class="value">{selectedScenario.demo?.primaryTool || "n/a"}</div>
            </div>
            <div>
              <div class="label">Widget</div>
              <div class="value">{selectedScenario.demo?.widget || "none"}</div>
            </div>
          </div>
          {#if selectedScenario.demo?.fixtureRefs?.length}
            <details class="details-block">
              <summary>Fixture refs</summary>
              <pre>{JSON.stringify(selectedScenario.demo.fixtureRefs, null, 2)}</pre>
            </details>
          {/if}
          {#if descriptorState}
            <details class="details-block">
              <summary>Route descriptor state</summary>
              <pre>{JSON.stringify(descriptorState, null, 2)}</pre>
            </details>
          {/if}
          {#if routingResult}
            <details class="details-block" open>
              <summary>Last routing payload</summary>
              <pre>{JSON.stringify(routingResult, null, 2)}</pre>
            </details>
          {/if}
        </div>
      {:else}
        <p class="muted">No routing scenarios loaded yet.</p>
      {/if}

      <UiPreviewPanel
        bind:iframeRef={uiIframe}
        compactHeightMax={compactHeightMax}
        compactHeightMin={compactHeightMin}
        compactWidthMax={compactWidthMax}
        compactWidthMin={compactWidthMin}
        onCompactHeightInput={onCompactHeightInput}
        onCompactWidthInput={onCompactWidthInput}
        onDismissInstructions={onDismissUiInstructions}
        onLoad={onLoadPreview}
        onTogglePreview={onTogglePreview}
        onViewportModeChange={onViewportModeChange}
        resourceLabel="Route planner preview"
        selectedResourceUri="ui://mcp-geo/route-planner"
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
    </div>
  </div>
</section>
