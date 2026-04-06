from __future__ import annotations

from server.landis import archive_item_detail, get_landis_archive_item, list_landis_archive_items
from tools.landis_common import error, paginate, parse_limit, parse_offset, registry_payload
from tools.registry import Tool, ToolResult, register


def _list_items(payload: dict[str, object]) -> ToolResult:
    limit = parse_limit(payload.get("limit"))
    if limit is None:
        return error("limit must be an integer between 1 and 100")
    offset = parse_offset(payload.get("offset"))
    if offset is None:
        return error("offset must be a non-negative integer")
    q = payload.get("q")
    family = payload.get("family")
    surfacing_class = payload.get("surfacingClass")
    if q is not None and not isinstance(q, str):
        return error("q must be a string")
    if family is not None and not isinstance(family, str):
        return error("family must be a string")
    if surfacing_class is not None and not isinstance(surfacing_class, str):
        return error("surfacingClass must be a string")

    items = []
    search = q.strip().lower() if isinstance(q, str) else None
    family_filter = family.strip().lower() if isinstance(family, str) else None
    surfacing_filter = surfacing_class.strip().lower() if isinstance(surfacing_class, str) else None
    for item in list_landis_archive_items():
        if family_filter and str(item.get("runtimeFamily") or "").lower() != family_filter:
            continue
        if surfacing_filter and str(item.get("surfacingClass") or "").lower() != surfacing_filter:
            continue
        if search:
            haystack = " ".join(
                [
                    str(item.get("archiveId") or ""),
                    str(item.get("title") or ""),
                    str(item.get("itemType") or ""),
                    str(item.get("runtimeFamily") or ""),
                    " ".join(str(tag) for tag in item.get("tags", []) if isinstance(tag, str)),
                ]
            ).lower()
            if search not in haystack:
                continue
        items.append(
            {
                "archiveId": item.get("archiveId"),
                "title": item.get("title"),
                "itemType": item.get("itemType"),
                "runtimeFamily": item.get("runtimeFamily"),
                "surfacingClass": item.get("surfacingClass"),
                "recordCount": item.get("recordCount"),
                "geometryType": item.get("geometryType"),
                "serviceUrl": item.get("serviceUrl"),
                "tags": item.get("tags", []),
            }
        )

    page, next_page = paginate(items, limit=limit, offset=offset)
    return 200, {
        "items": page,
        "nextPageToken": next_page,
        "totalCount": len(items),
        "registry": registry_payload(),
    }


def _get_item(payload: dict[str, object]) -> ToolResult:
    archive_id = payload.get("archiveId")
    if not isinstance(archive_id, str) or not archive_id.strip():
        return error("archiveId is required")
    item = get_landis_archive_item(archive_id)
    if item is None:
        return error("Unknown LandIS archive item", code="NOT_FOUND", status=404)
    return 200, {
        "item": archive_item_detail(item),
        "registry": registry_payload(),
    }


register(
    Tool(
        name="landis_archive.list_items",
        description="List locally mirrored LandIS archive items and their triage classification.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_archive.list_items"},
                "q": {"type": "string"},
                "family": {"type": "string"},
                "surfacingClass": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "offset": {"oneOf": [{"type": "integer", "minimum": 0}, {"type": "string"}]},
            },
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        handler=_list_items,
    )
)

register(
    Tool(
        name="landis_archive.get_item",
        description="Get detail for one locally mirrored LandIS archive item.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_archive.get_item"},
                "archiveId": {"type": "string"},
            },
            "required": ["archiveId"],
            "additionalProperties": False,
        },
        output_schema={"type": "object"},
        handler=_get_item,
    )
)
