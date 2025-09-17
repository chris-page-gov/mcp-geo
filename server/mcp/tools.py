
from fastapi import APIRouter, Request, status
from typing import Any, Dict
from fastapi.responses import JSONResponse

from tools.registry import all_tools, get, list_tools
import importlib

# Explicitly import tool modules to guarantee registration (some environments skipped side-effect imports)
for _mod in [
    "tools.os_places",
    "tools.os_places_extra",
    "tools.os_names",
    "tools.os_linked_ids",
    "tools.os_features",
    "tools.os_maps",
    "tools.os_vector_tiles",
    "tools.admin_lookup",
    "tools.ons_data",
]:
    try:  # pragma: no cover - defensive import
        importlib.import_module(_mod)
    except Exception:  # pragma: no cover
        pass

# (Legacy static import block retained for clarity; dynamic imports above ensure execution.)

router = APIRouter()


@router.get("/tools/list")
def list_tools_endpoint(limit: int = 10, page: int = 1) -> Dict[str, Any]:
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
