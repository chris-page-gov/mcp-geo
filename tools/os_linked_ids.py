from __future__ import annotations

from typing import Any

from tools.registry import Tool, register

from .os_common import client


def _linked_ids_get(payload: dict[str, Any]):
    identifier = str(payload.get("identifier", "")).strip()
    if not identifier:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing identifier"}
    # Hypothetical endpoint (OS Linked IDs API)
    status, body = client.get_json("https://api.os.uk/linked-ids/v1/id", {"id": identifier})
    if status != 200:
        return status, body
    # Pass through minimal mapping
    return 200, {"identifiers": body.get("identifiers", body)}

register(Tool(
    name="os_linked_ids.get",
    description="Resolve linked identifiers (UPRN/TOID etc)",
    input_schema={"type":"object","properties":{"tool":{"type":"string","const":"os_linked_ids.get"},"identifier":{"type":"string"}},"required":["identifier"],"additionalProperties":False},
    output_schema={"type":"object","properties":{"identifiers":{"type":["array","object"]}},"required":["identifiers"]},
    handler=_linked_ids_get
))
