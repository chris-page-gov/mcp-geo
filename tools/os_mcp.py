from __future__ import annotations

from typing import Any

from server import __version__ as SERVER_VERSION
from server.mcp.resource_catalog import SKILLS_RESOURCE, list_ui_resources
from server.mcp.tool_search import get_tool_search_config
from tools.registry import Tool, ToolResult, register


def _descriptor(payload: dict[str, Any]) -> ToolResult:
    """Describe server capabilities and tool search configuration.

    Request schema:
    {
      "type": "object",
      "properties": {
        "category": {"type": "string"},
        "includeTools": {"type": "boolean"}
      },
      "required": []
    }

    Response schema:
    {
      "type": "object",
      "properties": {
        "server": {"type": "string"},
        "version": {"type": "string"},
        "capabilities": {"type": "object"},
        "toolSearch": {"type": "object"},
        "skillsUri": {"type": "string"},
        "uiResources": {"type": "array"},
        "uiResourceCatalog": {"type": "array"}
      },
      "required": ["server", "version", "toolSearch"]
    }
    """
    category = payload.get("category")
    include_tools = payload.get("includeTools", True)
    if category is not None and not isinstance(category, str):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "category must be a string when provided",
        }
    if include_tools is not None and not isinstance(include_tools, bool):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "includeTools must be a boolean when provided",
        }
    tool_search = get_tool_search_config(category if include_tools else None)
    ui_catalog = list_ui_resources()
    return 200, {
        "server": "mcp-geo",
        "version": SERVER_VERSION,
        "capabilities": {
            "toolSearch": True,
            "skills": True,
            "uiResources": True,
        },
        "toolSearch": tool_search,
        "skillsUri": SKILLS_RESOURCE["uri"],
        "uiResources": [entry["uri"] for entry in ui_catalog],
        "uiResourceCatalog": ui_catalog,
    }


register(
    Tool(
        name="os_mcp.descriptor",
        description="Describe server capabilities and tool search configuration.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_mcp.descriptor"},
                "category": {
                    "type": "string",
                    "description": "Optional tool category to filter search config.",
                },
                "includeTools": {
                    "type": "boolean",
                    "description": "Include per-tool metadata in toolSearch section.",
                    "default": True,
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "server": {"type": "string"},
                "version": {"type": "string"},
                "capabilities": {"type": "object"},
                "toolSearch": {"type": "object"},
                "skillsUri": {"type": "string"},
                "uiResources": {"type": "array"},
                "uiResourceCatalog": {"type": "array"},
            },
            "required": ["server", "version", "toolSearch"],
        },
        handler=_descriptor,
    )
)
