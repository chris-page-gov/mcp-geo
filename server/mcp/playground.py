import json
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from server.config import settings

router = APIRouter()

# In-memory transcript (for demo only, not production)

TOOL_CALL_TRANSCRIPT: list[dict[str, Any]] = []
MAX_TRANSCRIPT = 10
PLAYGROUND_EVENTS: list[dict[str, Any]] = []
MAX_EVENTS = 200

@router.get("/playground/transcript")
async def get_transcript():
    return {"transcript": TOOL_CALL_TRANSCRIPT[-MAX_TRANSCRIPT:]}

class PlaygroundToolCall(BaseModel):
    tool: str = Field(..., description="Tool name invoked")
    input: Any | None = Field(None, description="Input sent to the tool")
    output: Any | None = Field(None, description="Output returned by the tool")


@router.post("/playground/tool_call")
async def record_tool_call(request: Request):
    data_raw = await request.json()
    try:
        model = PlaygroundToolCall(**data_raw)
    except Exception as exc:  # simple validation error path
        return {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": f"Invalid payload: {exc}",
        }
    entry = {
        "tool": model.tool,
        "input": model.input,
        "output": model.output,
        "timestamp": time.time(),
    }
    TOOL_CALL_TRANSCRIPT.append(entry)
    if len(TOOL_CALL_TRANSCRIPT) > MAX_TRANSCRIPT * 2:
        # prune oldest beyond a simple buffer
        del TOOL_CALL_TRANSCRIPT[:-MAX_TRANSCRIPT]
    return {"ok": True}


class PlaygroundEvent(BaseModel):
    eventType: str = Field(..., description="Event type")
    payload: Any | None = Field(None, description="Event payload")
    context: dict[str, Any] | None = Field(None, description="Additional context")


def _append_event_log(entry: dict[str, Any]) -> None:
    path = Path(settings.PLAYGROUND_EVENT_LOG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


@router.get("/playground/events")
async def list_events():
    return {"events": PLAYGROUND_EVENTS[-MAX_EVENTS:]}


@router.post("/playground/events")
async def record_event(request: Request):
    data_raw = await request.json()
    try:
        model = PlaygroundEvent(**data_raw)
    except Exception as exc:  # simple validation error path
        return {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": f"Invalid payload: {exc}",
        }
    entry = {
        "eventType": model.eventType,
        "payload": model.payload,
        "context": model.context,
        "timestamp": time.time(),
    }
    PLAYGROUND_EVENTS.append(entry)
    if len(PLAYGROUND_EVENTS) > MAX_EVENTS * 2:
        del PLAYGROUND_EVENTS[:-MAX_EVENTS]
    _append_event_log(entry)
    return {"ok": True}


@router.get("/playground/evaluation/latest")
async def latest_evaluation():
    candidates = [
        Path("data/evaluation_results_live.json"),
        Path("tests/evaluation/evaluation_results.json"),
    ]
    for path in candidates:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                return {"path": str(path), "data": json.load(handle)}
    return {"path": None, "data": None}
