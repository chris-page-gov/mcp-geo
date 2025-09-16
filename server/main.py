import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from server.mcp import playground, resources, tools
from server.security import mask_in_text

from .config import settings

app = FastAPI(title="MCP Geo Server")
print("[DEBUG] server/main.py loaded", flush=True)

# Middleware for correlation ID and request logging
@app.middleware("http")
async def add_correlation_id_and_log(request: Request, call_next):
    correlation_id = (
        request.headers.get("x-correlation-id") or str(uuid.uuid4())
    )
    request.state.correlation_id = correlation_id
    start_time = time.time()
    logger.info(
        f"[start] {request.method} {request.url.path} correlation_id={correlation_id}"
    )
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["x-correlation-id"] = correlation_id
    logger.info(
        "[end] %s %s correlation_id=%s status=%s time_ms=%.2f",
        request.method,
        request.url.path,
        correlation_id,
        response.status_code,
        process_time,
    )
    return response
app.include_router(tools.router)
app.include_router(resources.router)
app.include_router(playground.router)

# Health check endpoint
@app.get("/healthz")
def healthz():
    return {"status": "OK"}



# Error handler for uniform error model with optional traceback (DEBUG_ERRORS)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    import traceback
    correlation_id = getattr(request.state, "correlation_id", None)
    raw_message = str(exc)
    safe_message = mask_in_text(
        raw_message, [getattr(settings, "OS_API_KEY", "")]
    )
    tb: str | None = traceback.format_exc()
    if settings.DEBUG_ERRORS:
        logger.error(
            "Unhandled error: %s correlation_id=%s\nTraceback:\n%s",
            safe_message,
            correlation_id,
            tb,
        )
    else:
        logger.error(
            "Unhandled error: %s correlation_id=%s", safe_message, correlation_id
        )
        tb = None
    content = {
        "isError": True,
        "code": "INTERNAL_ERROR",
        "message": safe_message,
        "correlationId": correlation_id,
    }
    if tb:
        content["traceback"] = tb
    return JSONResponse(status_code=500, content=content)
