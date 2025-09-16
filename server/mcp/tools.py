
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from tools.registry import get, list_tools, all_tools

# Import tool modules so registration side-effects execute
import tools.os_places  # noqa: F401
import tools.os_places_extra  # noqa: F401
import tools.os_names  # noqa: F401
import tools.os_linked_ids  # noqa: F401
import tools.os_features  # noqa: F401
import tools.os_maps  # noqa: F401
import tools.os_vector_tiles  # noqa: F401

router = APIRouter()


@router.get("/tools/list")
def list_tools_endpoint(limit: int = 10, page: int = 1):
    names = list_tools()
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(names) else None
    return {"tools": names[start:end], "nextPageToken": next_page_token}


@router.post("/tools/call")
async def call_tool(request: Request):
    data = await request.json()
    tool_name = data.get("tool")
    if not tool_name:
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "Missing 'tool' field",
            },
        )
    tool = get(tool_name)
    if not tool:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "isError": True,
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' not found",
            },
        )
    status_code, payload = tool.call(data)
    return JSONResponse(status_code=status_code, content=payload)


@router.get("/tools/describe")
def describe_tools(name: str | None = None):
    if name:
        tool = get(name)
        if not tool:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "isError": True,
                    "code": "UNKNOWN_TOOL",
                    "message": f"Tool '{name}' not found",
                },
            )
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "version": tool.version,
                    "inputSchema": tool.input_schema,
                    "outputSchema": tool.output_schema,
                }
            ]
        }
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "version": t.version,
                "inputSchema": t.input_schema,
                "outputSchema": t.output_schema,
            }
            for t in all_tools()
        ]
    }
