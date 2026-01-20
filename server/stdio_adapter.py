"""STDIO JSON-RPC 2.0 adapter for mcp-geo.

Moved from `scripts/os_mcp.py` into the `server` package for consistency. The legacy
entry points (`scripts/os-mcp`, console script `mcp-geo-stdio`) still work by
delegating to this module's `main`.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import side-effects to register tools
import tools.registry as _reg  # noqa: F401
from server.mcp import tools as _mcp_import  # noqa: F401

from tools.registry import all_tools, get as get_tool
from server.mcp.resource_catalog import (
    DATA_RESOURCE_PREFIX,
    data_resource_uri,
    list_skill_resources,
    list_ui_resources,
    load_skill_content,
    load_ui_content,
    resolve_skill_resource,
    resolve_ui_resource,
)
from server.mcp.tool_search import get_tool_metadata, search_tools
from server import __version__ as SERVER_VERSION

JSONRPC = "2.0"

RESOURCE_LIST: List[dict[str, Any]] = [
    {
        "name": "admin_boundaries",
        "uri": data_resource_uri("admin_boundaries"),
        "type": "boundary_hierarchy",
        "version": "2025.09.17-alpha",
        "license": "Open Government Licence v3",
        "source": "ONS / Ordnance Survey open data (sample subset)",
        "description": "Sample administrative boundaries chain",
        "mimeType": "application/json",
        "annotations": {"audience": ["assistant"], "priority": 0.7},
    },
    {
        "name": "ons_observations",
        "uri": data_resource_uri("ons_observations"),
        "type": "dataset",
        "version": None,
        "license": "Open Government Licence v3",
        "source": "ONS (sample synthetic subset)",
        "description": "Sample ONS GDP observations (synthetic)",
        "mimeType": "application/json",
        "annotations": {"audience": ["assistant"], "priority": 0.6},
    },
    {
        "name": "address_classification_codes",
        "uri": data_resource_uri("address_classification_codes"),
        "type": "code_list",
        "version": "2025.11.03-alpha",
        "license": "Open Government Licence v3",
        "source": "OS AddressBase (sample subset)",
        "description": "Address classification code descriptions",
        "mimeType": "application/json",
        "annotations": {"audience": ["assistant"], "priority": 0.4},
    },
    {
        "name": "custodian_codes",
        "uri": data_resource_uri("custodian_codes"),
        "type": "code_list",
        "version": "2025.11.03-alpha",
        "license": "Open Government Licence v3",
        "source": "Local Authority Codes (sample)",
        "description": "Local custodian code to name mapping",
        "mimeType": "application/json",
        "annotations": {"audience": ["assistant"], "priority": 0.4},
    },
    {
        "name": "boundaries_wards",
        "uri": data_resource_uri("boundaries_wards"),
        "type": "boundary",
        "version": "2025.11.03-alpha",
        "license": "Open Government Licence v3",
        "source": "Sample Ward Boundaries (synthetic subset)",
        "description": "Ward-level bounding boxes (sample subset)",
        "mimeType": "application/json",
        "annotations": {"audience": ["assistant"], "priority": 0.5},
    },
]
RESOURCE_LIST.extend(list_skill_resources())
RESOURCE_LIST.extend(list_ui_resources())

RESOURCES_PATH = ROOT / "resources"

def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:  # pragma: no cover (error handled upstream)
        raise LookupError("Resource file missing")

def _etag_for(name: str, variant: str, raw_bytes: bytes, version: str = "v0") -> str:
    h = hashlib.sha256(raw_bytes + version.encode() + variant.encode()).hexdigest()[:16]
    return f"W/\"{h}\""

def handle_get_resource(params: Dict[str, Any]) -> Any:
    name = params.get("name")
    uri = params.get("uri")
    if not name and not uri:
        raise ValueError("Missing resource name or uri")
    if_none_match = params.get("ifNoneMatch")
    if uri:
        if isinstance(uri, str) and uri.startswith(DATA_RESOURCE_PREFIX):
            name = uri[len(DATA_RESOURCE_PREFIX):]
        else:
            ui_entry = resolve_ui_resource(str(uri))
            if ui_entry:
                content, etag = load_ui_content(ui_entry)
                if if_none_match:
                    tokens = {t.strip() for t in str(if_none_match).split(',') if t.strip()}
                    if etag in tokens or "*" in tokens:
                        return {"notModified": True, "etag": etag}
                return {
                    "uri": ui_entry["uri"],
                    "name": ui_entry["name"],
                    "title": ui_entry["title"],
                    "mimeType": ui_entry["mimeType"],
                    "etag": etag,
                    "content": content,
                }
            skill_entry = resolve_skill_resource(str(uri))
            if skill_entry:
                content, etag = load_skill_content()
                if if_none_match:
                    tokens = {t.strip() for t in str(if_none_match).split(',') if t.strip()}
                    if etag in tokens or "*" in tokens:
                        return {"notModified": True, "etag": etag}
                return {
                    "uri": skill_entry["uri"],
                    "name": skill_entry["name"],
                    "title": skill_entry["title"],
                    "mimeType": skill_entry["mimeType"],
                    "etag": etag,
                    "content": content,
                }
            raise LookupError(f"Unknown resource '{uri}'")
    if name:
        ui_entry = resolve_ui_resource(str(name))
        if ui_entry:
            content, etag = load_ui_content(ui_entry)
            if if_none_match:
                tokens = {t.strip() for t in str(if_none_match).split(',') if t.strip()}
                if etag in tokens or "*" in tokens:
                    return {"notModified": True, "etag": etag}
            return {
                "uri": ui_entry["uri"],
                "name": ui_entry["name"],
                "title": ui_entry["title"],
                "mimeType": ui_entry["mimeType"],
                "etag": etag,
                "content": content,
            }
        skill_entry = resolve_skill_resource(str(name))
        if skill_entry:
            content, etag = load_skill_content()
            if if_none_match:
                tokens = {t.strip() for t in str(if_none_match).split(',') if t.strip()}
                if etag in tokens or "*" in tokens:
                    return {"notModified": True, "etag": etag}
            return {
                "uri": skill_entry["uri"],
                "name": skill_entry["name"],
                "title": skill_entry["title"],
                "mimeType": skill_entry["mimeType"],
                "etag": etag,
                "content": content,
            }
    if not isinstance(name, str):
        raise ValueError("Missing resource name")
    if name == "admin_boundaries":
        raw = _read_json(RESOURCES_PATH / "admin_boundaries.json")
        features = raw.get("features", [])
        level = params.get("level")
        name_contains = params.get("nameContains")
        if level:
            lvl = str(level).upper()
            features = [f for f in features if f.get("level") == lvl]
        if name_contains:
            needle = str(name_contains).lower()
            features = [f for f in features if needle in str(f.get("name", "")).lower()]
        limit = int(params.get("limit", 100))
        page = int(params.get("page", 1))
        start = (page - 1) * limit
        end = start + limit
        page_items = features[start:end]
        next_page_token = str(page + 1) if end < len(features) else None
        variant_key = f"ab|{level or '*'}|{name_contains or '*'}|{limit}|{page}"
        etag = _etag_for(name, variant_key, json.dumps(raw, separators=(",", ":")).encode())
        if if_none_match:
            tokens = {t.strip() for t in str(if_none_match).split(',') if t.strip()}
            if etag in tokens or "*" in tokens:
                return {"notModified": True, "etag": etag}
        return {
            "name": name,
            "uri": data_resource_uri(name),
            "count": len(features),
            "etag": etag,
            "data": {
                "features": page_items,
                "total": len(features),
                "limit": limit,
                "page": page,
                "nextPageToken": next_page_token,
            },
        }
    if name == "ons_observations":
        raw = _read_json(RESOURCES_PATH / "ons_observations.json")
        observations = raw.get("observations", [])
        geography = params.get("geography")
        measure = params.get("measure")
        if geography or measure:
            filtered_obs: list[dict[str, Any]] = []
            for o in observations:
                if geography and o.get("geography") != geography:
                    continue
                if measure and o.get("measure") != measure:
                    continue
                filtered_obs.append(o)
            observations = filtered_obs
        limit = int(params.get("limit", 100))
        page = int(params.get("page", 1))
        start = (page - 1) * limit
        end = start + limit
        page_items = observations[start:end]
        next_page_token = str(page + 1) if end < len(observations) else None
        variant_key = f"obs|{geography or '*'}|{measure or '*'}|{page}|{limit}"
        etag = _etag_for(
            name, variant_key, json.dumps(raw, separators=(",", ":")).encode()
        )
        if if_none_match:
            tokens = {t.strip() for t in str(if_none_match).split(',') if t.strip()}
            if etag in tokens or "*" in tokens:
                return {"notModified": True, "etag": etag}
        return {
            "name": name,
            "uri": data_resource_uri(name),
            "count": len(observations),
            "etag": etag,
            "provenance": {
                **raw.get("provenance", {}),
                "retrievedAt": datetime.now(timezone.utc).isoformat(),
            },
            "data": {
                "observations": page_items,
                "total": len(observations),
                "limit": limit,
                "page": page,
                "nextPageToken": next_page_token,
                "dimensions": raw.get("dimensions", {}),
                "appliedFilters": {"geography": geography, "measure": measure},
            },
        }
    if name in {"address_classification_codes", "custodian_codes", "boundaries_wards"}:
        raw = _read_json(RESOURCES_PATH / f"{name}.json")
        items = raw.get("codes") or raw.get("features") or []
        limit = int(params.get("limit", 100))
        page = int(params.get("page", 1))
        start = (page - 1) * limit
        end = start + limit
        page_items = items[start:end]
        next_page_token = str(page + 1) if end < len(items) else None
        variant_key = f"{name}|base|{page}|{limit}"
        etag = _etag_for(
            name, variant_key, json.dumps(raw, separators=(",", ":")).encode()
        )
        if if_none_match:
            tokens = {t.strip() for t in str(if_none_match).split(',') if t.strip()}
            if etag in tokens or "*" in tokens:
                return {"notModified": True, "etag": etag}
        return {
            "name": name,
            "uri": data_resource_uri(name),
            "count": len(items),
            "etag": etag,
            "provenance": {
                **raw.get("provenance", {}),
                "retrievedAt": datetime.now(timezone.utc).isoformat(),
            },
            "data": {
                "items": page_items,
                "total": len(items),
                "limit": limit,
                "page": page,
                "nextPageToken": next_page_token,
            },
        }
    raise LookupError(f"Unknown resource '{name}'")

def _write_message(payload: Dict[str, Any]) -> None:
    data = json.dumps(payload, separators=(",", ":"))
    try:
        sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
        sys.stdout.flush()
    except BrokenPipeError:  # pragma: no cover
        pass

def _resp_success(msg_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": JSONRPC, "id": msg_id, "result": result}

def _resp_error(msg_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": JSONRPC, "id": msg_id, "error": err}

def handle_initialize(_params: Dict[str, Any]) -> Any:
    return {
        "server": "mcp-geo",
        "version": SERVER_VERSION,
        "capabilities": {
            "tools": True,
            "resources": True,
            "toolSearch": True,
            "uiResources": True,
            "skills": True,
        },
    }

def handle_list_tools(_params: Dict[str, Any]) -> Any:
    tool_entries: list[dict[str, Any]] = []
    for t in all_tools():
        meta = get_tool_metadata(t)
        tool_entries.append(
            {
                "name": t.name,
                "description": t.description,
                "version": t.version,
                "inputSchema": t.input_schema,
                "outputSchema": t.output_schema,
                "annotations": meta.get("annotations", {}),
                "category": meta.get("category"),
                "keywords": meta.get("keywords", []),
                "deferLoading": meta.get("defer_loading", False),
                "defer_loading": meta.get("defer_loading", False),
            }
        )
    return {"tools": tool_entries}


def handle_search_tools(params: Dict[str, Any]) -> Any:
    query = params.get("query") or params.get("q")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Missing query")
    mode = params.get("mode", "token")
    if not isinstance(mode, str):
        raise ValueError("mode must be a string")
    limit = params.get("limit", 10)
    if not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be >= 1")
    category = params.get("category")
    if category is not None and not isinstance(category, str):
        raise ValueError("category must be a string")
    include_schemas = params.get("includeSchemas", False)
    if not isinstance(include_schemas, bool):
        raise ValueError("includeSchemas must be a boolean")
    results = search_tools(
        query,
        mode=mode,
        limit=limit,
        category=category,
        include_schemas=include_schemas,
    )
    return {"tools": results, "count": len(results), "mode": mode}

def handle_call_tool(params: Dict[str, Any]) -> Any:
    name = params.get("tool") or params.get("name")
    if not isinstance(name, str):
        raise ValueError("Missing tool name")
    tool = get_tool(name)
    if not tool:
        raise LookupError(f"Unknown tool '{name}'")
    payload = params.get("args") or params.get("payload") or {}
    if not isinstance(payload, dict):
        raise TypeError("Payload must be object")
    status, data = tool.call(payload)
    return {"status": status, "ok": 200 <= status < 300, "data": data}

def handle_list_resources(_params: Dict[str, Any]) -> Any:
    return {"resources": RESOURCE_LIST}

def handle_shutdown(_params: Dict[str, Any]) -> Any:
    return None

HANDLERS: Dict[str, Any] = {
    "initialize": handle_initialize,
    "tools/list": handle_list_tools,
    "tools/search": handle_search_tools,
    "tools/call": handle_call_tool,
    "resources/list": handle_list_resources,
    "resources/describe": lambda _p: {"resources": RESOURCE_LIST},
    "resources/get": handle_get_resource,
    "shutdown": handle_shutdown,
}

def _read_headers(stdin) -> Optional[int]:
    content_length: Optional[int] = None
    while True:
        line = stdin.readline()
        if line == "":
            return None  # EOF
        if line in ("\n", "\r\n"):
            break
        lower = line.lower()
        if lower.startswith("content-length:"):
            try:
                content_length = int(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return content_length

def main(stdin: Optional[TextIO] = None, stdout: Optional[TextIO] = None) -> None:
    """Run adapter loop with optional injected streams (for unit tests).

    stdin/stdout may be injected StringIO objects in tests; in production they
    default to process stdio. All responses are framed using Content-Length and
    JSON-RPC 2.0 envelopes.
    """
    if stdin is None:
        stdin = sys.stdin  # type: ignore[assignment]
    if stdout is None:
        stdout = sys.stdout  # type: ignore[assignment]
    orig_stdout = sys.stdout
    sys.stdout = stdout  # type: ignore
    try:
        _write_message(
            {
                "jsonrpc": JSONRPC,
                "method": "log",
                "params": {"level": "info", "message": "mcp-geo stdio adapter starting"},
            }
        )
        while True:
            length = _read_headers(stdin)
            if length is None:
                break
            body = stdin.read(length)
            if not body:
                break
            try:
                msg = json.loads(body)
            except json.JSONDecodeError:
                _write_message(_resp_error(None, -32700, "Parse error"))
                continue
            if msg.get("jsonrpc") != JSONRPC:
                _write_message(_resp_error(msg.get("id"), -32600, "Invalid Request"))
                continue
            method = msg.get("method")
            msg_id = msg.get("id")
            if method == "exit":
                break
            handler = HANDLERS.get(method)
            if not handler:
                _write_message(
                    _resp_error(msg_id, -32601, f"Method not found: {method}")
                )
                continue
            # Preserve original type to validate; only default to empty dict when param key absent.
            params = msg.get("params")
            if params is None:
                params = {}
            if not isinstance(params, dict):
                _write_message(_resp_error(msg_id, -32602, "Invalid params"))
                continue
            try:
                result = handler(params)
                _write_message(_resp_success(msg_id, result))
            except LookupError as e:
                _write_message(_resp_error(msg_id, 1001, str(e)))
            except ValueError as e:
                _write_message(_resp_error(msg_id, 1002, str(e)))
            except TypeError as e:
                _write_message(_resp_error(msg_id, 1003, str(e)))
            except Exception as e:  # pragma: no cover
                _write_message(_resp_error(msg_id, -32603, f"Internal error: {e}"))
        try:
            _write_message(
                {
                    "jsonrpc": JSONRPC,
                    "method": "log",
                    "params": {"level": "info", "message": "adapter exiting"},
                }
            )
        except Exception:  # pragma: no cover
            pass
    finally:
        sys.stdout = orig_stdout  # type: ignore

if __name__ == "__main__":  # pragma: no cover
    main()
