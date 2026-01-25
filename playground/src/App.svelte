<script>
  import { Client } from "@modelcontextprotocol/sdk/client/index.js";
  import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
  import {
    CompatibilityCallToolResultSchema,
    ListResourcesResultSchema,
    ListResourceTemplatesResultSchema,
    ListToolsResultSchema
  } from "@modelcontextprotocol/sdk/types.js";

  let serverUrl = "http://localhost:8000/mcp";
  let playgroundUrl = "http://localhost:8000/playground";
  let status = "disconnected";
  let error = "";
  let client = null;
  let transport = null;
  let tools = [];
  let resources = [];
  let resourceTemplates = [];
  let toolFilter = "";
  let toolName = "os_mcp_descriptor";
  let toolArgs = '{\n  "tool": "os_mcp.descriptor"\n}';
  let toolResult = "";
  let promptText = "";
  let promptContext = "";
  let descriptor = null;
  let history = [];

  const recordHistory = (entry) => {
    history = [entry, ...history].slice(0, 50);
  };

  const sendRequest = async (request, schema) => {
    if (!client) {
      throw new Error("MCP client not connected");
    }
    const response = await client.request(request, schema);
    recordHistory({ request, response, at: new Date().toISOString() });
    return response;
  };

  const connect = async () => {
    error = "";
    status = "connecting";
    try {
      client = new Client(
        { name: "mcp-geo-playground", version: "0.1.0" },
        { capabilities: { tools: {}, resources: {} } }
      );
      transport = new StreamableHTTPClientTransport(new URL(serverUrl), {});
      await client.connect(transport);
      status = "connected";
      await refreshLists();
      await fetchDescriptor();
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
    descriptor = response;
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

  const filteredTools = tools.filter((tool) => {
    if (!toolFilter) {
      return true;
    }
    return tool.name.toLowerCase().includes(toolFilter.toLowerCase());
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
      <h1>Test tools, log prompts, and trace MCP behavior in one place.</h1>
      <p class="sub">Built on the MCP TypeScript client with live server diagnostics.</p>
    </div>
    <div class="status">
      <span class={`dot ${status}`}></span>
      <div>
        <div class="label">Status</div>
        <div class="value">{status}</div>
      </div>
    </div>
  </header>

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
      <h2>Descriptor</h2>
      {#if descriptor}
        <pre>{JSON.stringify(descriptor, null, 2)}</pre>
      {:else}
        <p class="muted">Connect to fetch server metadata.</p>
      {/if}
    </div>
  </section>

  <section class="grid">
    <div class="card">
      <h2>Tools</h2>
      <input class="search" type="text" placeholder="Filter tools" bind:value={toolFilter} />
      <div class="scroll">
        {#each filteredTools as tool}
          <button class="tool" on:click={() => (toolName = tool.name)}>
            <span>{tool.name}</span>
            <small>{tool.description}</small>
          </button>
        {/each}
      </div>
    </div>

    <div class="card">
      <h2>Tool Call</h2>
      <label>
        Tool name
        <input type="text" bind:value={toolName} />
      </label>
      <label>
        Arguments (JSON)
        <textarea rows="8" bind:value={toolArgs}></textarea>
      </label>
      <div class="actions">
        <button class="primary" on:click={callTool} disabled={status !== "connected"}>
          Run Tool
        </button>
      </div>
      {#if toolResult}
        <pre>{toolResult}</pre>
      {/if}
    </div>
  </section>

  <section class="grid">
    <div class="card">
      <h2>Resources</h2>
      <div class="scroll">
        {#each resources as resource}
          <div class="resource">
            <strong>{resource.name}</strong>
            <span>{resource.uri}</span>
          </div>
        {/each}
      </div>
    </div>

    <div class="card">
      <h2>Resource Templates</h2>
      <div class="scroll">
        {#if resourceTemplates.length === 0}
          <p class="muted">No templates advertised.</p>
        {:else}
          {#each resourceTemplates as template}
            <div class="resource">
              <strong>{template.name}</strong>
              <span>{template.uriTemplate}</span>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  </section>

  <section class="grid">
    <div class="card">
      <h2>Prompt Capture</h2>
      <label>
        Prompt
        <textarea rows="5" bind:value={promptText}></textarea>
      </label>
      <label>
        Context (optional)
        <input type="text" bind:value={promptContext} />
      </label>
      <div class="actions">
        <button class="primary" on:click={logPrompt}>Log Prompt</button>
      </div>
      <p class="muted">Use this for capturing user prompts before tooling runs.</p>
    </div>

    <div class="card">
      <h2>Request History</h2>
      <div class="scroll">
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
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: "Space Grotesk", sans-serif;
    background: radial-gradient(circle at top, #f6f4ef 0%, #efe7dc 40%, #e4d9cb 100%);
    color: #1c1c1c;
  }

  .page {
    padding: 32px;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .hero {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 24px;
    background: #0f2a2d;
    color: #f7f4ef;
    padding: 28px;
    border-radius: 20px;
    box-shadow: 0 12px 30px rgba(15, 42, 45, 0.2);
  }

  .hero h1 {
    margin: 8px 0 12px;
    font-size: 2rem;
    line-height: 1.2;
  }

  .eyebrow {
    font-size: 0.8rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #7dd3c7;
  }

  .sub {
    font-family: "Spectral", serif;
    max-width: 420px;
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
    font-size: 1.1rem;
    font-weight: 600;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
  }

  .card {
    background: #fdfbf7;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 8px 20px rgba(15, 42, 45, 0.08);
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

  .search {
    width: 100%;
  }

  .scroll {
    max-height: 280px;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .tool {
    text-align: left;
    background: #f0f5f4;
    border-radius: 10px;
    padding: 10px;
    border: 1px solid transparent;
  }

  .tool:hover {
    border-color: #2e7d6b;
  }

  .tool small {
    display: block;
    color: #567;
  }

  .resource {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 0.85rem;
  }

  .resource span {
    color: #6b6b6b;
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

  @media (max-width: 800px) {
    .hero {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>
