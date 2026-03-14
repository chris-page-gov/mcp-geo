from __future__ import annotations

import os
from typing import Any
from urllib.parse import quote

from server.config import settings
from server.mcp.resource_access import is_resource_uri
from server.mcp.resource_catalog import MCP_APPS_MIME, resolve_data_resource, resolve_skill_resource, resolve_ui_resource

DEFAULT_RESOURCE_CHUNK_BYTES = 16_384
MAX_RESOURCE_CHUNK_BYTES = 24_576

_RESOURCE_URI_KEYS = ("resourceUri", "resultUri", "statusUri", "uri")


def _current_http_auth_mode() -> str:
    mode = (os.getenv("MCP_HTTP_AUTH_MODE", "") or "").strip().lower()
    if not mode:
        if (os.getenv("MCP_HTTP_JWT_HS256_SECRET", "") or "").strip():
            return "hs256_jwt"
        if (os.getenv("MCP_HTTP_AUTH_TOKEN", "") or "").strip():
            return "static_bearer"
        return "off"
    if mode not in {"off", "static_bearer", "hs256_jwt"}:
        return "off"
    return mode


def _resource_name_from_uri(uri: str) -> str:
    trimmed = uri.rstrip("/")
    if "/" not in trimmed:
        return trimmed
    return trimmed.rsplit("/", 1)[-1] or trimmed


def _resource_mime_from_payload(data: dict[str, Any], resource_uri: str) -> str:
    mime_type = data.get("mimeType")
    if isinstance(mime_type, str) and mime_type.strip():
        return mime_type
    content_type = data.get("contentType")
    if isinstance(content_type, str) and content_type.strip():
        return content_type
    stream = data.get("stream")
    if isinstance(stream, dict):
        stream_mime = stream.get("mimeType")
        if isinstance(stream_mime, str) and stream_mime.strip():
            return stream_mime
    if resource_uri.startswith("ui://"):
        return MCP_APPS_MIME
    if resource_uri.startswith("skills://"):
        return "text/markdown"
    if resource_uri.endswith(".csv"):
        return "text/csv"
    if resource_uri.endswith(".txt"):
        return "text/plain"
    return "application/json"


def _primary_resource_uri(data: dict[str, Any]) -> str | None:
    for key in _RESOURCE_URI_KEYS:
        value = data.get(key)
        if is_resource_uri(value):
            return value
    stream = data.get("stream")
    if isinstance(stream, dict) and is_resource_uri(stream.get("uri")):
        return stream["uri"]
    return None


def _http_access(resource_uri: str) -> dict[str, Any] | None:
    if not getattr(settings, "MCP_RESOURCE_HTTP_LINKS_ENABLED", False):
        return None
    base_url = str(getattr(settings, "MCP_PUBLIC_BASE_URL", "") or "").strip().rstrip("/")
    if not base_url:
        return None
    auth_mode = _current_http_auth_mode()
    return {
        "readUrl": f"{base_url}/resources/read?uri={quote(resource_uri, safe='')}",
        "authMode": auth_mode,
        "requiresAuthorization": auth_mode != "off",
    }


def build_resource_handoff(data: dict[str, Any]) -> dict[str, Any] | None:
    resource_uri = _primary_resource_uri(data)
    if resource_uri is None:
        return None
    handoff: dict[str, Any] = {
        "resourceUri": resource_uri,
        "resolverTool": "os_resources.get",
        "resolverArgs": {"uri": resource_uri},
        "protocolMethod": "resources/read",
        "chunking": {
            "pageTokenType": "byte_offset",
            "defaultMaxBytes": DEFAULT_RESOURCE_CHUNK_BYTES,
            "maxBytes": MAX_RESOURCE_CHUNK_BYTES,
        },
        "availableVia": ["resources/read", "os_resources.get"],
        "mimeType": _resource_mime_from_payload(data, resource_uri),
    }
    bytes_value = data.get("bytes")
    if isinstance(bytes_value, int) and bytes_value >= 0:
        handoff["bytes"] = bytes_value
    sha_value = data.get("sha256")
    if isinstance(sha_value, str) and sha_value.strip():
        handoff["sha256"] = sha_value
    http_access = _http_access(resource_uri)
    if http_access is not None:
        handoff["httpAccess"] = http_access
    return handoff


def build_resource_stream_hint(resource_uri: str, *, hint: str) -> dict[str, Any]:
    return {
        "uri": resource_uri,
        "mode": "resource",
        "chunkBytes": DEFAULT_RESOURCE_CHUNK_BYTES,
        "maxBytes": MAX_RESOURCE_CHUNK_BYTES,
        "hint": hint,
    }


def build_resource_link_block(resource_uri: str, mime_type: str) -> dict[str, Any]:
    return {
        "type": "resource_link",
        "name": _resource_name_from_uri(resource_uri),
        "uri": resource_uri,
        "mimeType": mime_type,
    }


def build_resource_handoff_content(
    handoff: dict[str, Any], *, include_resource_link: bool = True
) -> list[dict[str, Any]]:
    resource_uri = str(handoff["resourceUri"])
    mime_type = str(handoff.get("mimeType") or "application/json")
    text = (
        "Large resource output is available via os_resources.get or resources/read "
        f"using {resource_uri}."
    )
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    if include_resource_link:
        content.append(build_resource_link_block(resource_uri, mime_type))
    return content


def _content_has_resource_link(content: list[Any], resource_uri: str) -> bool:
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "resource_link":
            continue
        if block.get("uri") == resource_uri:
            return True
    return False


def _preserve_text_only_override(data: dict[str, Any]) -> bool:
    meta = data.get("_meta")
    return isinstance(meta, dict) and meta.get("uiTextOnlyOverride") is True


def _resource_link_available(resource_uri: str) -> bool:
    if resource_uri.startswith("ui://"):
        return resolve_ui_resource(resource_uri) is not None
    if resource_uri.startswith("skills://"):
        return resolve_skill_resource(resource_uri) is not None
    if resource_uri.startswith("resource://"):
        return resolve_data_resource(resource_uri) is not None
    return False


def decorate_resource_handoff(
    data: dict[str, Any], *, include_resource_link: bool = True
) -> dict[str, Any]:
    handoff = build_resource_handoff(data)
    if handoff is None:
        return data

    decorated = dict(data)
    decorated.setdefault("resourceHandoff", handoff)

    structured = decorated.get("structuredContent")
    if isinstance(structured, dict):
        structured = dict(structured)
        structured.setdefault("resourceHandoff", decorated["resourceHandoff"])
        decorated["structuredContent"] = structured

    content = decorated.get("content")
    if not isinstance(content, list):
        decorated["content"] = build_resource_handoff_content(
            decorated["resourceHandoff"],
            include_resource_link=include_resource_link
            and _resource_link_available(str(decorated["resourceHandoff"]["resourceUri"])),
        )
    elif include_resource_link and not _preserve_text_only_override(decorated):
        resource_uri = str(decorated["resourceHandoff"]["resourceUri"])
        if _resource_link_available(resource_uri) and not _content_has_resource_link(content, resource_uri):
            updated_content = list(content)
            updated_content.append(
                build_resource_link_block(
                    resource_uri,
                    str(decorated["resourceHandoff"].get("mimeType") or "application/json"),
                )
            )
            decorated["content"] = updated_content
    return decorated
