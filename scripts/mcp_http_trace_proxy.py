#!/usr/bin/env python3
"""HTTP proxy that logs MCP JSON-RPC traffic.

Usage:
  python scripts/mcp_http_trace_proxy.py \\
    --upstream http://127.0.0.1:8000/mcp \\
    --log logs/mcp-http-trace.jsonl
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse


REDACTION_TOKEN = "[REDACTED]"


def redact(value: Optional[str]) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return REDACTION_TOKEN
    return f"{value[:3]}...{value[-3:]}"


def redact_header(name: str, value: str) -> str:
    if name.lower() != "authorization":
        return value
    if value.lower().startswith("bearer "):
        token = value.split(" ", 1)[1]
        return f"Bearer {redact(token)}"
    return redact(value)


def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    return {k: redact_header(k, v) for k, v in headers.items()}


def parse_json_body(body: bytes) -> Optional[Dict[str, Any]]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def log_record(log_path: Path, record: Dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_fh:
        log_fh.write(json.dumps(record, ensure_ascii=True) + "\n")


def _filtered_response_headers(headers: httpx.Headers) -> Dict[str, str]:
    filtered: Dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in {"content-length", "transfer-encoding", "connection"}:
            continue
        filtered[key] = value
    return filtered


def build_app(upstream_url: str, log_path: Path) -> FastAPI:
    app = FastAPI(title="MCP HTTP Trace Proxy")
    client = httpx.AsyncClient(timeout=None)
    base_url = upstream_url[:-4] if upstream_url.endswith("/mcp") else upstream_url.rstrip("/")

    @app.on_event("shutdown")
    async def _shutdown_client() -> None:
        await client.aclose()

    async def _forward_request(
        request: Request, method: str, url: str, body: Optional[bytes] = None
    ) -> Response:
        headers = dict(request.headers)
        headers.pop("host", None)
        headers.pop("content-length", None)
        record: Dict[str, Any] = {
            "ts": time.time(),
            "direction": "client->upstream",
            "method": method,
            "path": request.url.path,
            "headers": redact_headers(headers),
        }
        if body is not None:
            record["body"] = body.decode("utf-8", errors="replace")
            payload = parse_json_body(body)
            if payload:
                record["json"] = payload
                record["id"] = payload.get("id")
                record["method_name"] = payload.get("method")
        log_record(log_path, record)

        async with client.stream(method, url, headers=headers, content=body) as upstream:
            content_type = upstream.headers.get("content-type", "")
            response_headers = _filtered_response_headers(upstream.headers)

            if content_type.startswith("text/event-stream"):

                async def _stream() -> Iterable[bytes]:
                    async for chunk in upstream.aiter_bytes():
                        log_record(
                            log_path,
                            {
                                "ts": time.time(),
                                "direction": "upstream->client",
                                "status": upstream.status_code,
                                "chunk": chunk.decode("utf-8", errors="replace"),
                            },
                        )
                        yield chunk

                return StreamingResponse(
                    _stream(),
                    status_code=upstream.status_code,
                    headers=response_headers,
                    media_type=content_type,
                )

            body_bytes = await upstream.aread()
            log_record(
                log_path,
                {
                    "ts": time.time(),
                    "direction": "upstream->client",
                    "status": upstream.status_code,
                    "headers": redact_headers(dict(upstream.headers)),
                    "body": body_bytes.decode("utf-8", errors="replace"),
                    "json": parse_json_body(body_bytes),
                },
            )
            return Response(
                content=body_bytes,
                status_code=upstream.status_code,
                headers=response_headers,
                media_type=content_type or None,
            )

    @app.post("/mcp")
    async def proxy_mcp(request: Request) -> Response:
        body = await request.body()
        return await _forward_request(request, "POST", upstream_url, body)

    @app.get("/health")
    async def proxy_health(request: Request) -> Response:
        return await _forward_request(request, "GET", f"{base_url}/health")

    @app.get("/.well-known/mcp-auth")
    async def proxy_auth(request: Request) -> Response:
        return await _forward_request(
            request, "GET", f"{base_url}/.well-known/mcp-auth"
        )

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP HTTP trace proxy")
    parser.add_argument(
        "--upstream",
        default="http://127.0.0.1:8000/mcp",
        help="Upstream MCP endpoint (default: http://127.0.0.1:8000/mcp)",
    )
    parser.add_argument(
        "--log",
        default="logs/mcp-http-trace.jsonl",
        help="Path to JSONL log file",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8899, help="Port to bind to")
    args = parser.parse_args()

    app = build_app(args.upstream, Path(args.log))
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
