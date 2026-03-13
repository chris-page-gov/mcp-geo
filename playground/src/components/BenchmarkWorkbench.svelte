<script>
  export let benchmarkFilterId = "";
  export let benchmarkFilterSupport = "all";
  export let benchmarkFilterToolFamily = "all";
  export let benchmarkLiveView = null;
  export let benchmarkReferenceView = null;
  export let filteredBenchmarks = [];
  export let onOpenWidget = () => {};
  export let onPrefillTool = () => {};
  export let onSelectScenario = () => {};
  export let onViewLatestEvidence = () => {};
  export let selectedBenchmark = null;
  export let status = "disconnected";
</script>

<section class="grid">
  <div class="card">
    <h2>Benchmark scenarios</h2>
    <div class="form-grid">
      <label>
        Scenario ID
        <input type="text" bind:value={benchmarkFilterId} placeholder="SG03" />
      </label>
      <label>
        Support level
        <select bind:value={benchmarkFilterSupport}>
          <option value="all">all</option>
          <option value="full">full</option>
          <option value="partial">partial</option>
          <option value="blocked">blocked</option>
        </select>
      </label>
      <label>
        Tool family
        <select bind:value={benchmarkFilterToolFamily}>
          <option value="all">all</option>
          <option value="routing">routing</option>
          <option value="apps">apps</option>
          <option value="places">places</option>
          <option value="features">features</option>
          <option value="admin">admin</option>
          <option value="other">other</option>
        </select>
      </label>
    </div>
    <div class="benchmark-list">
      {#each filteredBenchmarks as scenario}
        <button
          class:selected={selectedBenchmark?.id === scenario.id}
          class={`list-item ${scenario.supportLevel === "blocked" ? "blocked" : ""}`}
          on:click={() => onSelectScenario(scenario.id)}
        >
          <div class="list-title">{scenario.id} · {scenario.title}</div>
          <div class="list-sub">{scenario.comparatorSummary}</div>
          <div class="list-badges">
            <span class="badge badge-ghost">{scenario.supportLevel}</span>
            <span class="badge badge-ghost">{scenario.demo?.primaryTool || "n/a"}</span>
            {#if scenario.demo?.widget}
              <span class="badge badge-ghost">widget</span>
            {/if}
          </div>
        </button>
      {/each}
    </div>
  </div>

  <div class="card">
    <h2>Reference / live / diff</h2>
    {#if selectedBenchmark}
      <div class="actions">
        <button class="ghost" on:click={onPrefillTool} disabled={status !== "connected"}>
          Prefill tool
        </button>
        <button class="ghost" on:click={onOpenWidget} disabled={!selectedBenchmark.demo?.widget || status !== "connected"}>
          Open widget
        </button>
        <button class="primary" on:click={onViewLatestEvidence}>
          View latest evidence
        </button>
      </div>
      <div class="meta-grid">
        <div>
          <div class="label">Support level</div>
          <div class="value">{selectedBenchmark.supportLevel}</div>
        </div>
        <div>
          <div class="label">Demo mode</div>
          <div class="value">{selectedBenchmark.demo?.mode || "guided"}</div>
        </div>
        <div>
          <div class="label">Primary tool</div>
          <div class="value">{selectedBenchmark.demo?.primaryTool || "n/a"}</div>
        </div>
      </div>
      {#if selectedBenchmark.supportLevel === "blocked"}
        <div class="info-card blocked-card">
          <h4>Evidence-first blocked scenario</h4>
          <p>
            This scenario remains blocked in MCP-Geo. The workbench shows fixtures and live evidence rather than inventing a runnable flow.
          </p>
        </div>
      {/if}
      <details class="details-block" open>
        <summary>Scenario demo contract</summary>
        <pre>{JSON.stringify(selectedBenchmark.demo, null, 2)}</pre>
      </details>
      <details class="details-block" open>
        <summary>Reference output</summary>
        <pre>{JSON.stringify(benchmarkReferenceView, null, 2)}</pre>
      </details>
      <details class="details-block" open>
        <summary>Latest live evidence</summary>
        <pre>{JSON.stringify(benchmarkLiveView, null, 2)}</pre>
      </details>
    {:else}
      <p class="muted">Select a benchmark scenario to inspect reference and live evidence.</p>
    {/if}
  </div>
</section>

<style>
  .form-grid {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  }

  .benchmark-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 12px;
    max-height: 65vh;
    overflow: auto;
  }

  .blocked {
    border-color: rgba(184, 75, 75, 0.4);
    background: #fff4f1;
  }

  .blocked-card {
    border-color: rgba(184, 75, 75, 0.25);
    background: #fff5f3;
  }
</style>
