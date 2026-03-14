from __future__ import annotations

import time
from typing import Any
from uuid import uuid4

from server.config import settings
from server.logging import log_export_lifecycle
from server.mcp.resource_handoff import build_resource_stream_hint
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


def _default_inline_max_bytes() -> int:
    return int(getattr(settings, "OS_EXPORT_INLINE_MAX_BYTES", 200_000))


def _log_export_state(
    *,
    tool_name: str,
    state: str,
    export_id: str | None = None,
    product_id: str | None = None,
    delivery: str | None = None,
    bytes_value: int | None = None,
    resource_uri: str | None = None,
    error_code: str | None = None,
    detail: str | None = None,
) -> None:
    log_export_lifecycle(
        service="os_downloads",
        tool_name=tool_name,
        state=state,
        export_id=export_id,
        product_id=product_id,
        delivery=delivery,
        bytes_value=bytes_value,
        resource_uri=resource_uri,
        error_code=error_code,
        detail=detail,
    )


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


def _paginate(
    items: list[dict[str, Any]],
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], str | None]:
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
    }
    if include_stream_hint:
        response["stream"] = build_resource_stream_hint(
            export_meta["resourceUri"],
            hint="Use os_resources.get or resources/read with resourceUri to fetch large OS outputs.",
        )
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
    page, next_page_token = _paginate(
        [item for item in body if isinstance(item, dict)],
        limit,
        offset,
    )

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
        inline_max_bytes=inline_max_bytes or _default_inline_max_bytes(),
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
        inline_max_bytes=inline_max_bytes or _default_inline_max_bytes(),
        include_stream_hint=True,
    )


def _expiry_iso(created_at_epoch: float) -> str | None:
    ttl = float(getattr(settings, "OS_DATA_CACHE_TTL", 3600.0) or 0.0)
    if ttl <= 0:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(created_at_epoch + ttl))


def _prepare_export(payload: dict[str, Any]) -> ToolResult:
    export_id = uuid4().hex
    product_id = str(payload.get("productId", "")).strip()
    if not product_id:
        _log_export_state(
            tool_name="os_downloads.prepare_export",
            state="failed",
            export_id=export_id,
            error_code="INVALID_INPUT",
            detail="productId is required",
        )
        return _invalid("productId is required")
    _log_export_state(
        tool_name="os_downloads.prepare_export",
        state="requested",
        export_id=export_id,
        product_id=product_id,
    )

    filename_contains = payload.get("filenameContains")
    if filename_contains is not None and not isinstance(filename_contains, str):
        _log_export_state(
            tool_name="os_downloads.prepare_export",
            state="failed",
            export_id=export_id,
            product_id=product_id,
            error_code="INVALID_INPUT",
            detail="filenameContains must be a string when provided",
        )
        return _invalid("filenameContains must be a string when provided")
    q_text = filename_contains.strip().lower() if isinstance(filename_contains, str) else ""

    _log_export_state(
        tool_name="os_downloads.prepare_export",
        state="queued",
        export_id=export_id,
        product_id=product_id,
    )
    status, body = _downloads_get(f"/products/{product_id}/downloads", None)
    if status != 200:
        _log_export_state(
            tool_name="os_downloads.prepare_export",
            state="failed",
            export_id=export_id,
            product_id=product_id,
            error_code=(body.get("code") if isinstance(body, dict) else "OS_API_ERROR"),
            detail=(body.get("message") if isinstance(body, dict) else None),
        )
        return status, body
    if not isinstance(body, list):
        _log_export_state(
            tool_name="os_downloads.prepare_export",
            state="failed",
            export_id=export_id,
            product_id=product_id,
            error_code="INTEGRATION_ERROR",
            detail="Expected downloads list from OS Downloads API.",
        )
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
        _log_export_state(
            tool_name="os_downloads.prepare_export",
            state="failed",
            export_id=export_id,
            product_id=product_id,
            error_code="INVALID_INPUT",
            detail=delivery_err,
        )
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        _log_export_state(
            tool_name="os_downloads.prepare_export",
            state="failed",
            export_id=export_id,
            product_id=product_id,
            error_code="INVALID_INPUT",
            detail=max_err,
        )
        return _invalid(max_err)
    chosen_delivery = select_delivery_mode(
        requested_delivery=delivery or "resource",
        payload_bytes=payload_bytes(export_payload),
        inline_max_bytes=inline_max_bytes or _default_inline_max_bytes(),
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
        response["stream"] = build_resource_stream_hint(
            resource_meta["resourceUri"],
            hint="Use os_resources.get or resources/read with resourceUri to fetch large OS outputs.",
        )
    else:
        response["export"] = export_payload
        response["bytes"] = payload_bytes(export_payload)
    _log_export_state(
        tool_name="os_downloads.prepare_export",
        state="completed",
        export_id=export_id,
        product_id=product_id,
        delivery=chosen_delivery,
        bytes_value=(
            response.get("bytes") if isinstance(response.get("bytes"), int) else None
        ),
        resource_uri=(
            response.get("resourceUri")
            if isinstance(response.get("resourceUri"), str)
            else None
        ),
    )
    return 200, response


def _get_export(payload: dict[str, Any]) -> ToolResult:
    export_id = str(payload.get("exportId", "")).strip()
    if not export_id:
        _log_export_state(
            tool_name="os_downloads.get_export",
            state="failed",
            error_code="INVALID_INPUT",
            detail="exportId is required",
        )
        return _invalid("exportId is required")
    _log_export_state(
        tool_name="os_downloads.get_export",
        state="requested",
        export_id=export_id,
    )
    stored = _EXPORT_STORE.get(export_id)
    if stored is None:
        _log_export_state(
            tool_name="os_downloads.get_export",
            state="failed",
            export_id=export_id,
            error_code="NOT_FOUND",
            detail="Export not found",
        )
        return 404, {"isError": True, "code": "NOT_FOUND", "message": "Export not found"}

    export_payload = stored.get("payload")
    if not isinstance(export_payload, dict):
        _log_export_state(
            tool_name="os_downloads.get_export",
            state="failed",
            export_id=export_id,
            error_code="INTEGRATION_ERROR",
            detail="Stored export payload is invalid.",
        )
        return _integration_error("Stored export payload is invalid.")
    resource_meta = stored.get("resourceMeta")

    delivery, delivery_err = parse_delivery(payload.get("delivery"), default="auto")
    if delivery_err:
        _log_export_state(
            tool_name="os_downloads.get_export",
            state="failed",
            export_id=export_id,
            error_code="INVALID_INPUT",
            detail=delivery_err,
        )
        return _invalid(delivery_err)
    inline_max_bytes, max_err = parse_inline_max_bytes(payload.get("inlineMaxBytes"))
    if max_err:
        _log_export_state(
            tool_name="os_downloads.get_export",
            state="failed",
            export_id=export_id,
            error_code="INVALID_INPUT",
            detail=max_err,
        )
        return _invalid(max_err)
    chosen_delivery = select_delivery_mode(
        requested_delivery=delivery or "auto",
        payload_bytes=payload_bytes(export_payload),
        inline_max_bytes=inline_max_bytes or _default_inline_max_bytes(),
    )

    if chosen_delivery == "resource":
        if not isinstance(resource_meta, dict):
            resource_meta = write_resource_payload(
                prefix=f"os-downloads-export-{export_id}",
                payload=export_payload,
            )
            stored["resourceMeta"] = resource_meta
        response = {
            "exportId": export_id,
            "state": "completed",
            "createdAt": stored.get("createdAt"),
            "expiresAt": stored.get("expiresAt"),
            "delivery": "resource",
            "resourceUri": resource_meta["resourceUri"],
            "bytes": resource_meta["bytes"],
            "sha256": resource_meta["sha256"],
            "stream": build_resource_stream_hint(
                resource_meta["resourceUri"],
                hint="Use os_resources.get or resources/read with resourceUri to fetch large OS outputs.",
            ),
            "live": True,
        }
        _log_export_state(
            tool_name="os_downloads.get_export",
            state="completed",
            export_id=export_id,
            delivery="resource",
            bytes_value=response.get("bytes"),
            resource_uri=response.get("resourceUri"),
        )
        return 200, response

    response = {
        "exportId": export_id,
        "state": "completed",
        "createdAt": stored.get("createdAt"),
        "expiresAt": stored.get("expiresAt"),
        "delivery": "inline",
        "bytes": payload_bytes(export_payload),
        "export": export_payload,
        "live": True,
    }
    _log_export_state(
        tool_name="os_downloads.get_export",
        state="completed",
        export_id=export_id,
        delivery="inline",
        bytes_value=response.get("bytes"),
    )
    return 200, response


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
        description=(
            "Prepare an OS downloads export payload and return inline or resource "
            "delivery metadata."
        ),
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
