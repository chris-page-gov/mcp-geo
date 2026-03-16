from __future__ import annotations

from typing import Any, TypeGuard


def is_strict_int(value: Any) -> TypeGuard[int]:
    """Return True only for real integers, excluding booleans."""
    return isinstance(value, int) and not isinstance(value, bool)


def is_strict_number(value: Any) -> TypeGuard[int | float]:
    """Return True for int/float inputs, excluding booleans."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def parse_float(value: Any) -> float:
    """Best-effort float conversion returning 0.0 on failure.
    Accepts str/int/float; None or invalid strings map to 0.0.
    """
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return 0.0
    try:
        if is_strict_number(value):
            return float(value)
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return 0.0
            return float(v)
    except Exception:
        return 0.0
    try:
        return float(value)
    except Exception:
        return 0.0
