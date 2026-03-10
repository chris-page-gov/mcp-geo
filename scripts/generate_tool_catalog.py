#!/usr/bin/env python3
"""Generate a markdown catalog of all registered tools with input/output schemas.

Usage:
  python scripts/generate_tool_catalog.py > docs/tool_catalog.md

The script imports the server tool registry ensuring dynamic imports run,
then emits a markdown table plus detailed sections per tool.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

# Ensure dynamic tool registration executes (mirrors server/mcp/tools.py)
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
    "tools.ons_search",
    "tools.ons_select",
    "tools.ons_codes",
    "tools.nomis_data",
    "tools.os_mcp",
    "tools.os_route",
    "tools.os_apps",
]:
    try:
        importlib.import_module(_mod)
    except Exception:  # pragma: no cover
        pass

from tools.registry import all_tools  # noqa: E402


def fmt_schema(schema: dict[str, Any]) -> str:
    return "```json\n" + json.dumps(schema, indent=2, sort_keys=True) + "\n```"


def main() -> None:
    tools = sorted(all_tools(), key=lambda t: t.name)
    print("# Tool Catalog\n")
    print("Auto-generated list of current tools, their descriptions, versions, and JSON Schemas.\n")
    print("| Tool | Version | Description |")
    print("|------|---------|-------------|")
    for t in tools:
        desc = t.description.replace("|", "\\|")
        print(f"| {t.name} | {t.version} | {desc} |")
    print("\n---\n")
    for t in tools:
        print(f"## {t.name}\n")
        print(f"**Description:** {t.description}\n")
        print(f"**Version:** {t.version}\n")
        print("### Input Schema\n")
        print(fmt_schema(t.input_schema))
        print("### Output Schema\n")
        print(fmt_schema(t.output_schema))
        print("\n")


if __name__ == "__main__":
    main()
