from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent.parent
UI_DIR = ROOT / "ui"
SKILL_PATH = ROOT / "SKILL.md"

DATA_RESOURCE_PREFIX = "resource://mcp-geo/"


def data_resource_uri(name: str) -> str:
    return f"{DATA_RESOURCE_PREFIX}{name}"


_UI_RESOURCE_DEFS: list[dict[str, Any]] = [
    {
        "uri": "ui://mcp-geo/geography-selector",
        "name": "ui_geography_selector",
        "title": "Geography Selector",
        "description": "Interactive selector for UK administrative areas.",
        "file": "geography_selector.html",
        "mimeType": "text/html;profile=mcp-app",
        "annotations": {
            "audience": ["user"],
            "priority": 1.0,
            "capabilities": ["search", "selection", "hierarchy", "map"],
        },
    },
    {
        "uri": "ui://mcp-geo/statistics-dashboard",
        "name": "ui_statistics_dashboard",
        "title": "Statistics Dashboard",
        "description": "Visual dashboard for ONS observations and comparisons.",
        "file": "statistics_dashboard.html",
        "mimeType": "text/html;profile=mcp-app",
        "annotations": {
            "audience": ["user"],
            "priority": 0.9,
            "capabilities": ["charts", "comparison", "export"],
        },
    },
    {
        "uri": "ui://mcp-geo/feature-inspector",
        "name": "ui_feature_inspector",
        "title": "Feature Inspector",
        "description": "Inspect OS NGD features and linked identifiers.",
        "file": "feature_inspector.html",
        "mimeType": "text/html;profile=mcp-app",
        "annotations": {
            "audience": ["user"],
            "priority": 0.7,
            "capabilities": ["properties", "map", "linked-ids"],
        },
    },
    {
        "uri": "ui://mcp-geo/route-planner",
        "name": "ui_route_planner",
        "title": "Route Planner",
        "description": "Plan routes with waypoints and directions.",
        "file": "route_planner.html",
        "mimeType": "text/html;profile=mcp-app",
        "annotations": {
            "audience": ["user"],
            "priority": 0.8,
            "capabilities": ["routing", "waypoints", "directions"],
        },
    },
]

SKILLS_RESOURCE: dict[str, Any] = {
    "uri": "skills://mcp-geo/getting-started",
    "name": "skills_getting_started",
    "title": "MCP Geo Skills",
    "description": "Getting started guidance for MCP Geo tools and resources.",
    "mimeType": "text/markdown",
    "annotations": {"audience": ["assistant"], "priority": 1.0},
}


def list_ui_resources() -> list[dict[str, Any]]:
    return [
        {
            "uri": entry["uri"],
            "name": entry["name"],
            "title": entry["title"],
            "description": entry["description"],
            "mimeType": entry["mimeType"],
            "annotations": entry["annotations"],
            "type": "ui",
        }
        for entry in _UI_RESOURCE_DEFS
    ]


def list_skill_resources() -> list[dict[str, Any]]:
    return [
        {
            "uri": SKILLS_RESOURCE["uri"],
            "name": SKILLS_RESOURCE["name"],
            "title": SKILLS_RESOURCE["title"],
            "description": SKILLS_RESOURCE["description"],
            "mimeType": SKILLS_RESOURCE["mimeType"],
            "annotations": SKILLS_RESOURCE["annotations"],
            "type": "skills",
        }
    ]


def _etag_from_bytes(content: bytes, variant: str = "") -> str:
    base = content + variant.encode()
    h = hashlib.sha256(base).hexdigest()[:16]
    return f'W/"{h}"'


def resolve_ui_resource(identifier: str) -> Optional[dict[str, Any]]:
    for entry in _UI_RESOURCE_DEFS:
        if identifier in (entry["uri"], entry["name"]):
            return entry
    return None


def resolve_skill_resource(identifier: str) -> Optional[dict[str, Any]]:
    if identifier in (SKILLS_RESOURCE["uri"], SKILLS_RESOURCE["name"]):
        return SKILLS_RESOURCE
    return None


def load_ui_content(entry: dict[str, Any]) -> tuple[str, str]:
    path = UI_DIR / entry["file"]
    content = path.read_text(encoding="utf-8")
    etag = _etag_from_bytes(content.encode("utf-8"), entry["uri"])
    return content, etag


def load_skill_content() -> tuple[str, str]:
    content = SKILL_PATH.read_text(encoding="utf-8")
    etag = _etag_from_bytes(content.encode("utf-8"), SKILLS_RESOURCE["uri"])
    return content, etag


__all__ = [
    "DATA_RESOURCE_PREFIX",
    "SKILL_PATH",
    "SKILLS_RESOURCE",
    "UI_DIR",
    "data_resource_uri",
    "list_skill_resources",
    "list_ui_resources",
    "load_skill_content",
    "load_ui_content",
    "resolve_skill_resource",
    "resolve_ui_resource",
]
