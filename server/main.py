import threading
import time
import traceback
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi import Response as FastAPIResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.responses import Response as StarletteResponse

from server import maps_proxy, observability
from server.audit import api as audit_api
from server.logging import configure_logging
from server.mcp import http_transport, playground, resources, tools
from server.security import configured_secrets, mask_in_text

from .config import settings

app = FastAPI(title="MCP Geo Server")
configure_logging()
logger.info("MCP Geo server module loaded")

cors_origins = [
    origin.strip()
    for origin in settings.CORS_ALLOWED_ORIGINS.split(",")
    if origin.strip()
]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.add_middleware(GZipMiddleware, minimum_size=512)

# In-memory rate limit store & metrics (simple; not for multi-process scale)
_rate_lock = threading.Lock()
_rate_counters: dict[tuple[str, str], tuple[int, float]] = {}

# Metrics accumulators
_metrics_lock = threading.Lock()
_requests_total = 0
_rate_limited_total = 0
_latency_buckets = [5, 10, 25, 50, 100, 250, 500, 1000, 2000]
_latency_hist: dict[int, int] = dict.fromkeys(_latency_buckets, 0)
_latency_overflow = 0


def _record_latency(ms: float) -> None:
    global _latency_overflow
    with _metrics_lock:
        for bucket in _latency_buckets:
            if ms <= bucket:
                _latency_hist[bucket] += 1
                break
        else:
            _latency_overflow += 1


def _increment_counter(rate_limited: bool = False) -> None:
    global _requests_total, _rate_limited_total
    with _metrics_lock:
        _requests_total += 1
        if rate_limited:
            _rate_limited_total += 1


def _rate_limit_exempt_prefixes() -> tuple[str, ...]:
    raw = getattr(settings, "RATE_LIMIT_EXEMPT_PATH_PREFIXES", "")
    if not isinstance(raw, str):
        return ()
    return tuple(prefix.strip() for prefix in raw.split(",") if prefix.strip())


def _is_rate_limit_exempt(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in _rate_limit_exempt_prefixes())


def _check_rate_limit(request: Request) -> bool:
    limit = settings.RATE_LIMIT_PER_MIN
    if settings.RATE_LIMIT_BYPASS:
        return True
    if limit <= 0:
        return True
    path = request.url.path
    if _is_rate_limit_exempt(path):
        return True

    client_ip = request.client.host if request.client else "unknown"
    path_key = path.split("/")[1] if "/" in path else path
    key = (client_ip, path_key)
    now = time.time()
    window_start = now // 60
    with _rate_lock:
        count, win = _rate_counters.get(key, (0, window_start))
        if win != window_start:
            count = 0
            win = window_start
        if count >= limit:
            return False
        _rate_counters[key] = (count + 1, win)
    return True


@app.middleware("http")
async def add_correlation_id_and_log(
    request: Request,
    call_next: Callable[[Request], Awaitable[StarletteResponse]],
) -> StarletteResponse:
    correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    start_time = time.time()
    logger.info(
        f"[start] {request.method} {request.url.path} correlation_id={correlation_id}"
    )
    if not _check_rate_limit(request):
        _increment_counter(rate_limited=True)
        return JSONResponse(
            status_code=429,
            content={
                "isError": True,
                "code": "RATE_LIMITED",
                "message": "Rate limit exceeded",
                "correlationId": correlation_id,
            },
        )

    response: StarletteResponse = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    response.headers["x-correlation-id"] = correlation_id
    logger.info(
        "[end] {} {} correlation_id={} status={} time_ms={:.2f}",
        request.method,
        request.url.path,
        correlation_id,
        response.status_code,
        process_time,
    )
    _record_latency(process_time)
    _increment_counter()
    return response


app.include_router(tools.router)
app.include_router(resources.router)
app.include_router(playground.router)
app.include_router(http_transport.router)
app.include_router(maps_proxy.router)
app.include_router(audit_api.router)


@app.get("/metrics")
def metrics() -> FastAPIResponse:
    if not settings.METRICS_ENABLED:
        return JSONResponse(
            status_code=404,
            content={
                "isError": True,
                "code": "NOT_ENABLED",
                "message": "Metrics disabled",
            },
        )

    lines = [
        "# HELP app_requests_total Total HTTP requests",
        "# TYPE app_requests_total counter",
        f"app_requests_total {_requests_total}",
        "# HELP app_rate_limited_total Total rate limited responses",
        "# TYPE app_rate_limited_total counter",
        f"app_rate_limited_total {_rate_limited_total}",
        "# HELP app_request_latency_ms Request latency histogram (ms)",
        "# TYPE app_request_latency_ms histogram",
    ]
    cumulative = 0
    with _metrics_lock:
        for bucket in _latency_buckets:
            cumulative += _latency_hist[bucket]
            lines.append(f'app_request_latency_ms_bucket{{le="{bucket}"}} {cumulative}')
        lines.append(
            f'app_request_latency_ms_bucket{{le="+Inf"}} '
            f'{cumulative + _latency_overflow}'
        )
        lines.append(f"app_request_latency_ms_count {cumulative + _latency_overflow}")
    lines.extend(observability.build_prometheus_lines())
    lines.extend(http_transport.build_prometheus_lines())
    body = "\n".join(lines) + "\n"
    return FastAPIResponse(content=body, media_type="text/plain; version=0.0.4")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "OK"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", None)
    raw_message = str(exc)
    safe_message = mask_in_text(raw_message, configured_secrets(settings))
    tb: str | None = traceback.format_exc()
    if settings.DEBUG_ERRORS:
        logger.error(
            "Unhandled error: {} correlation_id={}\nTraceback:\n{}",
            safe_message,
            correlation_id,
            tb,
        )
    else:
        logger.error("Unhandled error: {} correlation_id={}", safe_message, correlation_id)
        tb = None
    content: dict[str, object] = {
        "isError": True,
        "code": "INTERNAL_ERROR",
        "message": safe_message,
        "correlationId": correlation_id,
    }
    if tb:
        content["traceback"] = tb
    return JSONResponse(status_code=500, content=content)
