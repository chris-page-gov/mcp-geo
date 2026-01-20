from __future__ import annotations

from typing import Any

from tools.registry import Tool, ToolResult, register

_UI_URIS = {
    "geography": "ui://mcp-geo/geography-selector",
    "statistics": "ui://mcp-geo/statistics-dashboard",
    "feature": "ui://mcp-geo/feature-inspector",
    "route": "ui://mcp-geo/route-planner",
}


def _error(message: str) -> ToolResult:
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": message}


def _build_widget_response(uri: str, config: dict[str, Any], instructions: str) -> ToolResult:
    return 200, {
        "status": "ready",
        "config": config,
        "instructions": instructions,
        "uiResourceUris": [uri],
        "_meta": {"uiResourceUris": [uri], "audience": ["user"]},
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
        "uiResourceUris": {"type": "array"},
        "_meta": {"type": "object"}
      },
      "required": ["status", "uiResourceUris"]
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
    return _build_widget_response(
        _UI_URIS["geography"],
        config,
        "Open the geography selector widget to choose areas interactively.",
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
        "uiResourceUris": {"type": "array"},
        "_meta": {"type": "object"}
      },
      "required": ["status", "uiResourceUris"]
    }
    """
    config: dict[str, Any] = {}
    dataset = payload.get("dataset")
    if dataset is not None and not isinstance(dataset, str):
        return _error("dataset must be a string")
    if dataset:
        config["dataset"] = dataset
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
    return _build_widget_response(
        _UI_URIS["statistics"],
        config,
        "Open the statistics dashboard to compare observations across areas.",
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
        "uiResourceUris": {"type": "array"},
        "_meta": {"type": "object"}
      },
      "required": ["status", "uiResourceUris"]
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
    return _build_widget_response(
        _UI_URIS["feature"],
        config,
        "Open the feature inspector to review properties and linked identifiers.",
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
        "uiResourceUris": {"type": "array"},
        "_meta": {"type": "object"}
      },
      "required": ["status", "uiResourceUris"]
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
    return _build_widget_response(
        _UI_URIS["route"],
        config,
        "Open the route planner to set start and end points and view directions.",
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
                "uiResourceUris": {"type": "array"},
                "_meta": {"type": "object"},
            },
            "required": ["status", "uiResourceUris"],
        },
        handler=_render_geography_selector,
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
                "uiResourceUris": {"type": "array"},
                "_meta": {"type": "object"},
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
                "uiResourceUris": {"type": "array"},
                "_meta": {"type": "object"},
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
                "uiResourceUris": {"type": "array"},
                "_meta": {"type": "object"},
            },
            "required": ["status", "uiResourceUris"],
        },
        handler=_render_route_planner,
    )
)
