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

    lookup_inputs = [requested_stripped]
    # Accept client-side server-qualified aliases like "mcp-geo:os_places_search"
    # or "mcp-geo/os_places_search".
    for separator in (":", "/"):
        if separator not in requested_stripped:
            continue
        first = requested_stripped.split(separator, 1)[1].strip()
        last = requested_stripped.rsplit(separator, 1)[1].strip()
        for candidate in (first, last):
            if candidate and candidate not in lookup_inputs:
                lookup_inputs.append(candidate)

    original_casefold = {name.casefold(): name for name in original_set}
    _original_to_sanitized, sanitized_to_original = build_tool_name_maps(original_set)
    sanitized_casefold = {alias.casefold(): original for alias, original in sanitized_to_original.items()}

    for lookup in lookup_inputs:
        if lookup in original_set:
            return lookup

        direct_casefold = original_casefold.get(lookup.casefold())
        if direct_casefold is not None:
            return direct_casefold

        direct = sanitized_to_original.get(lookup)
        if direct is not None:
            return direct

        # Accept display labels such as "Os names find" and punctuation variants.
        normalized = _ALLOWED_TOOL_NAME_RE.sub("_", lookup)
        normalized_collapsed = re.sub(r"_+", "_", normalized).strip("_")
        candidates = (
            lookup.casefold(),
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
    return _flatten_top_level_schema_combinators(new_schema)


def _flatten_top_level_schema_combinators(schema: dict[str, Any]) -> dict[str, Any]:
    if schema.get("type") != "object":
        return schema

    combinator_keys = [key for key in ("oneOf", "anyOf", "allOf") if key in schema]
    if not combinator_keys:
        return schema

    new_schema = dict(schema)
    required = new_schema.get("required")
    merged_required = (
        [item for item in required if isinstance(item, str)]
        if isinstance(required, list)
        else []
    )
    notes: list[str] = []

    for key in combinator_keys:
        variants = new_schema.pop(key, None)
        if not isinstance(variants, list):
            notes.append(f"Top-level {key} was removed for client compatibility.")
            continue

        variant_required_sets: list[list[str]] = []
        simple_required_only = True
        for variant in variants:
            if not isinstance(variant, dict):
                simple_required_only = False
                break
            extra_keys = set(variant) - {"required", "description", "title"}
            if extra_keys:
                simple_required_only = False
                break
            variant_required = variant.get("required", [])
            if not isinstance(variant_required, list) or not all(
                isinstance(item, str) for item in variant_required
            ):
                simple_required_only = False
                break
            variant_required_sets.append(variant_required)

        if simple_required_only and variant_required_sets:
            if key == "allOf":
                for variant_required in variant_required_sets:
                    for item in variant_required:
                        if item not in merged_required:
                            merged_required.append(item)
            option_text = " or ".join(
                " + ".join(items) if items else "(no additional required fields)"
                for items in variant_required_sets
            )
            notes.append(
                f"Client compatibility note: top-level {key} was flattened; valid input should "
                f"satisfy {option_text}. Server-side validation still enforces the exact rule."
            )
        else:
            notes.append(
                f"Client compatibility note: top-level {key} was flattened for strict clients; "
                "server-side validation still enforces the full original schema."
            )

    if merged_required:
        new_schema["required"] = merged_required

    if notes:
        description = new_schema.get("description")
        if isinstance(description, str) and description.strip():
            new_schema["description"] = f"{description} {' '.join(notes)}"
        else:
            new_schema["description"] = " ".join(notes)

    return new_schema
