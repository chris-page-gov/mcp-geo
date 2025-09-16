from __future__ import annotations

from typing import Any, cast

from .types import DPAEntry, GazetteerEntry


def get_gaz(result: dict[str, Any]) -> GazetteerEntry:
    gaz = result.get("GAZETTEER_ENTRY", {})
    return cast(GazetteerEntry, gaz)

def get_dpa(result: dict[str, Any]) -> DPAEntry:
    dpa = result.get("DPA", {})
    return cast(DPAEntry, dpa)
