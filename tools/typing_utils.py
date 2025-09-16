from __future__ import annotations

from typing import Any


def parse_float(value: Any) -> float:
    """Best-effort float conversion returning 0.0 on failure.
    Accepts str/int/float; None or invalid strings map to 0.0.
    """
    if value is None:
        return 0.0
    try:
        if isinstance(value, (int, float)):
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
