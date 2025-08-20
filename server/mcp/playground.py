from fastapi import APIRouter, Request
import time

router = APIRouter()

# In-memory transcript (for demo only, not production)
TOOL_CALL_TRANSCRIPT = []
MAX_TRANSCRIPT = 10

@router.get("/playground/transcript")
def get_transcript():
    return {"transcript": TOOL_CALL_TRANSCRIPT[-MAX_TRANSCRIPT:]}

@router.post("/playground/tool_call")
def record_tool_call(request: Request):
    # This would be called by the playground UI after a tool call
    data = request.json()
    entry = {
        "tool": data.get("tool"),
        "input": data.get("input"),
        "output": data.get("output"),
        "timestamp": time.time()
    }
    TOOL_CALL_TRANSCRIPT.append(entry)
    return {"ok": True}
