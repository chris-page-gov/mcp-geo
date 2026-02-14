import hashlib
import re
from collections.abc import Iterable, Mapping
from typing import Any


_ALLOWED_TOOL_NAME_RE = re.compile(r"[^A-Za-z0-9_-]")


def sanitize_tool_name(name: str, seen: Mapping[str, str]) -> str:
    """Sanitize a tool name to a restricted-character form.

    Matches the STDIO adapter behavior:
    - Replace non [A-Za-z0-9_-] with underscore
    - Ensure <= 64 chars (suffix with short sha1 digest when truncating)
    - Resolve collisions by suffixing digest
    """

    base = _ALLOWED_TOOL_NAME_RE.sub("_", name)
    if not base:
        base = "tool"

    candidate = base
    if len(candidate) > 64:
        digest = hashlib.sha1(name.encode()).hexdigest()[:8]
        max_prefix = 64 - 1 - len(digest)
        candidate = f"{candidate[:max_prefix]}_{digest}"

    if candidate in seen and seen[candidate] != name:
        digest = hashlib.sha1(name.encode()).hexdigest()[:8]
        max_prefix = 64 - 1 - len(digest)
        candidate = f"{base[:max_prefix]}_{digest}"

    return candidate


def build_tool_name_maps(
    originals: Iterable[str],
) -> tuple[dict[str, str], dict[str, str]]:
    original_to_sanitized: dict[str, str] = {}
    sanitized_to_original: dict[str, str] = {}

    for original in originals:
        sanitized = sanitize_tool_name(original, sanitized_to_original)
        original_to_sanitized[original] = sanitized
        sanitized_to_original[sanitized] = original

    return original_to_sanitized, sanitized_to_original


def resolve_tool_name(requested: str, originals: Iterable[str]) -> str:
    """Resolve a requested tool name to a canonical/original name.

    - If `requested` is already an original, returns it.
    - If `requested` matches a sanitized alias, returns the corresponding original.
    - If `requested` is a display-style alias (case/spacing/punctuation variants),
      normalize and resolve it to the same canonical tool.
    - Otherwise returns `requested` unchanged.
    """

    original_set = set(originals)
    if requested in original_set:
        return requested

    requested_stripped = requested.strip()
    if requested_stripped in original_set:
        return requested_stripped

    original_casefold = {name.casefold(): name for name in original_set}
    direct_casefold = original_casefold.get(requested_stripped.casefold())
    if direct_casefold is not None:
        return direct_casefold

    _original_to_sanitized, sanitized_to_original = build_tool_name_maps(original_set)
    direct = sanitized_to_original.get(requested_stripped)
    if direct is not None:
        return direct

    sanitized_casefold = {alias.casefold(): original for alias, original in sanitized_to_original.items()}

    # Accept display labels such as "Os names find" and punctuation variants.
    normalized = _ALLOWED_TOOL_NAME_RE.sub("_", requested_stripped)
    normalized_collapsed = re.sub(r"_+", "_", normalized).strip("_")
    candidates = (
        requested_stripped.casefold(),
        normalized,
        normalized.casefold(),
        normalized_collapsed,
        normalized_collapsed.casefold(),
    )
    for candidate in candidates:
        if not candidate:
            continue
        resolved = sanitized_to_original.get(candidate)
        if resolved is not None:
            return resolved
        resolved = sanitized_casefold.get(candidate.casefold())
        if resolved is not None:
            return resolved

    return requested


def rewrite_tool_schema(
    schema: dict[str, Any],
    *,
    sanitized_name: str,
    original_name: str,
) -> dict[str, Any]:
    if not isinstance(schema, dict):
        return schema
    props = schema.get("properties")
    if not isinstance(props, dict):
        return schema
    tool_prop = props.get("tool")
    if not isinstance(tool_prop, dict):
        return schema
    updated_tool = dict(tool_prop)
    if "const" in updated_tool:
        updated_tool["const"] = sanitized_name
    if "enum" in updated_tool and isinstance(updated_tool["enum"], list):
        updated_tool["enum"] = [
            sanitized_name if item == original_name else item for item in updated_tool["enum"]
        ]
    new_props = dict(props)
    new_props["tool"] = updated_tool
    new_schema = dict(schema)
    new_schema["properties"] = new_props
    return new_schema
