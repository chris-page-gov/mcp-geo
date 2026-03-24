import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from server.config import settings
from server.mcp.http_route_auth import apply_auth_headers, authorize_http_route
from server.observability import (
    record_playground_event,
    record_playground_orchestration_request,
    record_playground_tool_call,
)

router = APIRouter()

# In-memory transcript (for demo only, not production)
TOOL_CALL_TRANSCRIPT: list[dict[str, Any]] = []
MAX_TRANSCRIPT = 10
PLAYGROUND_EVENTS: list[dict[str, Any]] = []
MAX_EVENTS = 200


class PlaygroundToolCall(BaseModel):
    tool: str = Field(..., description="Tool name invoked")
    input: Any | None = Field(None, description="Input sent to the tool")
    output: Any | None = Field(None, description="Output returned by the tool")
    sessionId: str | None = Field(None, description="Optional playground session id")
    correlationId: str | None = Field(None, description="Optional correlation id")


class PlaygroundEvent(BaseModel):
    eventType: str = Field(..., description="Event type")
    payload: Any | None = Field(None, description="Event payload")
    context: dict[str, Any] | None = Field(None, description="Additional context")
    sessionId: str | None = Field(None, description="Optional playground session id")
    correlationId: str | None = Field(None, description="Optional correlation id")


def _append_event_log(entry: dict[str, Any]) -> None:
    path = Path(settings.PLAYGROUND_EVENT_LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _latest_evaluation_payload() -> dict[str, Any]:
    candidates = [
        Path("data/evaluation_results_live.json"),
        Path("tests/evaluation/evaluation_results.json"),
    ]
    for path in candidates:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                return {"path": str(path), "data": json.load(handle)}
    return {"path": None, "data": None}


def _filter_by_session(
    rows: list[dict[str, Any]],
    *,
    session_id: str | None,
) -> list[dict[str, Any]]:
    if not isinstance(session_id, str) or not session_id.strip():
        return rows
    return [row for row in rows if row.get("sessionId") == session_id]


def _summarize(values: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in values:
        raw = row.get(key)
        if isinstance(raw, str) and raw.strip():
            counts[raw.strip()] += 1
    return dict(sorted(counts.items()))


@router.get("/playground/transcript")
async def get_transcript(request: Request, response: Response, sessionId: str | None = None):
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    filtered = _filter_by_session(TOOL_CALL_TRANSCRIPT, session_id=sessionId)
    return {"transcript": filtered[-MAX_TRANSCRIPT:]}


@router.post("/playground/tool_call")
async def record_tool_call(request: Request, response: Response):
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    try:
        data_raw = await request.json()
    except (json.JSONDecodeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "Malformed JSON request body",
            },
            headers=auth_headers,
        )
    try:
        model = PlaygroundToolCall(**data_raw)
    except Exception as exc:  # simple validation error path
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": f"Invalid payload: {exc}",
            },
            headers=auth_headers,
        )
    entry = {
        "tool": model.tool,
        "input": model.input,
        "output": model.output,
        "sessionId": model.sessionId,
        "correlationId": model.correlationId,
        "timestamp": time.time(),
    }
    TOOL_CALL_TRANSCRIPT.append(entry)
    if len(TOOL_CALL_TRANSCRIPT) > MAX_TRANSCRIPT * 2:
        del TOOL_CALL_TRANSCRIPT[:-MAX_TRANSCRIPT]
    record_playground_tool_call(model.tool)
    return {"ok": True}


@router.get("/playground/events")
async def list_events(request: Request, response: Response, sessionId: str | None = None):
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    filtered = _filter_by_session(PLAYGROUND_EVENTS, session_id=sessionId)
    return {"events": filtered[-MAX_EVENTS:]}


@router.post("/playground/events")
async def record_event(request: Request, response: Response):
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    try:
        data_raw = await request.json()
    except (json.JSONDecodeError, ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "Malformed JSON request body",
            },
            headers=auth_headers,
        )
    try:
        model = PlaygroundEvent(**data_raw)
    except Exception as exc:  # simple validation error path
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": f"Invalid payload: {exc}",
            },
            headers=auth_headers,
        )
    entry = {
        "eventType": model.eventType,
        "payload": model.payload,
        "context": model.context,
        "sessionId": model.sessionId,
        "correlationId": model.correlationId,
        "timestamp": time.time(),
    }
    PLAYGROUND_EVENTS.append(entry)
    if len(PLAYGROUND_EVENTS) > MAX_EVENTS * 2:
        del PLAYGROUND_EVENTS[:-MAX_EVENTS]
    _append_event_log(entry)
    record_playground_event(model.eventType)
    return {"ok": True}


@router.get("/playground/orchestration")
async def orchestration_summary(request: Request, response: Response, sessionId: str | None = None):
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    record_playground_orchestration_request()
    transcript = _filter_by_session(TOOL_CALL_TRANSCRIPT, session_id=sessionId)
    events = _filter_by_session(PLAYGROUND_EVENTS, session_id=sessionId)
    latest_tool_call_at = transcript[-1]["timestamp"] if transcript else None
    latest_event_at = events[-1]["timestamp"] if events else None
    return {
        "sessionId": sessionId,
        "summary": {
            "toolCallCount": len(transcript),
            "eventCount": len(events),
            "toolCounts": _summarize(transcript, "tool"),
            "eventTypeCounts": _summarize(events, "eventType"),
            "latestToolCallAt": latest_tool_call_at,
            "latestEventAt": latest_event_at,
        },
        "transcript": transcript[-MAX_TRANSCRIPT:],
        "events": events[-MAX_EVENTS:],
        "evaluation": _latest_evaluation_payload(),
    }


@router.delete("/playground/orchestration")
async def reset_orchestration_state(request: Request, response: Response):
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    cleared_tools = len(TOOL_CALL_TRANSCRIPT)
    cleared_events = len(PLAYGROUND_EVENTS)
    TOOL_CALL_TRANSCRIPT.clear()
    PLAYGROUND_EVENTS.clear()
    return {
        "ok": True,
        "cleared": {
            "toolCallCount": cleared_tools,
            "eventCount": cleared_events,
        },
    }


@router.get("/playground/evaluation/latest")
async def latest_evaluation(request: Request, response: Response):
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    return _latest_evaluation_payload()
