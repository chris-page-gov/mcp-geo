from __future__ import annotations

from typing import Any

from server.mcp.resource_catalog import (
    DATA_RESOURCE_PREFIX,
    load_data_content,
    load_skill_content,
    load_ui_content,
    resolve_data_resource,
    resolve_skill_resource,
    resolve_ui_resource,
)

RESOURCE_URI_PREFIXES = ("resource://", "ui://", "skills://")
_INTERNAL_META_KEYS = {"path", "aliasPath"}


def is_resource_uri(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(RESOURCE_URI_PREFIXES)


def sanitize_resource_meta(meta: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(meta, dict):
        return None
    sanitized = {key: value for key, value in meta.items() if key not in _INTERNAL_META_KEYS}
    return sanitized or None


def resource_mime_from_entry(entry: dict[str, Any], meta: dict[str, Any] | None) -> str:
    if isinstance(meta, dict):
        value = meta.get("mimeType")
        if isinstance(value, str) and value.strip():
            return value
    entry_mime = entry.get("mimeType")
    if isinstance(entry_mime, str) and entry_mime.strip():
        return entry_mime
    return "application/json"


def read_resource_content(
    *,
    name: str | None = None,
    uri: str | None = None,
    asset_mode: str = "relative",
) -> dict[str, Any]:
    if uri is not None and not isinstance(uri, str):
        raise ValueError("uri must be a string")
    if name is not None and not isinstance(name, str):
        raise ValueError("name must be a string")
    if not name and not uri:
        raise ValueError("Missing resource name or uri")

    if uri:
        if uri.startswith(DATA_RESOURCE_PREFIX):
            entry = resolve_data_resource(uri)
            if entry:
                content, etag, meta = load_data_content(entry)
                return {
                    "uri": uri,
                    "mimeType": resource_mime_from_entry(entry, meta),
                    "text": content,
                    "etag": etag,
                    "_meta": sanitize_resource_meta(meta),
                    "kind": "data",
                    "slug": entry.get("slug"),
                }
            raise LookupError(f"Unknown resource '{uri}'")
        ui_entry = resolve_ui_resource(uri)
        if ui_entry:
            content, etag = load_ui_content(ui_entry, asset_mode=asset_mode)
            return {
                "uri": ui_entry["uri"],
                "mimeType": ui_entry["mimeType"],
                "text": content,
                "etag": etag,
                "_meta": sanitize_resource_meta(ui_entry.get("resourceMeta")),
                "kind": "ui",
            }
        skill_entry = resolve_skill_resource(uri)
        if skill_entry:
            content, etag = load_skill_content()
            return {
                "uri": skill_entry["uri"],
                "mimeType": skill_entry["mimeType"],
                "text": content,
                "etag": etag,
                "_meta": None,
                "kind": "skill",
            }
        raise LookupError(f"Unknown resource '{uri}'")

    assert name is not None
    ui_entry = resolve_ui_resource(name)
    if ui_entry:
        content, etag = load_ui_content(ui_entry, asset_mode=asset_mode)
        return {
            "uri": ui_entry["uri"],
            "mimeType": ui_entry["mimeType"],
            "text": content,
            "etag": etag,
            "_meta": sanitize_resource_meta(ui_entry.get("resourceMeta")),
            "kind": "ui",
        }
    skill_entry = resolve_skill_resource(name)
    if skill_entry:
        content, etag = load_skill_content()
        return {
            "uri": skill_entry["uri"],
            "mimeType": skill_entry["mimeType"],
            "text": content,
            "etag": etag,
            "_meta": None,
            "kind": "skill",
        }
    if name.startswith(DATA_RESOURCE_PREFIX) or resolve_data_resource(name):
        entry = resolve_data_resource(name)
        if entry:
            content, etag, meta = load_data_content(entry)
            resolved_uri = (
                name
                if name.startswith(DATA_RESOURCE_PREFIX)
                else f"{DATA_RESOURCE_PREFIX}{entry.get('slug', '')}"
            )
            return {
                "uri": resolved_uri,
                "mimeType": resource_mime_from_entry(entry, meta),
                "text": content,
                "etag": etag,
                "_meta": sanitize_resource_meta(meta),
                "kind": "data",
                "slug": entry.get("slug"),
            }
    raise LookupError(f"Unknown resource '{name}'")


def read_result_payload(resource: dict[str, Any]) -> dict[str, Any]:
    item: dict[str, Any] = {"uri": resource["uri"], "text": resource["text"]}
    mime_type = resource.get("mimeType")
    if isinstance(mime_type, str) and mime_type.strip():
        item["mimeType"] = mime_type
    meta = sanitize_resource_meta(resource.get("_meta"))
    if meta:
        item["_meta"] = meta
    return {"contents": [item]}
