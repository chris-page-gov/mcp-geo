from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from server.config import settings
from tools.os_common import client
from tools.os_delivery import (
    now_utc_iso,
    parse_delivery,
    parse_inline_max_bytes,
    payload_bytes,
    select_delivery_mode,
    write_resource_payload,
)
from tools.registry import Tool, ToolResult, register

_DOWNLOADS_BASE = "https://api.os.uk/downloads/v1"
_DEFAULT_LIMIT = 50
_MAX_LIMIT = 500
_EXPORT_STORE: dict[str, dict[str, Any]] = {}


def _invalid(message: str) -> ToolResult:
    return 400, {"isError": True, "code": "INVALID_INPUT", "message": message}


def _integration_error(message: str) -> ToolResult:
    return 500, {"isError": True, "code": "INTEGRATION_ERROR", "message": message}


def _downloads_get(path: str, params: dict[str, Any] | None = None) -> ToolResult:
    return client.get_json(f"{_DOWNLOADS_BASE}{path}", params)


def _parse_limit(value: Any) -> int | None:
    if value is None:
        return _DEFAULT_LIMIT
    if isinstance(value, int) and 1 <= value <= _MAX_LIMIT:
        return value
    return None


def _parse_offset(value: Any) -> int | None:
    if value is None:
        return 0
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        if text.isdigit():
            return int(text)
    return None


def _paginate(items: list[dict[str, Any]], limit: int, offset: int) -> tuple[list[dict[str, Any]], str | None]:
    sliced = items[offset: offset + limit]
    next_offset = offset + limit
    next_page = str(next_offset) if next_offset < len(items) else None
    return sliced, next_page


def _delivery_response(
    *,
    response_prefix: str,
    payload: dict[str, Any],
    requested_delivery: str,
    inline_max_bytes: int,
    include_stream_hint: bool = False,
) -> ToolResult:
    size = payload_bytes(payload)
    mode = select_delivery_mode(
        requested_delivery=requested_delivery,
        payload_bytes=size,
        inline_max_bytes=inline_max_bytes,
    )
    if mode == "inline":
        inline_payload = dict(payload)
        inline_payload["delivery"] = "inline"
        inline_payload["bytes"] = size
        return 200, inline_payload

    export_meta = write_resource_payload(prefix=response_prefix, payload=payload)
    response: dict[str, Any] = {
        "delivery": "resource",
        "resourceUri": export_meta["resourceUri"],
        "bytes": export_meta["bytes"],
        "sha256": export_meta["sha256"],
        "path": export_meta["path"],
    }
    if include_stream_hint:
        response["stream"] = {
            "uri": export_meta["resourceUri"],
            "mode": "resource",
            "chunkBytes": 65536,
            "hint": "Use resources/read with resourceUri to fetch large OS outputs.",
        }
    return 200, response


def _list_products(payload: dict[str, Any]) -> ToolResult:
    status, body = _downloads_get("/products", None)
    if status != 200:
        return status, body
    if not isinstance(body, list):
        return _integration_error("Expected product list from OS Downloads API.")

    query = payload.get("q")
    query_text = str(query).strip().lower() if isinstance(query, str) else ""
    filtered: list[dict[str, Any]] = []
    for item in body:
        if not isinstance(item, dict):
            continue
        if query_text:
            hay = " ".join(
                str(item.get(key, ""))
                for key in ("id", "name", "title", "description", "productType")
            ).lower()
            if query_text not in hay:
                continue
        filtered.append(item)

    limit = _parse_limit(payload.get("limit"))
    if limit is None:
        return _invalid(f"limit must be an integer between 1 and {_MAX_LIMIT}")
    offset = _parse_offset(payload.get("pageToken") or payload.get("offset"))
    if offset is None:
        return _invalid("pageToken/offset must be a non-negative integer")
    page, next_page_token = _paginate(filtered, limit, offset)
    return 200, {
        "products": page,
        "count": len(page),
        "total": len(filtered),
        "limit": limit,
        "offset": offset,
        "nextPageToken": next_page_token,
        "live": True,
    }


def _get_product(payload: dict[str, Any]) -> ToolResult:
    product_id = str(payload.get("productId", "")).strip()
    if not product_id:
        return _invalid("productId is required")
    status, body = _downloads_get(f"/products/{product_id}", None)
    if status != 200:
        return status, body
    if not isinstance(body, dict):
        return _integration_error("Expected product object from OS Downloads API.")
    return 200, {"product": body, "live": True}


def _list_product_downloads(payload: dict[str, Any]) -> ToolResult:
    product_id = str(payload.get("productId", "")).strip()
    if not product_id:
        return _invalid("productId is required")
    status, body = _downloads_get(f"/products/{product_id}/downloads", None)
    if status != 200:
        return status, body
    if not isinstance(body, list):
        return _integration_error("Expected downloads list from OS Downloads API.")

    limit = _parse_limit(payload.get("limit"))
    if limit is None:
        return _invalid(f"limit must be an integer between 1 and {_MAX_LIMIT}")
    offset = _parse_offset(payload.get("pageToken") or payload.get("offset"))
    if offset is None:
        return _invalid("pageToken/offset must be a non-negative integer")
    page, next_page_token = _paginate([item for item in body if isinstance(item, dict)], limit, offset)

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _invalid(max_err)

    response_payload = {
        "productId": product_id,
        "downloads": page,
        "count": len(page),
        "total": len(body),
        "limit": limit,
        "offset": offset,
        "nextPageToken": next_page_token,
        "live": True,
    }
    return _delivery_response(
        response_prefix=f"os-downloads-{product_id}-downloads",
        payload=response_payload,
        requested_delivery=delivery or "auto",
        inline_max_bytes=inline_max_bytes or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
        include_stream_hint=True,
    )


def _list_data_packages(payload: dict[str, Any]) -> ToolResult:
    status, body = _downloads_get("/dataPackages", None)
    if status != 200:
        return status, body
    if not isinstance(body, list):
        return _integration_error("Expected dataPackages list from OS Downloads API.")

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _invalid(max_err)

    response_payload = {
        "dataPackages": [item for item in body if isinstance(item, dict)],
        "count": len(body),
        "live": True,
    }
    return _delivery_response(
        response_prefix="os-downloads-data-packages",
        payload=response_payload,
        requested_delivery=delivery or "auto",
        inline_max_bytes=inline_max_bytes or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
        include_stream_hint=True,
    )


def _expiry_iso(created_at_epoch: float) -> str | None:
    ttl = float(getattr(settings, "OS_DATA_CACHE_TTL", 3600.0) or 0.0)
    if ttl <= 0:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created_at_epoch + ttl))


def _prepare_export(payload: dict[str, Any]) -> ToolResult:
    product_id = str(payload.get("productId", "")).strip()
    if not product_id:
        return _invalid("productId is required")

    filename_contains = payload.get("filenameContains")
    if filename_contains is not None and not isinstance(filename_contains, str):
        return _invalid("filenameContains must be a string when provided")
    q_text = filename_contains.strip().lower() if isinstance(filename_contains, str) else ""

    status, body = _downloads_get(f"/products/{product_id}/downloads", None)
    if status != 200:
        return status, body
    if not isinstance(body, list):
        return _integration_error("Expected downloads list from OS Downloads API.")

    filtered: list[dict[str, Any]] = []
    for item in body:
        if not isinstance(item, dict):
            continue
        if q_text:
            hay = " ".join(
                str(item.get(key, ""))
                for key in ("name", "fileName", "format", "description", "id")
            ).lower()
            if q_text not in hay:
                continue
        filtered.append(item)

    export_id = uuid4().hex
    created_at_epoch = time.time()
    created_at = now_utc_iso()
    expires_at = _expiry_iso(created_at_epoch)
    export_payload = {
        "exportId": export_id,
        "productId": product_id,
        "createdAt": created_at,
        "expiresAt": expires_at,
        "itemCount": len(filtered),
        "downloads": filtered,
        "live": True,
    }

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="resource")
    if delivery_err:
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _invalid(max_err)
    chosen_delivery = select_delivery_mode(
        requested_delivery=delivery or "resource",
        payload_bytes=payload_bytes(export_payload),
        inline_max_bytes=inline_max_bytes or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
    )

    resource_meta: dict[str, Any] | None = None
    if chosen_delivery == "resource":
        resource_meta = write_resource_payload(
            prefix=f"os-downloads-export-{export_id}",
            payload=export_payload,
        )

    _EXPORT_STORE[export_id] = {
        "createdAt": created_at,
        "expiresAt": expires_at,
        "payload": export_payload,
        "resourceMeta": resource_meta,
    }

    response: dict[str, Any] = {
        "exportId": export_id,
        "state": "completed",
        "createdAt": created_at,
        "expiresAt": expires_at,
        "itemCount": len(filtered),
        "delivery": chosen_delivery,
        "live": True,
    }
    if resource_meta:
        response["resourceUri"] = resource_meta["resourceUri"]
        response["bytes"] = resource_meta["bytes"]
        response["sha256"] = resource_meta["sha256"]
        response["stream"] = {
            "uri": resource_meta["resourceUri"],
            "mode": "resource",
            "chunkBytes": 65536,
            "hint": "Use resources/read with resourceUri to fetch large OS outputs.",
        }
    else:
        response["export"] = export_payload
        response["bytes"] = payload_bytes(export_payload)
    return 200, response


def _get_export(payload: dict[str, Any]) -> ToolResult:
    export_id = str(payload.get("exportId", "")).strip()
    if not export_id:
        return _invalid("exportId is required")
    stored = _EXPORT_STORE.get(export_id)
    if stored is None:
        return 404, {"isError": True, "code": "NOT_FOUND", "message": "Export not found"}

    export_payload = stored.get("payload")
    if not isinstance(export_payload, dict):
        return _integration_error("Stored export payload is invalid.")
    resource_meta = stored.get("resourceMeta")

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        return _invalid(max_err)
    chosen_delivery = select_delivery_mode(
        requested_delivery=delivery or "auto",
        payload_bytes=payload_bytes(export_payload),
        inline_max_bytes=inline_max_bytes or int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000)),
    )

    if chosen_delivery == "resource":
        if not isinstance(resource_meta, dict):
            resource_meta = write_resource_payload(
                prefix=f"os-downloads-export-{export_id}",
                payload=export_payload,
            )
            stored["resourceMeta"] = resource_meta
        return 200, {
            "exportId": export_id,
            "state": "completed",
            "createdAt": stored.get("createdAt"),
            "expiresAt": stored.get("expiresAt"),
            "delivery": "resource",
            "resourceUri": resource_meta["resourceUri"],
            "bytes": resource_meta["bytes"],
            "sha256": resource_meta["sha256"],
            "live": True,
        }

    return 200, {
        "exportId": export_id,
        "state": "completed",
        "createdAt": stored.get("createdAt"),
        "expiresAt": stored.get("expiresAt"),
        "delivery": "inline",
        "bytes": payload_bytes(export_payload),
        "export": export_payload,
        "live": True,
    }


register(
    Tool(
        name="os_downloads.list_products",
        description="List OS Downloads products with optional local query filtering.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_downloads.list_products"},
                "q": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_LIMIT},
                "offset": {"type": ["integer", "string"]},
                "pageToken": {"type": ["integer", "string"]},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "products": {"type": "array"},
                "count": {"type": "integer"},
                "total": {"type": "integer"},
                "nextPageToken": {"type": ["string", "null"]},
            },
            "required": ["products", "count", "total"],
            "additionalProperties": True,
        },
        handler=_list_products,
    )
)

register(
    Tool(
        name="os_downloads.get_product",
        description="Get OS Downloads product metadata by productId.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_downloads.get_product"},
                "productId": {"type": "string"},
            },
            "required": ["productId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {"product": {"type": "object"}},
            "required": ["product"],
            "additionalProperties": True,
        },
        handler=_get_product,
    )
)

register(
    Tool(
        name="os_downloads.list_product_downloads",
        description="List download entries for a specific OS Downloads product.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_downloads.list_product_downloads"},
                "productId": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": _MAX_LIMIT},
                "offset": {"type": ["integer", "string"]},
                "pageToken": {"type": ["integer", "string"]},
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": ["productId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "downloads": {"type": "array"},
                "count": {"type": "integer"},
                "total": {"type": "integer"},
                "nextPageToken": {"type": ["string", "null"]},
                "delivery": {"type": "string"},
                "resourceUri": {"type": "string"},
            },
            "required": ["delivery"],
            "additionalProperties": True,
        },
        handler=_list_product_downloads,
    )
)

register(
    Tool(
        name="os_downloads.list_data_packages",
        description="List account-specific OS data packages (permission dependent).",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_downloads.list_data_packages"},
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": [],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "dataPackages": {"type": "array"},
                "count": {"type": "integer"},
                "delivery": {"type": "string"},
            },
            "required": ["delivery"],
            "additionalProperties": True,
        },
        handler=_list_data_packages,
    )
)

register(
    Tool(
        name="os_downloads.prepare_export",
        description="Prepare an OS downloads export payload and return inline or resource delivery metadata.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_downloads.prepare_export"},
                "productId": {"type": "string"},
                "filenameContains": {"type": "string"},
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": ["productId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "exportId": {"type": "string"},
                "state": {"type": "string"},
                "delivery": {"type": "string"},
                "resourceUri": {"type": "string"},
            },
            "required": ["exportId", "state", "delivery"],
            "additionalProperties": True,
        },
        handler=_prepare_export,
    )
)

register(
    Tool(
        name="os_downloads.get_export",
        description="Retrieve a previously prepared OS downloads export by exportId.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_downloads.get_export"},
                "exportId": {"type": "string"},
                "delivery": {"type": "string", "enum": ["inline", "resource", "auto"]},
                "inlineMaxBytes": {"type": "integer", "minimum": 1},
            },
            "required": ["exportId"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "exportId": {"type": "string"},
                "state": {"type": "string"},
                "delivery": {"type": "string"},
                "resourceUri": {"type": "string"},
            },
            "required": ["exportId", "state", "delivery"],
            "additionalProperties": True,
        },
        handler=_get_export,
    )
)

