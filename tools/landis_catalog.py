from __future__ import annotations

from typing import Any

from server.landis import list_landis_products
from tools.landis_common import (
    error,
    paginate,
    parse_limit,
    parse_offset,
    product_summary,
    registry_payload,
)
from tools.registry import Tool, ToolResult, register


def _list_products(payload: dict[str, Any]) -> ToolResult:
    limit = parse_limit(payload.get("limit"))
    if limit is None:
        return error("limit must be an integer between 1 and 100")
    offset = parse_offset(payload.get("pageToken") or payload.get("offset"))
    if offset is None:
        return error("pageToken/offset must be a non-negative integer")

    query = payload.get("q")
    if query is not None and not isinstance(query, str):
        return error("q must be a string when provided")
    family = payload.get("family")
    if family is not None and not isinstance(family, str):
        return error("family must be a string when provided")

    query_text = query.strip().lower() if isinstance(query, str) else ""
    family_text = family.strip().lower() if isinstance(family, str) else ""

    products = []
    for product in list_landis_products():
        if family_text:
            current_family = str(product.get("family") or "").strip().lower()
            if current_family != family_text:
                continue
        if query_text:
            haystack = " ".join(
                str(product.get(key, ""))
                for key in ("id", "title", "family", "abstract", "coverage", "accessTier")
            ).lower()
            tags = product.get("tags")
            if isinstance(tags, list):
                haystack = f"{haystack} {' '.join(str(item) for item in tags)}"
            if query_text not in haystack:
                continue
        products.append(product_summary(product))

    page, next_page_token = paginate(products, limit, offset)
    return 200, {
        "products": page,
        "count": len(page),
        "total": len(products),
        "nextPageToken": next_page_token,
        "registry": registry_payload(),
    }


register(
    Tool(
        name="landis_catalog.list_products",
        description=(
            "List the LandIS MVP product registry with coverage, access tier, "
            "and resource hints."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_catalog.list_products"},
                "q": {"type": "string"},
                "family": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "pageToken": {"type": ["string", "integer"]},
                "offset": {"type": ["string", "integer"]},
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "products": {"type": "array"},
                "count": {"type": "integer"},
                "total": {"type": "integer"},
                "nextPageToken": {"type": ["string", "null"]},
                "registry": {"type": "object"},
            },
            "required": ["products", "count", "total", "registry"],
            "additionalProperties": False,
        },
        handler=_list_products,
    )
)
