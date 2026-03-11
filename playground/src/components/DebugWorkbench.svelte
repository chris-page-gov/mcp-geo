<script>
  export let auditRestLog = [];
  export let bootedAt = "";
  export let buildInfo = { mode: "unknown" };
  export let clearDebugLog = () => {};
  export let clearHistory = () => {};
  export let debugEnabled = false;
  export let debugEntries = [];
  export let debugSnapshotText = "";
  export let hmrLastUpdate = "";
  export let hmrStatus = "disabled";
  export let hmrUpdateCount = 0;
  export let lastErrorAt = "";
  export let lastErrorDetail = null;
  export let lastErrorMessage = "";
  export let lastRequestAt = "";
  export let lastResponseAt = "";
  export let rejectedBridgeEvents = [];
  export let secretAudit = { count: 0, paths: [], truncated: false };
  export let uiIframeSandbox = "allow-scripts";
  export let uiPreviewReady = false;
  export let uiResourceError = "";
  export let uiResourceText = "";
  export let selectedResourceUri = "";
</script>

<section class="grid">
  <div class="card">
    <h2>Runtime</h2>
    <div class="meta-grid debug-meta">
      <div>
        <div class="label">Booted at</div>
        <div class="value">{bootedAt}</div>
      </div>
      <div>
        <div class="label">Build mode</div>
        <div class="value">{buildInfo.mode}</div>
      </div>
      <div>
        <div class="label">HMR status</div>
        <div class="value">{hmrStatus}</div>
      </div>
      <div>
        <div class="label">HMR updates</div>
        <div class="value">{hmrUpdateCount}</div>
      </div>
      <div>
        <div class="label">Last HMR update</div>
        <div class="value">{hmrLastUpdate || "n/a"}</div>
      </div>
      <div>
        <div class="label">Last request</div>
        <div class="value">{lastRequestAt || "n/a"}</div>
      </div>
      <div>
        <div class="label">Last response</div>
        <div class="value">{lastResponseAt || "n/a"}</div>
      </div>
      <div>
        <div class="label">Last error</div>
        <div class="value">{lastErrorAt || "n/a"}</div>
      </div>
    </div>
    <div class="actions">
      <label class="toggle">
        <input type="checkbox" bind:checked={debugEnabled} />
        <span>Enable console debug</span>
      </label>
      <button class="ghost" on:click={clearDebugLog}>Clear debug log</button>
      <button class="ghost" on:click={clearHistory}>Clear request history</button>
    </div>
    {#if lastErrorMessage}
      <div class="error">Last error: {lastErrorMessage}</div>
    {/if}
  </div>

  <div class="card">
    <h2>Secret audit</h2>
    <div class="list-badges">
      {#if secretAudit.count === 0}
        <span class="badge badge-ok">No secrets detected</span>
      {:else}
        <span class="badge badge-warn">{secretAudit.count} potential secrets</span>
      {/if}
    </div>
    {#if secretAudit.count > 0}
      <pre>{JSON.stringify(secretAudit.paths, null, 2)}{secretAudit.truncated ? "\n...truncated" : ""}</pre>
    {/if}
  </div>

  <div class="card">
    <h2>Connection snapshot</h2>
    <pre>{debugSnapshotText}</pre>
    {#if lastErrorDetail}
      <details class="details-block">
        <summary>Last error detail</summary>
        <pre>{JSON.stringify(lastErrorDetail, null, 2)}</pre>
      </details>
    {/if}
  </div>

  <div class="card">
    <h2>Rejected bridge events</h2>
    {#if rejectedBridgeEvents.length === 0}
      <p class="muted">No widget bridge rejections recorded.</p>
    {:else}
      {#each rejectedBridgeEvents as entry}
        <div class="history">
          <strong>{entry.at} · {entry.code}</strong>
          <div class="list-sub">{entry.reason}</div>
          <pre>{JSON.stringify(entry.detail, null, 2)}</pre>
        </div>
      {/each}
    {/if}
  </div>

  <div class="card">
    <h2>Audit REST log</h2>
    {#if auditRestLog.length === 0}
      <p class="muted">No audit REST traffic yet.</p>
    {:else}
      {#each auditRestLog as entry}
        <div class="history">
          <strong>{entry.at} · {entry.method} {entry.path}</strong>
          <div class="list-sub">{entry.status || "pending"}</div>
          <pre>{JSON.stringify(entry.payload, null, 2)}</pre>
        </div>
      {/each}
    {/if}
  </div>

  <div class="card">
    <h2>UI preview diagnostics</h2>
    <div class="meta-grid debug-meta">
      <div>
        <div class="label">Selected UI</div>
        <div class="value">{selectedResourceUri || "n/a"}</div>
      </div>
      <div>
        <div class="label">Preview ready</div>
        <div class="value">{uiPreviewReady ? "yes" : "no"}</div>
      </div>
      <div>
        <div class="label">Sandbox</div>
        <div class="value">{uiIframeSandbox}</div>
      </div>
    </div>
    {#if uiResourceError}
      <div class="error">{uiResourceError}</div>
    {/if}
    <details class="details-block">
      <summary>Raw UI HTML</summary>
      <pre>{uiResourceText || "No UI HTML loaded yet."}</pre>
    </details>
  </div>

  <div class="card">
    <h2>Debug log</h2>
    {#if debugEntries.length === 0}
      <p class="muted">No debug entries yet.</p>
    {:else}
      {#each debugEntries as entry}
        <div class="history">
          <strong>{entry.at} · {entry.level}</strong>
          <div class="list-sub">{entry.message}</div>
          {#if entry.detail}
            <pre>{JSON.stringify(entry.detail, null, 2)}</pre>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</section>
