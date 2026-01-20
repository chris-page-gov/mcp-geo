from __future__ import annotations

import re
import time
from typing import Any, TypedDict, cast

try:
    import requests
    from requests import exceptions as req_exc
except ImportError:  # pragma: no cover - optional dependency fallback
    requests = None  # type: ignore[assignment]

    class _ReqExc:
        SSLError = Exception
        ConnectionError = Exception
        Timeout = Exception

    req_exc = _ReqExc()

from server.config import settings
from tools.registry import Tool, ToolResult, register
from tools.os_common import client
from pathlib import Path
import json
from tools.types import PlacesResponse

POSTCODE_REGEX = re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$")

# In-memory code list caches (loaded once)
_CLASS_CODES: dict[str, str] = {}
_CUSTODIANS: dict[str, str] = {}

def _load_code_lists() -> None:
    global _CLASS_CODES, _CUSTODIANS
    if _CLASS_CODES and _CUSTODIANS:
        return  # already loaded
    base = Path(__file__).resolve().parent.parent / "resources"
    try:
        cls_path = base / "address_classification_codes.json"
        data = json.loads(cls_path.read_text())
        for entry in data.get("codes", []):
            code = str(entry.get("code"))
            desc = str(entry.get("description")) if entry.get("description") else ""
            if code:
                _CLASS_CODES[code] = desc
    except Exception:  # pragma: no cover - missing file fallback
        _CLASS_CODES = {}
    try:
        cust_path = base / "custodian_codes.json"
        data = json.loads(cust_path.read_text())
        for entry in data.get("codes", []):
            code_val = entry.get("code")
            name = entry.get("name")
            if code_val is not None and name:
                _CUSTODIANS[str(code_val)] = str(name)
    except Exception:  # pragma: no cover
        _CUSTODIANS = {}


class NormalizedUPRN(TypedDict, total=False):
    uprn: str | None
    address: str | None
    lat: float
    lon: float
    classification: str | None
    local_custodian_code: str | int | float | None


def _by_postcode(payload: dict[str, Any]) -> ToolResult:
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

    status, raw = client.get_json(
        f"{client.base_places}/postcode",
        {"postcode": postcode_raw, "output_srs": "WGS84"},
    )
    if status != 200:
        return 501, raw

    body = cast(PlacesResponse, raw)
    results = body.get("results", [])
    _load_code_lists()
    uprns: list[NormalizedUPRN] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        dpa_val = result.get("DPA")
        if not isinstance(dpa_val, dict):
            continue
        dpa = dpa_val
        try:
            lat = float(dpa.get("LAT", 0) or 0)
        except Exception:
            lat = 0.0
        try:
            lon = float(dpa.get("LNG", 0) or 0)
        except Exception:
            lon = 0.0
        lcc = dpa.get("LOCAL_CUSTODIAN_CODE")
        local_custodian_code = cast(str | int | float | None, lcc)
        classification_code = dpa.get("CLASS")
        if classification_code:
            classification_desc = _CLASS_CODES.get(str(classification_code), None)
        else:
            classification_desc = None
        if local_custodian_code is not None:
            cust_name = _CUSTODIANS.get(str(local_custodian_code), None)
        else:
            cust_name = None
        uprns.append({
            "uprn": dpa.get("UPRN"),
            "address": dpa.get("ADDRESS"),
            "lat": lat,
            "lon": lon,
            "classification": classification_code,
            "classificationDescription": classification_desc,
            "local_custodian_code": local_custodian_code,
            "localCustodianName": cust_name,
        })
    return 200, {
        "uprns": uprns,
        "provenance": {
            "source": "os_places",
            "timestamp": raw.get("epoch", time.time()),
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
                            "classificationDescription": {"type": ["string", "null"]},
                            "local_custodian_code": {
                                "type": [
                                    "string",
                                    "number",
                                    "null",
                                ]
                            },
                            "localCustodianName": {"type": ["string", "null"]},
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

## Removed obsolete placeholder loop: real tools registered in their modules.
