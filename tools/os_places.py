from __future__ import annotations

import re
import time
from typing import Any

import requests

from server.config import settings
from tools.registry import Tool, register

POSTCODE_REGEX = re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$")


def _by_postcode(payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    postcode_raw = (
        str(payload.get("postcode", ""))
        .strip()
        .upper()
        .replace(" ", "")
    )
    if not POSTCODE_REGEX.match(postcode_raw):
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "Invalid UK postcode",
        }
    api_key = getattr(settings, "OS_API_KEY", None)
    if not api_key:
        return 501, {
            "isError": True,
            "code": "NO_API_KEY",
            "message": "OS_API_KEY not set",
        }
    url = (
        "https://api.os.uk/search/places/v1/postcode?postcode="
        f"{postcode_raw}&key={api_key}"
    )
    try:
        resp = requests.get(url, timeout=5)
    except Exception as exc:  # network / requests errors
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": str(exc),
        }
    if resp.status_code != 200:
        # Normalise non-200s into OS_API_ERROR
        return resp.status_code, {
            "isError": True,
            "code": "OS_API_ERROR",
            "message": f"OS API error: {resp.text[:200]}",
        }
    body = resp.json()
    uprns: list[dict[str, Any]] = []
    for result in body.get("results", []):
        dpa = result.get("DPA", {})
        uprns.append(
            {
                "uprn": dpa.get("UPRN"),
                "address": dpa.get("ADDRESS"),
                "lat": float(dpa.get("LAT", 0) or 0),
                "lon": float(dpa.get("LNG", 0) or 0),
                "classification": dpa.get("CLASS"),
                "local_custodian_code": dpa.get("LOCAL_CUSTODIAN_CODE"),
            }
        )
    return 200, {
        "uprns": uprns,
        "provenance": {
            "source": "os_places",
            "timestamp": body.get("epoch", time.time()),
        },
    }


register(
    Tool(
        name="os_places.by_postcode",
        description=(
            "Lookup UPRNs and addresses for a UK postcode via OS Places API"
        ),
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_places.by_postcode"},
                "postcode": {"type": "string", "description": "UK postcode"},
            },
            "required": ["postcode"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "uprns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "uprn": {"type": ["string", "null"]},
                            "address": {"type": ["string", "null"]},
                            "lat": {"type": "number"},
                            "lon": {"type": "number"},
                            "classification": {"type": ["string", "null"]},
                            "local_custodian_code": {
                                "type": [
                                    "string",
                                    "number",
                                    "null",
                                ]
                            },
                        },
                        "required": ["uprn", "address", "lat", "lon"],
                        "additionalProperties": True,
                    },
                },
                "provenance": {"type": "object"},
            },
            "required": ["uprns"],
            "additionalProperties": True,
        },
        handler=_by_postcode,
    )
)

# Placeholder registrations for future tools (marked not implemented)
for placeholder in [
    "os_places.search",
    "os_places.by_uprn",
    "os_places.nearest",
    "os_places.within",
    "os_linked_ids.get",
    "os_features.query",
    "os_names.find",
    "os_names.nearest",
    "os_maps.render",
    "os_vector_tiles.descriptor",
]:
    if placeholder == "os_places.by_postcode":  # already registered
        continue
    register(
        Tool(
            name=placeholder,
            description=f"Placeholder for {placeholder}",
        )
    )
