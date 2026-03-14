from __future__ import annotations

import json
from typing import Any

from server.mcp.resource_access import read_resource_content
from server.mcp.resource_handoff import (
    DEFAULT_RESOURCE_CHUNK_BYTES,
    MAX_RESOURCE_CHUNK_BYTES,
)
from tools.registry import Tool, register


def _error(message: str, code: str = "INVALID_INPUT") -> tuple[int, dict[str, Any]]:
    return 400, {"isError": True, "code": code, "message": message}


def _parse_page_token(value: Any) -> tuple[int | None, str | None]:
    if value is None or value == "":
        return 0, None
    if isinstance(value, int):
        if value < 0:
            return None, "pageToken must be a non-negative integer offset"
        return value, None
    if not isinstance(value, str):
        return None, "pageToken must be a non-negative integer offset"
    raw = value.strip()
    if not raw:
        return 0, None
    if not raw.isdigit():
        return None, "pageToken must be a non-negative integer offset"
    return int(raw), None


def _parse_max_bytes(value: Any) -> tuple[int | None, str | None]:
    if value is None:
        return DEFAULT_RESOURCE_CHUNK_BYTES, None
    if not isinstance(value, int):
        return None, "maxBytes must be an integer between 1 and 24576"
    if value < 1 or value > MAX_RESOURCE_CHUNK_BYTES:
        return None, "maxBytes must be an integer between 1 and 24576"
    return value, None


def _validate_boundary(encoded: bytes, offset: int) -> bool:
    try:
        encoded[:offset].decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _slice_text(encoded: bytes, start: int, max_bytes: int) -> tuple[str, int]:
    end = min(len(encoded), start + max_bytes)
    while end > start:
        try:
            return encoded[start:end].decode("utf-8"), end
        except UnicodeDecodeError:
            end -= 1
    probe = start + 1
    while probe <= len(encoded):
        try:
            return encoded[start:probe].decode("utf-8"), probe
        except UnicodeDecodeError:
            probe += 1
    return "", start


def _resource_error_payload(resource: dict[str, Any]) -> tuple[int, dict[str, Any]] | None:
    if resource.get("kind") != "data":
        return None
    slug = resource.get("slug")
    if not isinstance(slug, str) or "/" not in slug:
        return None
    if resource.get("mimeType") != "application/json":
        return None
    text = str(resource.get("text") or "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or parsed.get("isError") is not True:
        return None
    code = str(parsed.get("code") or "")
    message = str(parsed.get("message") or "Resource not found")
    if code == "INVALID_INPUT":
        return 400, {"isError": True, "code": code, "message": message}
    if code == "NOT_FOUND":
        return 404, {"isError": True, "code": code, "message": message}
    return None


def _get_resource(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    uri = payload.get("uri")
    name = payload.get("name")
    if uri is not None and not isinstance(uri, str):
        return _error("uri must be a string")
    if name is not None and not isinstance(name, str):
        return _error("name must be a string")
    if not uri and not name:
        return _error("uri or name is required")

    page_token, token_error = _parse_page_token(payload.get("pageToken"))
    if token_error:
        return _error(token_error)
    max_bytes, max_error = _parse_max_bytes(payload.get("maxBytes"))
    if max_error:
        return _error(max_error)

    try:
        resource = read_resource_content(name=name, uri=uri)
    except ValueError as exc:
        return _error(str(exc))
    except LookupError:
        return 404, {"isError": True, "code": "NOT_FOUND", "message": "Resource not found"}

    payload_error = _resource_error_payload(resource)
    if payload_error is not None:
        return payload_error

    text = str(resource["text"])
    encoded = text.encode("utf-8")
    offset = page_token or 0
    if offset > len(encoded):
        return _error("pageToken must not exceed the resource byte length")
    if not _validate_boundary(encoded, offset):
        return _error("pageToken must align to a UTF-8 codepoint boundary")

    chunk_text, next_offset = _slice_text(encoded, offset, max_bytes or DEFAULT_RESOURCE_CHUNK_BYTES)
    complete = next_offset >= len(encoded)
    delivery = "inline" if complete and offset == 0 else "chunked"
    response: dict[str, Any] = {
        "uri": resource["uri"],
        "mimeType": resource["mimeType"],
        "etag": resource["etag"],
        "delivery": delivery,
        "text": chunk_text,
        "pageToken": str(offset) if offset else None,
        "nextPageToken": None if complete else str(next_offset),
        "complete": complete,
        "totalBytes": len(encoded),
    }
    meta = resource.get("_meta")
    if isinstance(meta, dict):
        response["_meta"] = meta
    return 200, response


register(
    Tool(
        name="os_resources.get",
        description="Read an MCP Geo resource by uri or name with transport-safe chunking.",
        input_schema={
            "type": "object",
            "properties": {
                "uri": {"type": "string"},
                "name": {"type": "string"},
                "pageToken": {
                    "type": ["string", "integer"],
                    "description": "UTF-8 byte offset returned by a previous call.",
                },
                "maxBytes": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_RESOURCE_CHUNK_BYTES,
                },
            },
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "uri": {"type": "string"},
                "mimeType": {"type": "string"},
                "etag": {"type": "string"},
                "delivery": {"type": "string"},
                "text": {"type": "string"},
                "pageToken": {"type": ["string", "null"]},
                "nextPageToken": {"type": ["string", "null"]},
                "complete": {"type": "boolean"},
                "totalBytes": {"type": "integer"},
            },
            "required": ["uri", "mimeType", "etag", "delivery", "text", "complete", "totalBytes"],
        },
        handler=_get_resource,
    )
)
