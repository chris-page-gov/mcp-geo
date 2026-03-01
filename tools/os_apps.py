from __future__ import annotations

import json
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from server.config import settings
from server.mcp.resource_catalog import MCP_APPS_MIME, load_ui_content, resolve_ui_resource
from tools.registry import Tool, ToolResult, register

_UI_URIS = {
    "geography": "ui://mcp-geo/geography-selector",
    "boundary": "ui://mcp-geo/boundary-explorer",
    "statistics": "ui://mcp-geo/statistics-dashboard",
    "feature": "ui://mcp-geo/feature-inspector",
    "route": "ui://mcp-geo/route-planner",
}
_UI_RESOURCE_LINKS = {
    _UI_URIS["geography"]: {
        "name": "ui_geography_selector",
        "title": "Geography Selector",
        "description": "Interactive selector for UK administrative areas.",
    },
    _UI_URIS["boundary"]: {
        "name": "ui_boundary_explorer",
        "title": "Map Lab",
        "description": "Map Lab workspace for UK boundaries, UPRNs, buildings, links, and selector-based collections.",
    },
    _UI_URIS["statistics"]: {
        "name": "ui_statistics_dashboard",
        "title": "Statistics Dashboard",
        "description": "Visual dashboard for ONS observations and comparisons.",
    },
    _UI_URIS["feature"]: {
        "name": "ui_feature_inspector",
        "title": "Feature Inspector",
        "description": "Inspect OS NGD features and linked identifiers.",
    },
    _UI_URIS["route"]: {
        "name": "ui_route_planner",
        "title": "Route Planner",
        "description": "Plan routes with waypoints and directions.",
    },
}
UI_TOOL_RESOURCES = {
    "os_apps.render_geography_selector": {
        "mcp": _UI_URIS["geography"],
    },
    "os_apps.render_boundary_explorer": {
        "mcp": _UI_URIS["boundary"],
    },
    "os_apps.render_statistics_dashboard": {
        "mcp": _UI_URIS["statistics"],
    },
    "os_apps.render_feature_inspector": {
        "mcp": _UI_URIS["feature"],
    },
    "os_apps.render_route_planner": {
        "mcp": _UI_URIS["route"],
    },
    "os_apps.render_ui_probe": {
        "mcp": _UI_URIS["statistics"],
    },
}

_MAX_TOOL_RESPONSE_BYTES = 950_000
_MAX_EMBEDDED_RESOURCE_BYTES = 850_000
_ONS_DATASET_ALIASES = {
    "gdp": "gdp-to-four-decimal-places",
}


def build_ui_tool_meta(tool_name: str) -> dict[str, Any] | None:
    entry = UI_TOOL_RESOURCES.get(tool_name)
    if not entry:
        return None
    return {
        "ui": {"resourceUri": entry["mcp"]},
        "ui/resourceUri": entry["mcp"],
        "openai/outputTemplate": entry["mcp"],
    }
_EVENT_LOG_LOCK = threading.Lock()
_SENSITIVE_KEY_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "token",
    "secret",
    "password",
)


def _error(message: str) -> ToolResult:
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": message}

def _normalize_content_mode(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    norm = value.strip().lower()
    if not norm or norm == "auto":
        return None
    if norm in {"resource_link", "link"}:
        return "resource_link"
    if norm in {"resource", "embedded", "embed", "inline"}:
        return "embedded"
    if norm in {"text", "plain"}:
        return "text"
    return None


def _resolve_content_mode(override: Any) -> str | None:
    mode = _normalize_content_mode(override)
    if mode:
        return mode
    env_mode = _normalize_content_mode(getattr(settings, "MCP_APPS_CONTENT_MODE", ""))
    if env_mode:
        return env_mode
    if settings.MCP_APPS_RESOURCE_LINK:
        return "resource_link"
    return None


def _json_size_bytes(value: Any) -> int:
    try:
        encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":"), default=str)
    except Exception:
        encoded = str(value)
    return len(encoded.encode("utf-8"))


def _build_embedded_resource(resource_uri: str) -> tuple[dict[str, Any] | None, str | None]:
    entry = resolve_ui_resource(resource_uri)
    if not entry:
        return None, None
    text, _etag = load_ui_content(entry)
    if len(text.encode("utf-8")) > _MAX_EMBEDDED_RESOURCE_BYTES:
        return (
            None,
            (
                "Embedded UI content omitted because it exceeds transport-safe limits; "
                "open the widget using resourceUri instead."
            ),
        )
    resource: dict[str, Any] = {
        "uri": entry["uri"],
        "mimeType": entry.get("mimeType", MCP_APPS_MIME),
        "text": text,
    }
    meta = entry.get("resourceMeta")
    if meta:
        resource["_meta"] = meta
    return {"type": "resource", "resource": resource}, None


def _enforce_widget_response_limit(response: dict[str, Any], *, resource_uri: str) -> dict[str, Any]:
    if _json_size_bytes(response) <= _MAX_TOOL_RESPONSE_BYTES:
        return response
    response["content"] = [
        {"type": "text", "text": response.get("instructions", "Open the UI widget.")},
        {
            "type": "text",
            "text": (
                "UI payload reduced to stay under the 1MB transport limit; "
                f"use {resource_uri} for full widget content."
            ),
        },
    ]
    meta = response.get("_meta")
    if not isinstance(meta, dict):
        meta = {}
        response["_meta"] = meta
    meta["uiPayloadTruncated"] = True
    meta["uiPayloadLimitBytes"] = _MAX_TOOL_RESPONSE_BYTES
    structured = response.get("structuredContent")
    if isinstance(structured, dict):
        structured["contentTruncated"] = True
        structured["delivery"] = "uri_only"
    return response


def _build_widget_response(
    config: dict[str, Any],
    instructions: str,
    *,
    resource_uri: str,
    content_mode: str | None = None,
) -> ToolResult:
    content = [{"type": "text", "text": instructions}]
    mode = _resolve_content_mode(content_mode)
    if mode == "resource_link":
        link_meta = _UI_RESOURCE_LINKS.get(resource_uri)
        resource_link = {
            "type": "resource_link",
            "name": link_meta["name"] if link_meta else resource_uri,
            "uri": resource_uri,
            "mimeType": MCP_APPS_MIME,
        }
        if link_meta:
            resource_link["title"] = link_meta["title"]
            resource_link["description"] = link_meta["description"]
        content.append(resource_link)
    elif mode == "embedded":
        embedded, warning = _build_embedded_resource(resource_uri)
        if embedded:
            content.append(embedded)
        if warning:
            content.append({"type": "text", "text": warning})
    structured = {
        "status": "ready",
        "config": config,
        "instructions": instructions,
        "resourceUri": resource_uri,
        "uiResourceUris": [resource_uri],
    }
    response = {
        "status": "ready",
        "config": config,
        "instructions": instructions,
        "resourceUri": resource_uri,
        "uiResourceUris": [resource_uri],
        "_meta": {
            "ui": {"resourceUri": resource_uri},
            "ui/resourceUri": resource_uri,
            "uiResourceUris": [resource_uri],
        },
        "structuredContent": structured,
        "content": content,
    }
    return 200, _enforce_widget_response_limit(response, resource_uri=resource_uri)


def _looks_sensitive(key: str) -> bool:
    key_norm = key.lower()
    if key_norm in _SENSITIVE_KEY_MARKERS:
        return True
    if key_norm.endswith("_key") or key_norm.endswith("_token"):
        return True
    if key_norm.startswith("bearer"):
        return True
    return False


def _redact_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        redacted: dict[str, Any] = {}
        for key, value in payload.items():
            if _looks_sensitive(str(key)):
                redacted[key] = "***"
            else:
                redacted[key] = _redact_payload(value)
        return redacted
    if isinstance(payload, list):
        return [_redact_payload(item) for item in payload]
    if isinstance(payload, str):
        redacted = payload
        redacted = re.sub(
            r"([?&](?:key|api_key|apikey|token|access_token|authorization)=)[^&#\s]+",
            r"\1REDACTED",
            redacted,
            flags=re.IGNORECASE,
        )
        redacted = re.sub(
            r"\b(Bearer)\s+[A-Za-z0-9\-._~+/]+=*",
            r"\1 REDACTED",
            redacted,
            flags=re.IGNORECASE,
        )
        redacted = re.sub(
            r"\b(api_key|apikey|access_token|token|authorization|auth)\b\s*[:=]\s*[^\s,;]+",
            r"\1=[REDACTED]",
            redacted,
            flags=re.IGNORECASE,
        )
        return redacted
    return payload


def _get_event_log_path() -> Path | None:
    raw = getattr(settings, "UI_EVENT_LOG_PATH", "")
    if not raw:
        return None
    return Path(raw)


def _log_event(payload: dict[str, Any]) -> ToolResult:
    """Log UI interaction events for MCP-Apps widgets.

    Request schema:
    {
      "type": "object",
      "properties": {
        "eventType": {"type": "string"},
        "source": {"type": "string"},
        "payload": {"type": "object"},
        "context": {"type": "object"},
        "timestamp": {"type": "number"},
        "sessionId": {"type": "string"}
      },
      "required": ["eventType"]
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "status": {"type": "string"},
        "eventId": {"type": "string"},
        "timestamp": {"type": "number"},
        "logPath": {"type": ["string", "null"]}
      },
      "required": ["status", "eventId", "timestamp"]
    }
    """
    event_type = payload.get("eventType")
    if not isinstance(event_type, str) or not event_type.strip():
        return _error("eventType must be a non-empty string")
    source = payload.get("source")
    if source is not None and not isinstance(source, str):
        return _error("source must be a string")
    context = payload.get("context")
    if context is not None and not isinstance(context, dict):
        return _error("context must be an object")
    event_payload = payload.get("payload")
    if event_payload is not None and not isinstance(
        event_payload,
        (dict, list, str, int, float, bool),
    ):
        return _error("payload must be JSON-serializable")
    session_id = payload.get("sessionId")
    if session_id is not None and not isinstance(session_id, str):
        return _error("sessionId must be a string")
    timestamp = payload.get("timestamp")
    if timestamp is not None and not isinstance(timestamp, (int, float)):
        return _error("timestamp must be a number")

    event_id = uuid.uuid4().hex
    event_ts = float(timestamp) if timestamp is not None else time.time()
    record: dict[str, Any] = {
        "eventId": event_id,
        "eventType": event_type.strip(),
        "source": source or "mcp-app",
        "timestamp": event_ts,
    }
    if session_id:
        record["sessionId"] = session_id
    if context:
        record["context"] = _redact_payload(context)
    if event_payload is not None:
        record["payload"] = _redact_payload(event_payload)

    log_path = _get_event_log_path()
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=True, default=str)
        with _EVENT_LOG_LOCK:
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    return 200, {
        "status": "logged",
        "eventId": event_id,
        "timestamp": event_ts,
        "logPath": str(log_path) if log_path else None,
    }


def _render_geography_selector(payload: dict[str, Any]) -> ToolResult:
    """Open the geography selector widget.

    Request schema:
    {
      "type": "object",
      "properties": {
        "level": {"type": "string"},
        "searchTerm": {"type": "string"},
        "focusName": {"type": "string"},
        "focusLevel": {"type": "string"},
        "multiSelect": {"type": "boolean"},
        "initialLat": {"type": "number"},
        "initialLng": {"type": "number"},
        "initialZoom": {"type": "integer"}
      },
      "required": []
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "status": {"type": "string"},
        "config": {"type": "object"},
        "instructions": {"type": "string"},
        "structuredContent": {"type": "object"},
        "content": {"type": "array"}
      },
      "required": ["status"]
    }
    """
    config: dict[str, Any] = {}
    level = payload.get("level")
    if level is not None and not isinstance(level, str):
        return _error("level must be a string")
    if level:
        config["level"] = level
    search_term = payload.get("searchTerm")
    if search_term is not None and not isinstance(search_term, str):
        return _error("searchTerm must be a string")
    if search_term:
        config["searchTerm"] = search_term
    focus_name = payload.get("focusName")
    if focus_name is not None and not isinstance(focus_name, str):
        return _error("focusName must be a string")
    if focus_name:
        config["focusName"] = focus_name
    focus_level = payload.get("focusLevel")
    if focus_level is not None and not isinstance(focus_level, str):
        return _error("focusLevel must be a string")
    if focus_level:
        config["focusLevel"] = focus_level
    multi_select = payload.get("multiSelect")
    if multi_select is not None and not isinstance(multi_select, bool):
        return _error("multiSelect must be a boolean")
    if multi_select is not None:
        config["multiSelect"] = multi_select
    initial_lat = payload.get("initialLat")
    initial_lng = payload.get("initialLng")
    initial_zoom = payload.get("initialZoom")
    if initial_lat is not None and not isinstance(initial_lat, (int, float)):
        return _error("initialLat must be a number")
    if initial_lng is not None and not isinstance(initial_lng, (int, float)):
        return _error("initialLng must be a number")
    if initial_zoom is not None and not isinstance(initial_zoom, int):
        return _error("initialZoom must be an integer")
    if initial_lat is not None and initial_lng is not None:
        config["initialView"] = {"lat": float(initial_lat), "lng": float(initial_lng)}
    if initial_zoom is not None:
        config["initialZoom"] = int(initial_zoom)
    content_mode = payload.get("contentMode")
    if content_mode is not None and not isinstance(content_mode, str):
        return _error("contentMode must be a string")
    return _build_widget_response(
        config,
        "Open the geography selector widget to choose areas interactively.",
        resource_uri=_UI_URIS["geography"],
        content_mode=content_mode,
    )


def _render_boundary_explorer(payload: dict[str, Any]) -> ToolResult:
    """Open the boundary explorer widget."""
    config: dict[str, Any] = {}
    level = payload.get("level")
    if level is not None and not isinstance(level, str):
        return _error("level must be a string")
    if level:
        config["level"] = level
    search_term = payload.get("searchTerm")
    if search_term is not None and not isinstance(search_term, str):
        return _error("searchTerm must be a string")
    if search_term:
        config["searchTerm"] = search_term
    focus_name = payload.get("focusName")
    if focus_name is not None and not isinstance(focus_name, str):
        return _error("focusName must be a string")
    if focus_name:
        config["focusName"] = focus_name
    focus_level = payload.get("focusLevel")
    if focus_level is not None and not isinstance(focus_level, str):
        return _error("focusLevel must be a string")
    if focus_level:
        config["focusLevel"] = focus_level
    initial_lat = payload.get("initialLat")
    initial_lng = payload.get("initialLng")
    initial_zoom = payload.get("initialZoom")
    if initial_lat is not None and not isinstance(initial_lat, (int, float)):
        return _error("initialLat must be a number")
    if initial_lng is not None and not isinstance(initial_lng, (int, float)):
        return _error("initialLng must be a number")
    if initial_zoom is not None and not isinstance(initial_zoom, int):
        return _error("initialZoom must be an integer")
    if initial_lat is not None and initial_lng is not None:
        config["initialView"] = {"lat": float(initial_lat), "lng": float(initial_lng)}
    if initial_zoom is not None:
        config["initialZoom"] = int(initial_zoom)
    detail_level = payload.get("detailLevel")
    if detail_level is not None and not isinstance(detail_level, str):
        return _error("detailLevel must be a string")
    if detail_level:
        config["detailLevel"] = detail_level
    content_mode = payload.get("contentMode")
    if content_mode is not None and not isinstance(content_mode, str):
        return _error("contentMode must be a string")
    return _build_widget_response(
        config,
        "Open Map Lab to learn mapping fundamentals, build collections, and render map layers.",
        resource_uri=_UI_URIS["boundary"],
        content_mode=content_mode,
    )


def _render_statistics_dashboard(payload: dict[str, Any]) -> ToolResult:
    """Open the statistics dashboard widget.

    Request schema:
    {
      "type": "object",
      "properties": {
        "dataset": {"type": "string"},
        "areaCodes": {"type": "array", "items": {"type": "string"}},
        "measure": {"type": "string"}
      },
      "required": []
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "status": {"type": "string"},
        "config": {"type": "object"},
        "instructions": {"type": "string"},
        "structuredContent": {"type": "object"},
        "content": {"type": "array"}
      },
      "required": ["status"]
    }
    """
    config: dict[str, Any] = {}
    dataset = payload.get("dataset")
    if dataset is not None and not isinstance(dataset, str):
        return _error("dataset must be a string")
    if dataset:
        normalized_dataset = dataset.strip()
        config["dataset"] = _ONS_DATASET_ALIASES.get(
            normalized_dataset.lower(),
            normalized_dataset,
        )
    area_codes = payload.get("areaCodes")
    if area_codes is not None:
        if not isinstance(area_codes, list) or not all(isinstance(x, str) for x in area_codes):
            return _error("areaCodes must be a list of strings")
        config["areaCodes"] = area_codes
    measure = payload.get("measure")
    if measure is not None and not isinstance(measure, str):
        return _error("measure must be a string")
    if measure:
        config["measure"] = measure
    content_mode = payload.get("contentMode")
    if content_mode is not None and not isinstance(content_mode, str):
        return _error("contentMode must be a string")
    return _build_widget_response(
        config,
        "Open the statistics dashboard to compare observations across areas.",
        resource_uri=_UI_URIS["statistics"],
        content_mode=content_mode,
    )


def _render_feature_inspector(payload: dict[str, Any]) -> ToolResult:
    """Open the feature inspector widget.

    Request schema:
    {
      "type": "object",
      "properties": {
        "collectionId": {"type": "string"},
        "featureId": {"type": "string"},
        "linkedIds": {"type": "array", "items": {"type": "string"}}
      },
      "required": []
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "status": {"type": "string"},
        "config": {"type": "object"},
        "instructions": {"type": "string"},
        "structuredContent": {"type": "object"},
        "content": {"type": "array"}
      },
      "required": ["status"]
    }
    """
    config: dict[str, Any] = {}
    collection_id = payload.get("collectionId")
    if collection_id is not None and not isinstance(collection_id, str):
        return _error("collectionId must be a string")
    if collection_id:
        config["collectionId"] = collection_id
    feature_id = payload.get("featureId")
    if feature_id is not None and not isinstance(feature_id, str):
        return _error("featureId must be a string")
    if feature_id:
        config["featureId"] = feature_id
    linked_ids = payload.get("linkedIds")
    if linked_ids is not None:
        if not isinstance(linked_ids, list) or not all(isinstance(x, str) for x in linked_ids):
            return _error("linkedIds must be a list of strings")
        config["linkedIds"] = linked_ids
    content_mode = payload.get("contentMode")
    if content_mode is not None and not isinstance(content_mode, str):
        return _error("contentMode must be a string")
    return _build_widget_response(
        config,
        "Open the feature inspector to review properties and linked identifiers.",
        resource_uri=_UI_URIS["feature"],
        content_mode=content_mode,
    )


def _render_route_planner(payload: dict[str, Any]) -> ToolResult:
    """Open the route planner widget.

    Request schema:
    {
      "type": "object",
      "properties": {
        "startLat": {"type": "number"},
        "startLng": {"type": "number"},
        "endLat": {"type": "number"},
        "endLng": {"type": "number"},
        "mode": {"type": "string"}
      },
      "required": []
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "status": {"type": "string"},
        "config": {"type": "object"},
        "instructions": {"type": "string"},
        "structuredContent": {"type": "object"},
        "content": {"type": "array"}
      },
      "required": ["status"]
    }
    """
    config: dict[str, Any] = {}
    start_lat = payload.get("startLat")
    start_lng = payload.get("startLng")
    end_lat = payload.get("endLat")
    end_lng = payload.get("endLng")
    for key, value in {
        "startLat": start_lat,
        "startLng": start_lng,
        "endLat": end_lat,
        "endLng": end_lng,
    }.items():
        if value is not None and not isinstance(value, (int, float)):
            return _error(f"{key} must be a number")
    if start_lat is not None and start_lng is not None:
        config["start"] = {"lat": float(start_lat), "lng": float(start_lng)}
    if end_lat is not None and end_lng is not None:
        config["end"] = {"lat": float(end_lat), "lng": float(end_lng)}
    mode = payload.get("mode")
    if mode is not None and not isinstance(mode, str):
        return _error("mode must be a string")
    if mode:
        config["mode"] = mode
    content_mode = payload.get("contentMode")
    if content_mode is not None and not isinstance(content_mode, str):
        return _error("contentMode must be a string")
    return _build_widget_response(
        config,
        "Open the route planner to set start and end points and view directions.",
        resource_uri=_UI_URIS["route"],
        content_mode=content_mode,
    )

def _render_ui_probe(payload: dict[str, Any]) -> ToolResult:
    """Probe MCP-Apps UI rendering support.

    Request schema:
    {
      "type": "object",
      "properties": {
        "resourceUri": {"type": "string"},
        "contentMode": {"type": "string"}
      },
      "required": []
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "status": {"type": "string"},
        "config": {"type": "object"},
        "instructions": {"type": "string"},
        "structuredContent": {"type": "object"},
        "content": {"type": "array"}
      },
      "required": ["status"]
    }
    """
    resource_uri = payload.get("resourceUri") or _UI_URIS["statistics"]
    if not isinstance(resource_uri, str):
        return _error("resourceUri must be a string")
    if not resource_uri.startswith("ui://"):
        return _error("resourceUri must be a ui:// URI")
    content_mode = payload.get("contentMode")
    if content_mode is not None and not isinstance(content_mode, str):
        return _error("contentMode must be a string")
    config = {"resourceUri": resource_uri}
    return _build_widget_response(
        config,
        "Open the UI probe widget to verify MCP-Apps rendering support.",
        resource_uri=resource_uri,
        content_mode=content_mode,
    )


register(
    Tool(
        name="os_apps.render_geography_selector",
        description="Open the MCP-Apps geography selector widget.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_apps.render_geography_selector"},
                "level": {"type": "string"},
                "searchTerm": {"type": "string"},
                "focusName": {"type": "string"},
                "focusLevel": {"type": "string"},
                "multiSelect": {"type": "boolean"},
                "initialLat": {"type": "number"},
                "initialLng": {"type": "number"},
                "initialZoom": {"type": "integer"},
                "contentMode": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "config": {"type": "object"},
                "instructions": {"type": "string"},
                "resourceUri": {"type": "string"},
                "uiResourceUris": {"type": "array", "items": {"type": "string"}},
                "_meta": {"type": "object"},
                "structuredContent": {"type": "object"},
                "content": {"type": "array"},
            },
            "required": ["status", "uiResourceUris"],
        },
        handler=_render_geography_selector,
    )
)

register(
    Tool(
        name="os_apps.render_boundary_explorer",
        description="Open the MCP-Apps boundary explorer widget.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_apps.render_boundary_explorer"},
                "level": {"type": "string"},
                "searchTerm": {"type": "string"},
                "focusName": {"type": "string"},
                "focusLevel": {"type": "string"},
                "detailLevel": {"type": "string"},
                "initialLat": {"type": "number"},
                "initialLng": {"type": "number"},
                "initialZoom": {"type": "integer"},
                "contentMode": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "config": {"type": "object"},
                "instructions": {"type": "string"},
                "resourceUri": {"type": "string"},
                "uiResourceUris": {"type": "array", "items": {"type": "string"}},
                "_meta": {"type": "object"},
                "structuredContent": {"type": "object"},
                "content": {"type": "array"},
            },
            "required": ["status", "uiResourceUris"],
        },
        handler=_render_boundary_explorer,
    )
)

register(
    Tool(
        name="os_apps.render_statistics_dashboard",
        description="Open the MCP-Apps statistics dashboard widget.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_apps.render_statistics_dashboard"},
                "dataset": {"type": "string"},
                "areaCodes": {"type": "array", "items": {"type": "string"}},
                "measure": {"type": "string"},
                "contentMode": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "config": {"type": "object"},
                "instructions": {"type": "string"},
                "resourceUri": {"type": "string"},
                "uiResourceUris": {"type": "array", "items": {"type": "string"}},
                "_meta": {"type": "object"},
                "structuredContent": {"type": "object"},
                "content": {"type": "array"},
            },
            "required": ["status", "uiResourceUris"],
        },
        handler=_render_statistics_dashboard,
    )
)

register(
    Tool(
        name="os_apps.render_feature_inspector",
        description="Open the MCP-Apps feature inspector widget.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_apps.render_feature_inspector"},
                "collectionId": {"type": "string"},
                "featureId": {"type": "string"},
                "linkedIds": {"type": "array", "items": {"type": "string"}},
                "contentMode": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "config": {"type": "object"},
                "instructions": {"type": "string"},
                "resourceUri": {"type": "string"},
                "uiResourceUris": {"type": "array", "items": {"type": "string"}},
                "_meta": {"type": "object"},
                "structuredContent": {"type": "object"},
                "content": {"type": "array"},
            },
            "required": ["status", "uiResourceUris"],
        },
        handler=_render_feature_inspector,
    )
)

register(
    Tool(
        name="os_apps.render_route_planner",
        description="Open the MCP-Apps route planner widget.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_apps.render_route_planner"},
                "startLat": {"type": "number"},
                "startLng": {"type": "number"},
                "endLat": {"type": "number"},
                "endLng": {"type": "number"},
                "mode": {"type": "string"},
                "contentMode": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "config": {"type": "object"},
                "instructions": {"type": "string"},
                "resourceUri": {"type": "string"},
                "uiResourceUris": {"type": "array", "items": {"type": "string"}},
                "_meta": {"type": "object"},
                "structuredContent": {"type": "object"},
                "content": {"type": "array"},
            },
            "required": ["status", "uiResourceUris"],
        },
        handler=_render_route_planner,
    )
)

register(
    Tool(
        name="os_apps.render_ui_probe",
        description="Probe MCP-Apps UI rendering support.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_apps.render_ui_probe"},
                "resourceUri": {"type": "string"},
                "contentMode": {"type": "string"},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "config": {"type": "object"},
                "instructions": {"type": "string"},
                "resourceUri": {"type": "string"},
                "uiResourceUris": {"type": "array", "items": {"type": "string"}},
                "_meta": {"type": "object"},
                "structuredContent": {"type": "object"},
                "content": {"type": "array"},
            },
            "required": ["status", "uiResourceUris"],
        },
        handler=_render_ui_probe,
    )
)

register(
    Tool(
        name="os_apps.log_event",
        description="Log MCP-Apps UI interaction events for tracing.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_apps.log_event"},
                "eventType": {"type": "string"},
                "source": {"type": "string"},
                "payload": {"type": "object"},
                "context": {"type": "object"},
                "timestamp": {"type": "number"},
                "sessionId": {"type": "string"},
            },
            "required": ["eventType"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "eventId": {"type": "string"},
                "timestamp": {"type": "number"},
                "logPath": {"type": ["string", "null"]},
            },
            "required": ["status", "eventId", "timestamp"],
        },
        handler=_log_event,
    )
)
