import importlib
from typing import Any, Dict

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from server.mcp.tool_search import get_tool_metadata, search_tools
from tools.os_apps import build_ui_tool_meta
from tools.registry import Tool, all_tools, get, list_tools, register

# Explicitly import tool modules to guarantee registration
# (some environments skipped side-effect imports).
_IMPORT_MODULES = [
    "tools.os_places",
    "tools.os_places_extra",
    "tools.os_names",
    "tools.os_linked_ids",
    "tools.os_features",
    "tools.os_maps",
    "tools.os_vector_tiles",
    "tools.admin_lookup",
    "tools.ons_data",
    "tools.ons_search",
    "tools.ons_codes",
    "tools.os_mcp",
    "tools.os_apps",
]

for _mod in _IMPORT_MODULES:
    try:  # pragma: no cover - defensive import
        importlib.import_module(_mod)
    except Exception:  # pragma: no cover
        pass

if get("os_features.query") is None:
    register(
        Tool(
            name="os_features.query",
            description="Query features by bbox",
            input_schema={
                "type": "object",
                "properties": {
                    "tool": {"type": "string", "const": "os_features.query"},
                    "collection": {"type": "string"},
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                },
                "required": ["collection", "bbox"],
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "properties": {
                    "features": {"type": "array"},
                    "count": {"type": "number"},
                },
                "required": ["features"],
            },
        )
    )

_PREFIX_IMPORTS = {
    "os_places": ["tools.os_places", "tools.os_places_extra"],
    "os_names": ["tools.os_names"],
    "os_linked_ids": ["tools.os_linked_ids"],
    "os_features": ["tools.os_features"],
    "os_maps": ["tools.os_maps"],
    "os_vector_tiles": ["tools.os_vector_tiles"],
    "admin_lookup": ["tools.admin_lookup"],
    "ons_data": ["tools.ons_data"],
    "ons_search": ["tools.ons_search"],
    "ons_codes": ["tools.ons_codes"],
    "os_mcp": ["tools.os_mcp"],
    "os_apps": ["tools.os_apps"],
}


def _try_import_for_tool(tool_name: str) -> list[str]:
    prefix = tool_name.split(".", 1)[0].lower()
    modules = _PREFIX_IMPORTS.get(prefix, [])
    errors: list[str] = []
    for mod in modules:
        try:
            importlib.import_module(mod)
        except Exception as exc:  # pragma: no cover - defensive import
            errors.append(f"{mod}: {exc}")
    return errors

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
    if not isinstance(tool_name, str) or not tool_name.strip():
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "Missing 'tool' field",
            },
        )
    tool_name = tool_name.strip()
    tool = get(tool_name)
    if not tool:
        errors = _try_import_for_tool(tool_name)
        tool = get(tool_name)
        prefix = tool_name.split(".", 1)[0].lower()
        if not tool and (errors or prefix in _PREFIX_IMPORTS):
            code = "TOOL_IMPORT_FAILED" if errors else "TOOL_NOT_REGISTERED"
            message = (
                "Failed to import tool module"
                if errors
                else "Tool module imported but tool not registered"
            )
            return JSONResponse(
                status_code=501,
                content={
                    "isError": True,
                    "code": code,
                    "message": message,
                    "details": errors,
                },
            )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "isError": True,
                "code": "UNKNOWN_TOOL",
                "message": f"Tool '{tool_name}' not found",
            },
        )
    status_code, payload = tool.call(data)
    if tool_name == "os_mcp.descriptor" and isinstance(payload, dict):
        payload = dict(payload)
        payload.setdefault("transport", "http")
    return JSONResponse(status_code=status_code, content=payload)


@router.post("/tools/search")
async def search_tools_endpoint(request: Request):
    data = await request.json()
    query = data.get("query") or data.get("q")
    if not isinstance(query, str) or not query.strip():
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "Missing 'query' field",
            },
        )
    mode = data.get("mode", "token")
    if not isinstance(mode, str):
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "mode must be a string",
            },
        )
    limit = data.get("limit", 10)
    if not isinstance(limit, int) or limit < 1:
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "limit must be >= 1",
            },
        )
    category = data.get("category")
    if category is not None and not isinstance(category, str):
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "category must be a string",
            },
        )
    include_schemas = data.get("includeSchemas", False)
    if not isinstance(include_schemas, bool):
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "includeSchemas must be a boolean",
            },
        )
    try:
        results = search_tools(
            query,
            mode=mode,
            limit=limit,
            category=category,
            include_schemas=include_schemas,
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": str(exc),
            },
        )
    return {"tools": results, "count": len(results), "mode": mode}


def _describe_tool(tool: Tool) -> dict[str, Any]:
    meta = get_tool_metadata(tool)
    description: dict[str, Any] = {
        "name": tool.name,
        "description": tool.description,
        "version": tool.version,
        "inputSchema": tool.input_schema,
        "outputSchema": tool.output_schema,
        "inputSchemaRef": f"#/tools/{tool.name}/inputSchema",
        "outputSchemaRef": f"#/tools/{tool.name}/outputSchema",
        "annotations": meta.get("annotations", {}),
    }
    ui_meta = build_ui_tool_meta(tool.name)
    internal_meta: dict[str, Any] = {}
    if meta.get("category") is not None:
        internal_meta["category"] = meta.get("category")
    if meta.get("keywords"):
        internal_meta["keywords"] = meta.get("keywords", [])
    if meta.get("defer_loading") is not None:
        internal_meta["deferLoading"] = meta.get("defer_loading")
    if ui_meta or internal_meta:
        merged: dict[str, Any] = {}
        if ui_meta:
            merged.update(ui_meta)
        if internal_meta:
            merged["mcp-geo"] = internal_meta
        description["_meta"] = merged
    return description


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
        return {"tools": [_describe_tool(tool)]}
    return {
        "tools": [_describe_tool(t) for t in all_tools()]
    }
