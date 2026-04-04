from __future__ import annotations

from typing import Any

from server.landis import get_landis_product
from tools.landis_common import error, product_metadata, product_summary, registry_payload
from tools.registry import Tool, ToolResult, register


def _get_metadata(payload: dict[str, Any]) -> ToolResult:
    product_id = payload.get("productId")
    if not isinstance(product_id, str) or not product_id.strip():
        return error("productId is required")
    product = get_landis_product(product_id)
    if product is None:
        return error("LandIS product not found", code="NOT_FOUND", status=404)
    return 200, {
        "product": product_summary(product),
        "metadata": product_metadata(product),
        "registry": registry_payload(),
    }


register(
    Tool(
        name="landis_metadata.get",
        description="Retrieve LandIS product metadata, provenance notes, and linked resources.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "landis_metadata.get"},
                "productId": {"type": "string"},
            },
            "required": ["productId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "product": {"type": "object"},
                "metadata": {"type": "object"},
                "registry": {"type": "object"},
            },
            "required": ["product", "metadata", "registry"],
            "additionalProperties": False,
        },
        handler=_get_metadata,
    )
)
