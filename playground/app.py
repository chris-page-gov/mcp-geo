from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def index():
    return HTMLResponse("""
    <html>
    <head><title>MCP Playground</title></head>
    <body>
        <h1>MCP Playground</h1>
        <form action="/chat" method="post">
            <input name="message" placeholder="Type a message..." />
            <button type="submit">Send</button>
        </form>
    </body>
    </html>
    """)
