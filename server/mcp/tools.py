from fastapi import APIRouter

router = APIRouter()


@router.get("/tools/list")
def list_tools(limit: int = 10, page: int = 1):
    # Pagination stub
    tools = ["placeholder_tool"]
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(tools) else None
    return {
        "tools": tools[start:end],
        "nextPageToken": next_page_token
    }


@router.post("/tools/call")
def call_tool():
    # Uniform error model example
    try:
        return {"result": "Tool call stub"}
    except Exception as exc:
        return {"isError": True, "code": "TOOL_ERROR", "message": str(exc)}
