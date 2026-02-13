import importlib
import time
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from server.mcp.tool_search import (
    filter_tool_names_by_toolsets,
    get_tool_metadata,
    get_toolset_catalog,
    parse_toolset_list,
    search_tools,
)
from server.observability import record_tool_call
from server.tool_naming import build_tool_name_maps, resolve_tool_name, rewrite_tool_schema
from tools.os_apps import build_ui_tool_meta
from tools.registry import Tool, all_tools, get, list_tools, register

# Explicitly import tool modules to guarantee registration
# (some environments skipped side-effect imports).
_IMPORT_MODULES = [
    "tools.os_places",
    "tools.os_places_extra",
    "tools.os_poi",
    "tools.os_names",
    "tools.os_linked_ids",
    "tools.os_features",
    "tools.os_maps",
    "tools.os_vector_tiles",
    "tools.os_qgis",
    "tools.os_tiles_ota",
    "tools.os_net",
    "tools.os_downloads",
    "tools.admin_lookup",
    "tools.ons_data",
    "tools.ons_search",
    "tools.ons_select",
    "tools.ons_codes",
    "tools.nomis_data",
    "tools.os_map",
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
    "os_poi": ["tools.os_poi"],
    "os_names": ["tools.os_names"],
    "os_linked_ids": ["tools.os_linked_ids"],
    "os_features": ["tools.os_features"],
    "os_maps": ["tools.os_maps"],
    "os_vector_tiles": ["tools.os_vector_tiles"],
    "os_qgis": ["tools.os_qgis"],
    "os_tiles_ota": ["tools.os_tiles_ota"],
    "os_net": ["tools.os_net"],
    "os_downloads": ["tools.os_downloads"],
    "admin_lookup": ["tools.admin_lookup"],
    "ons_data": ["tools.ons_data"],
    "ons_search": ["tools.ons_search"],
    "ons_select": ["tools.ons_select"],
    "ons_codes": ["tools.ons_codes"],
    "nomis": ["tools.nomis_data"],
    "os_map": ["tools.os_map"],
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
def list_tools_endpoint(
    limit: int = 10,
    page: int = 1,
    toolset: str | None = None,
    includeToolsets: str | None = None,
    excludeToolsets: str | None = None,
) -> Any:
    names = list_tools()
    try:
        filtered_names = filter_tool_names_by_toolsets(
            names,
            toolset=toolset,
            include_toolsets=parse_toolset_list(includeToolsets),
            exclude_toolsets=parse_toolset_list(excludeToolsets),
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"isError": True, "code": "INVALID_INPUT", "message": str(exc)},
        )
    original_to_sanitized, _ = build_tool_name_maps(names)
    sanitized = [original_to_sanitized.get(name, name) for name in filtered_names]
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(sanitized) else None
    return {
        "tools": sanitized[start:end],
        "nextPageToken": next_page_token,
        "toolsets": get_toolset_catalog(),
    }


@router.post("/tools/call")
async def call_tool(request: Request):
    data = await request.json()
    if not isinstance(data, dict):
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "Request body must be a JSON object",
            },
        )
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
    resolved_name = resolve_tool_name(tool_name, list_tools())
    tool = get(resolved_name)
    if resolved_name != tool_name:
        data = dict(data)
        data["tool"] = resolved_name
    if not tool:
        errors = _try_import_for_tool(resolved_name)
        tool = get(resolved_name)
        prefix = resolved_name.split(".", 1)[0].lower()
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
    started = time.perf_counter()
    status_code, payload = tool.call(data)
    if resolved_name == "os_mcp.descriptor" and isinstance(payload, dict):
        payload = dict(payload)
        payload.setdefault("transport", "http")
    record_tool_call(
        tool_name=resolved_name,
        transport="http_tools",
        payload=data,
        result=payload,
        status_code=status_code,
        latency_ms=(time.perf_counter() - started) * 1000.0,
    )
    return JSONResponse(status_code=status_code, content=payload)


@router.post("/tools/search")
async def search_tools_endpoint(request: Request):
    data = await request.json()
    if not isinstance(data, dict):
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "Request body must be a JSON object",
            },
        )
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
    toolset = data.get("toolset")
    if toolset is not None and not isinstance(toolset, str):
        return JSONResponse(
            status_code=400,
            content={
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "toolset must be a string",
            },
        )
    try:
        include_toolsets = parse_toolset_list(data.get("includeToolsets"))
        exclude_toolsets = parse_toolset_list(data.get("excludeToolsets"))
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"isError": True, "code": "INVALID_INPUT", "message": str(exc)},
        )
    try:
        results = search_tools(
            query,
            mode=mode,
            limit=limit,
            category=category,
            include_schemas=include_schemas,
            toolset=toolset,
            include_toolsets=include_toolsets,
            exclude_toolsets=exclude_toolsets,
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
    original_to_sanitized, _ = build_tool_name_maps(list_tools())
    normalized: list[dict[str, Any]] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        entry = dict(result)
        original_name = entry.get("name")
        if isinstance(original_name, str):
            entry["name"] = original_to_sanitized.get(original_name, original_name)
            annotations = entry.get("annotations")
            if isinstance(annotations, dict):
                annotations = dict(annotations)
            else:
                annotations = {}
            annotations.setdefault("originalName", original_name)
            entry["annotations"] = annotations
        normalized.append(entry)
    return {
        "tools": normalized,
        "count": len(normalized),
        "mode": mode,
        "toolsets": get_toolset_catalog(),
    }


def _describe_tool(tool: Tool, original_to_sanitized: dict[str, str]) -> dict[str, Any]:
    meta = get_tool_metadata(tool)
    original_name = tool.name
    sanitized_name = original_to_sanitized.get(original_name, original_name)
    annotations = dict(meta.get("annotations", {}))
    annotations.setdefault("originalName", original_name)
    description: dict[str, Any] = {
        "name": sanitized_name,
        "description": tool.description,
        "version": tool.version,
        "inputSchema": rewrite_tool_schema(
            tool.input_schema,
            sanitized_name=sanitized_name,
            original_name=original_name,
        ),
        "outputSchema": tool.output_schema,
        "inputSchemaRef": f"#/tools/{sanitized_name}/inputSchema",
        "outputSchemaRef": f"#/tools/{sanitized_name}/outputSchema",
        "annotations": annotations,
    }
    ui_meta = build_ui_tool_meta(original_name)
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
def describe_tools(
    name: str | None = None,
    toolset: str | None = None,
    includeToolsets: str | None = None,
    excludeToolsets: str | None = None,
):
    original_names = list_tools()
    try:
        filtered_names = set(
            filter_tool_names_by_toolsets(
                original_names,
                toolset=toolset,
                include_toolsets=parse_toolset_list(includeToolsets),
                exclude_toolsets=parse_toolset_list(excludeToolsets),
            )
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"isError": True, "code": "INVALID_INPUT", "message": str(exc)},
        )
    original_to_sanitized, _ = build_tool_name_maps(original_names)
    if name:
        resolved_name = resolve_tool_name(name, original_names)
        if filtered_names and resolved_name not in filtered_names:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "isError": True,
                    "code": "UNKNOWN_TOOL",
                    "message": f"Tool '{name}' not found",
                },
            )
        tool = get(resolved_name)
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
            "tools": [_describe_tool(tool, original_to_sanitized)],
            "toolsets": get_toolset_catalog(),
        }
    filtered_tools = [tool for tool in all_tools() if tool.name in filtered_names]
    return {
        "tools": [_describe_tool(t, original_to_sanitized) for t in filtered_tools],
        "toolsets": get_toolset_catalog(),
    }
