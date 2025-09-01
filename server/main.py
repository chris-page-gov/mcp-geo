
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger
import uuid
import time

from .config import settings
from server.mcp import tools
from server.mcp import resources
from server.mcp import playground


app = FastAPI(title="MCP Geo Server")

# Middleware for correlation ID and request logging
@app.middleware("http")
async def add_correlation_id_and_log(request: Request, call_next):
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start_time = time.time()
    logger.info(f"[start] {request.method} {request.url.path} correlation_id={correlation_id}")
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["x-correlation-id"] = correlation_id
    logger.info(f"[end] {request.method} {request.url.path} correlation_id={correlation_id} status={response.status_code} time_ms={process_time:.2f}")
    return response
app.include_router(tools.router)
app.include_router(resources.router)
app.include_router(playground.router)

# Health check endpoint
@app.get("/healthz")
def healthz():
    return {"status": "OK"}



# Error handler for uniform error model with PII-safe redaction
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    correlation_id = getattr(request.state, "correlation_id", None)
    safe_message = str(exc).replace(settings.OS_API_KEY, "[REDACTED]") if hasattr(settings, "OS_API_KEY") else str(exc)
    logger.error(f"Unhandled error: {safe_message} correlation_id={correlation_id}")
    return JSONResponse(
        status_code=500,
        content={"isError": True, "code": "INTERNAL_ERROR", "message": safe_message, "correlationId": correlation_id},
    )
