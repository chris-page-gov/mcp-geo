Facts about MCP Apps support (ext-apps vs ChatGPT Apps)
	•	MCP Apps (ext-apps) is an optional extension to MCP: servers declare ui://… resources with mimeType: text/html;profile=mcp-app, and hosts may or may not render them. The spec explicitly notes hosts differ and UI support can’t be assumed.  ￼
	•	ChatGPT “Apps” (OpenAI’s Apps SDK) expects ui://… resources with mimeType: text/html+skybridge and tool metadata that points to the template via openai/outputTemplate.  ￼
	•	Your map-geo server emits both UI resource variants: ui://mcp-geo/geography-selector (mcp-app) and ui://mcp-geo/geography-selector.html (skybridge).  ￼
	•	goose Desktop documents experimental MCP Apps rendering (useful as a sanity check client).  ￼

So: if you want an “AI client that renders MCP Apps”, ChatGPT (Apps SDK / MCP apps in ChatGPT) is the primary target, and goose is a convenient second reference implementation.

⸻

What OpenAI clients can you target (and what “Mac Desktop” currently means)

What OpenAI documents clearly today
	•	Developer mode in ChatGPT is the supported way to connect your own MCP server to ChatGPT for testing. It’s described as a beta feature providing full MCP client support.  ￼
	•	The Apps SDK docs show how to connect from ChatGPT: enable developer mode, create a connector pointing at your server’s public /mcp endpoint over HTTPS, then add it in a chat via the + → More menu.  ￼
	•	OpenAI’s “Connect from ChatGPT” guide explicitly states: once linked on ChatGPT web, it becomes available on ChatGPT mobile apps.  ￼

What the macOS ChatGPT app docs cover (separate feature)
	•	“Work with Apps on macOS” is about ChatGPT reading/editing content in local apps (VS Code, terminals, Notes, etc.), not MCP Apps rendering.  ￼

Practical takeaway: use ChatGPT web as the “source of truth” for enabling developer mode + creating the connector. Then check whether the connector appears in the macOS app’s chat “+ / More” tool picker; if it doesn’t, you still have a guaranteed path via ChatGPT web (and mobile).  ￼

⸻

Non-negotiable requirement for ChatGPT: your MCP server must be reachable over HTTPS

OpenAI’s guidance for ChatGPT connection assumes your MCP server is reachable via an HTTPS URL (for local dev, via ngrok/Cloudflare Tunnel).  ￼
For OpenAI APIs, remote MCP must support Streamable HTTP or HTTP/SSE transports.  ￼

That means a stdio-only server (typical Claude Desktop setup) needs a bridge (or a native HTTP transport) to work with ChatGPT developer mode.

⸻

Implementation plan: “map-geo + proxy logging” to OpenAI (ChatGPT) clients

Architecture (simple, robust, debuggable)
	1.	map-geo MCP server (native `/mcp` Streamable HTTP + existing /tools/* + /resources/*)
	2.	MCP HTTP trace proxy in front of it (for ChatGPT traffic capture)
	3.	Public HTTPS tunnel for local demos (ngrok)  ￼
	4.	Validation harness: MCP Inspector (fastest way to debug before ChatGPT)  ￼
	5.	ChatGPT developer mode connector pointing to https://…/mcp  ￼

Why this works well
	•	Inspector gives you immediate visibility into tool schemas, raw requests/responses, and UI resources.  ￼
	•	Your proxy captures the same traffic ChatGPT will send, which is critical for troubleshooting.

⸻

Tutorial (novice-friendly) that you can hand to someone and expect it to work

Below is the “golden path” I’d recommend you publish as your demo tutorial. It avoids repo internals where possible and relies on official user-guide level steps for ChatGPT + standard MCP tooling.

Part A — One-time setup on a Mac (novice steps)
	1.	Install ChatGPT

	•	Install ChatGPT for macOS (OpenAI’s mac app install flow is documented here).  ￼

	2.	Ensure your default browser is Atlas

	•	This matters because OAuth / login flows will open in your default browser during “Connect”. (This is macOS System Settings → Desktop & Dock → Default web browser.)

	3.	Install Node.js (if you’ll run MCP Inspector or your server locally)

	•	MCP Inspector is run via npx …@latest in the docs.  ￼

⸻

Part B — Run the server locally (with logging proxy) and expose it over HTTPS

Goal: end up with a public URL like https://something.example/mcp.
	1.	Start map-geo behind the HTTP trace proxy

	•	Start `uvicorn server.main:app --reload` and run the HTTP trace proxy:
	  `python scripts/mcp_http_trace_proxy.py --upstream http://127.0.0.1:8000/mcp`
	•	Sanity check: your logs should show tools/list and at least one tools/call when tested.

	2.	Expose it publicly

	•	Use either ngrok or Cloudflare Tunnel to expose your local /mcp endpoint to the public internet. OpenAI explicitly suggests these for local development.  ￼
	•	Devcontainer note: run the server + proxy inside the container (ports 8000/8899 forwarded), then run ngrok on the host targeting `http://127.0.0.1:8899/mcp`.

	3.	Verify in MCP Inspector (do this before ChatGPT)

	•	Run MCP Inspector and point it at your public (or local) /mcp URL. The Apps SDK testing guide recommends this as the fastest debugging workflow.  ￼
	•	In Inspector:
	•	Click List Tools
	•	Call the tool that should return a UI (e.g. your geography selector / route planner)
	•	Confirm you see a resource with mimeType: text/html;profile=mcp-app (ext-apps) and text/html+skybridge (ChatGPT Apps), with matching ui:// URIs.  ￼

If Inspector can’t see the tools: fix this before touching ChatGPT (it will be faster).

⸻

Part C — Connect it to ChatGPT (the key “MCP Apps render” step)
	1.	Enable Developer Mode in ChatGPT

	•	OpenAI documents the toggle and that it provides full MCP client support.  ￼

	2.	Create a connector / app pointing at your server

	•	In ChatGPT, go to Settings → Apps & Connectors → Advanced settings → Developer mode, then create a connector with your public /mcp URL over HTTPS.  ￼

	3.	Add the connector to a chat

	•	Start a new chat → press + → More → select your connector.  ￼

	4.	Trigger a UI tool

	•	Ask ChatGPT to open your geography selector / route planner (examples below).
	•	If ChatGPT supports rendering for that UI resource, you should see the embedded interface rather than only JSON/text.

⸻

“Showcase script”: prompts that demonstrate map-geo end-to-end

These are written so a novice can copy/paste them in order. They’re also designed to exercise both search and UI rendering.

1) Prove the connector is live
	•	“List the tools available in the map-geo app and tell me what each one does in one line.”

2) Demonstrate the Geography Selector UI (MCP App)
	•	“Open the geography selector for Coventry and let me choose an area. Then summarise what I selected.”

(Your trace shows a geography selector UI resource exists; Claude didn’t render it, which is exactly why this is the demo moment in ChatGPT.)  ￼

3) Demonstrate place search (text → map)
	•	“Search for ‘Broadgate Coventry’ and show the top 5 results with coordinates. Then render a map centred on the best match.”

4) Demonstrate “postcode → places”
	•	“Find places for postcode CV1 1AA, then render a map that includes all returned points.”

5) Demonstrate route planner UI (MCP App)
	•	“Open the route planner. Set start to Coventry station and end to Warwick Castle, then show the route summary.”

(If your server exposes a route-planner MCP App similar to the selector, this is the second “wow” moment. Your tool naming suggests this exists.)  ￼

6) Demonstrate “developer-grade” capability (vector tiles / metadata)
	•	“Give me the vector tile descriptor for the current map view and explain how to use it in one paragraph.”

⸻

Troubleshooting (the small set of failures novices actually hit)

1) “ChatGPT can’t connect to the server”
	•	Confirm the connector URL is HTTPS and ends in /mcp.  ￼
	•	Confirm your server supports a remote transport (Streamable HTTP or HTTP/SSE).  ￼
	•	Use MCP Inspector to verify the server responds to List Tools.  ￼

2) “Tools appear, but the UI doesn’t render”
	•	Confirm the tool response points to a ui://… resource and the resource is text/html;profile=mcp-app for ext-apps clients or text/html+skybridge for ChatGPT Apps.  ￼
	•	If it renders in Inspector but not ChatGPT, treat it as a client support gap (MCP Apps is optional per spec).  ￼

3) “Claude Desktop works, ChatGPT doesn’t”
	•	That’s expected if Claude is using stdio and ChatGPT needs remote HTTPS.  ￼

⸻

What I need from you to make this tutorial “map-geo specific” rather than generic

Right now I can’t fetch your GitHub branch contents (your URL returns 404 via my web fetch), so I can’t quote your exact run commands, ports, or scripts. If you paste (or upload) just these two files from the sota-mcp branch, I’ll rewrite the tutorial with exact commands and a “copy/paste” quickstart:
	1.	README.md (or whichever file contains your install/run steps)
	2.	package.json (or pyproject.toml / requirements.txt if it’s Python)

I’ll then:
	•	produce a single novice handout with “do this, see that” steps,
	•	include a known-good expected output at each step (Inspector screenshots checklist),
	•	and tailor the demo prompts to every tool your server advertises (including your MCP Apps widgets).
