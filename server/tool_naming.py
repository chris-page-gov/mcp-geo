import hashlib
import re
from collections.abc import Iterable, Mapping


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
    - Otherwise returns `requested` unchanged.
    """

    original_set = set(originals)
    if requested in original_set:
        return requested

    _original_to_sanitized, sanitized_to_original = build_tool_name_maps(original_set)
    return sanitized_to_original.get(requested, requested)
