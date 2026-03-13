<script>
  export let auditError = "";
  export let auditForm = {
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
  export let auditPacks = [];
  export let auditResult = null;
  export let auditSelectedPack = null;
  export let onCreatePack = () => {};
  export let onDownloadBundle = () => {};
  export let onDownloadHash = () => {};
  export let onNormaliseSession = () => {};
  export let onRedactPack = () => {};
  export let onRefreshPacks = () => {};
  export let onSelectPack = () => {};
  export let onToggleLegalHold = () => {};
  export let onVerifyPack = () => {};
  export let status = "disconnected";
</script>

<section class="split">
  <div class="pane">
    <div class="pane-header">
      <div class="pane-title">Audit / FOI packs</div>
      <div class="actions">
        <button class="ghost" on:click={onRefreshPacks} disabled={status !== "connected"}>Refresh</button>
      </div>
    </div>
    <div class="pane-body">
      {#if auditPacks.length === 0}
        <p class="muted">No packs listed yet. Connect to the server and refresh or build one from a session.</p>
      {:else}
        {#each auditPacks as pack}
          <button
            class:selected={auditSelectedPack?.packId === pack.packId}
            class="list-item"
            on:click={() => onSelectPack(pack.packId)}
          >
            <div class="list-title">{pack.packId}</div>
            <div class="list-sub">{pack.scopeType || "conversation"} · {pack.retentionClass || "default_operational"}</div>
            <div class="list-badges">
              <span class="badge badge-ghost">{pack.legalHold ? "legal hold" : "standard"}</span>
              <span class="badge badge-ghost">{pack.disclosures?.length || 0} disclosures</span>
            </div>
          </button>
        {/each}
      {/if}
    </div>
  </div>

  <div class="pane">
    <div class="pane-header alt">
      <div class="pane-title">Pack operations</div>
      <div class="actions">
        <button class="ghost" on:click={onNormaliseSession}>Normalise session</button>
        <button class="primary" on:click={onCreatePack}>Build pack</button>
      </div>
    </div>
    <div class="pane-body">
      <div class="detail-block">
        <h3>Build from session</h3>
        <div class="form-grid">
          <label>
            Session directory
            <input type="text" bind:value={auditForm.sessionDir} placeholder="/path/to/session" />
          </label>
          <label>
            Output root (optional)
            <input type="text" bind:value={auditForm.outputRoot} placeholder="/path/to/output/root" />
          </label>
          <label>
            Scope type
            <select bind:value={auditForm.scopeType}>
              <option value="conversation">conversation</option>
              <option value="episode">episode</option>
              <option value="snapshot">snapshot</option>
            </select>
          </label>
          <label>
            Retention class
            <input type="text" bind:value={auditForm.retentionClass} />
          </label>
          <label>
            Episode ID (optional)
            <input type="text" bind:value={auditForm.episodeId} />
          </label>
          <label>
            Episode title (optional)
            <input type="text" bind:value={auditForm.episodeTitle} />
          </label>
          <label>
            Episode start sequence
            <input type="number" bind:value={auditForm.episodeStartSequence} />
          </label>
          <label>
            Episode end sequence
            <input type="number" bind:value={auditForm.episodeEndSequence} />
          </label>
        </div>
        <label class="toggle">
          <input type="checkbox" bind:checked={auditForm.legalHold} />
          <span>Apply legal hold on creation</span>
        </label>
      </div>

      {#if auditSelectedPack}
        <div class="detail-block">
          <h3>{auditSelectedPack.packId}</h3>
          <div class="actions">
            <button class="ghost" on:click={onVerifyPack}>Verify integrity</button>
            <button class="ghost" on:click={() => onRedactPack("foi_redacted")}>FOI redact</button>
            <button class="ghost" on:click={onToggleLegalHold}>
              {auditSelectedPack.legalHold ? "Release legal hold" : "Apply legal hold"}
            </button>
            <button class="ghost" on:click={onDownloadBundle}>Download bundle</button>
            <button class="ghost" on:click={onDownloadHash}>Download hash</button>
          </div>
          <details class="details-block" open>
            <summary>Pack detail</summary>
            <pre>{JSON.stringify(auditSelectedPack, null, 2)}</pre>
          </details>
        </div>
      {/if}

      {#if auditError}
        <div class="error">{auditError}</div>
      {/if}

      {#if auditResult}
        <details class="details-block" open>
          <summary>Last audit response</summary>
          <pre>{JSON.stringify(auditResult, null, 2)}</pre>
        </details>
      {/if}
    </div>
  </div>
</section>

<style>
  .form-grid {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  }
</style>
