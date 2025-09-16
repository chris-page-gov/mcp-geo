from fastapi import APIRouter, Request
import time
from pydantic import BaseModel, Field
from typing import Any

router = APIRouter()

# In-memory transcript (for demo only, not production)
TOOL_CALL_TRANSCRIPT = []
MAX_TRANSCRIPT = 10

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
