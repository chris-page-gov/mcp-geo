"""Legacy FastAPI stub for the playground UI.

The active playground is the Svelte + Vite app under `playground/`.
Run `npm run dev` in that folder and open http://localhost:5173.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/")
def index():
    return HTMLResponse(
        """
    <!doctype html>
    <html>
    <head>
        <title>MCP Geo Playground (Legacy Stub)</title>
        <style>
            body { font-family: system-ui, sans-serif; margin: 2rem; }
            code { background: #f1f1f1; padding: 0.1rem 0.3rem; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>MCP Geo Playground</h1>
        <p>This FastAPI stub does not serve the Svelte playground UI.</p>
        <p>
            Run <code>npm run dev</code> in <code>playground/</code> and open
            <code>http://localhost:5173</code>.
        </p>
    </body>
    </html>
    """
    )
