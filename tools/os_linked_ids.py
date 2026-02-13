from __future__ import annotations

import re
from typing import Any

from tools.os_common import client
from tools.registry import Tool, ToolResult, register

_TOID_PREFIX_RE = re.compile(r"^osgb", re.IGNORECASE)
_NUMERIC_RE = re.compile(r"^[0-9]+$")


def _normalize_identifier_type(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    text = value.strip().lower()
    if not text:
        return None
    if text in {"uprn", "usrn", "toid"}:
        return text
    if text in {"toid_id", "osgb"}:
        return "toid"
    return None


def _infer_identifier_type(identifier: str) -> str | None:
    if _TOID_PREFIX_RE.match(identifier):
        return "toid"
    if _NUMERIC_RE.match(identifier):
        # Ambiguous (UPRN/USRN), but UPRN is the more common default for MCP queries.
        return "uprn"
    return None


def _linked_ids_get(payload: dict[str, Any]) -> ToolResult:
    """Resolve linked identifiers (UPRN/USRN/TOID) via OS Linked Identifiers API."""
    identifier = str(payload.get("identifier", "")).strip()
    if not identifier:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing identifier"}

    identifier_type = _normalize_identifier_type(
        payload.get("identifierType") or payload.get("type")
    )
    assumed_type = False
    if identifier_type is None:
        inferred = _infer_identifier_type(identifier)
        if inferred is None:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "identifierType must be one of: uprn, usrn, toid",
            }
        identifier_type = inferred
        assumed_type = True

    url = f"{client.base_linked_ids}/identifierTypes/{identifier_type}/{identifier}"
    status, body = client.get_json(url, None)
    if status != 200:
        return 501, body
    if not isinstance(body, dict):
        return 500, {
            "isError": True,
            "code": "INTEGRATION_ERROR",
            "message": "Expected JSON object response from OS linked identifiers API",
        }

    identifiers = body.get("identifiers")
    if identifiers is None:
        identifiers = body

    return 200, {
        "identifier": identifier,
        "identifierType": identifier_type,
        "assumedType": assumed_type,
        "identifiers": identifiers,
        "live": True,
        "hints": [
            "Set identifierType explicitly (uprn/usrn/toid) if inference is wrong.",
        ],
    }


def _linked_ids_identifiers(payload: dict[str, Any]) -> ToolResult:
    identifier = str(payload.get("identifier", "")).strip()
    if not identifier:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing identifier"}
    status, body = client.get_json(f"{client.base_linked_ids}/identifiers/{identifier}", None)
    if status != 200:
        return status, body
    return 200, {"identifier": identifier, "identifiers": body, "live": True}


def _linked_ids_feature_types(payload: dict[str, Any]) -> ToolResult:
    feature_type = str(payload.get("featureType", "")).strip()
    identifier = str(payload.get("identifier", "")).strip()
    if not feature_type:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing featureType"}
    if not identifier:
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "Missing identifier"}
    status, body = client.get_json(
        f"{client.base_linked_ids}/featureTypes/{feature_type}/{identifier}",
        None,
    )
    if status != 200:
        return status, body
    return 200, {
        "featureType": feature_type,
        "identifier": identifier,
        "identifiers": body,
        "live": True,
    }


def _linked_ids_product_version_info(payload: dict[str, Any]) -> ToolResult:
    correlation_method = str(payload.get("correlationMethod", "")).strip()
    if not correlation_method:
        return 400, {
            "isError": True,
            "code": "INVALID_INPUT",
            "message": "Missing correlationMethod",
        }
    status, body = client.get_json(
        f"{client.base_linked_ids}/productVersionInfo/{correlation_method}",
        None,
    )
    if status != 200:
        return status, body
    return 200, {
        "correlationMethod": correlation_method,
        "productVersionInfo": body,
        "live": True,
    }


register(
    Tool(
        name="os_linked_ids.get",
        description="Resolve linked identifiers (UPRN/USRN/TOID) using OS search/links API.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_linked_ids.get"},
                "identifier": {"type": "string"},
                "identifierType": {
                    "type": "string",
                    "description": "One of: uprn, usrn, toid (optional, inferred if omitted).",
                },
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "identifier": {"type": "string"},
                "identifierType": {"type": "string"},
                "assumedType": {"type": "boolean"},
                "identifiers": {"type": ["array", "object"]},
            },
            "required": ["identifiers"],
            "additionalProperties": True,
        },
        handler=_linked_ids_get,
    )
)

register(
    Tool(
        name="os_linked_ids.identifiers",
        description="Resolve linked identifiers using /identifiers/{id}.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_linked_ids.identifiers"},
                "identifier": {"type": "string"},
            },
            "required": ["identifier"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "identifier": {"type": "string"},
                "identifiers": {"type": ["array", "object"]},
                "live": {"type": "boolean"},
            },
            "required": ["identifier", "identifiers"],
            "additionalProperties": True,
        },
        handler=_linked_ids_identifiers,
    )
)

register(
    Tool(
        name="os_linked_ids.feature_types",
        description="Resolve linked identifiers using /featureTypes/{featureType}/{id}.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_linked_ids.feature_types"},
                "featureType": {"type": "string"},
                "identifier": {"type": "string"},
            },
            "required": ["featureType", "identifier"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "featureType": {"type": "string"},
                "identifier": {"type": "string"},
                "identifiers": {"type": ["array", "object"]},
                "live": {"type": "boolean"},
            },
            "required": ["featureType", "identifier", "identifiers"],
            "additionalProperties": True,
        },
        handler=_linked_ids_feature_types,
    )
)

register(
    Tool(
        name="os_linked_ids.product_version_info",
        description="Resolve product version info for a correlation method.",
        input_schema={
            "type": "object",
            "properties": {
                "tool": {"type": "string", "const": "os_linked_ids.product_version_info"},
                "correlationMethod": {"type": "string"},
            },
            "required": ["correlationMethod"],
            "additionalProperties": False,
        },
        output_schema={
            "type": "object",
            "properties": {
                "correlationMethod": {"type": "string"},
                "productVersionInfo": {"type": ["array", "object"]},
                "live": {"type": "boolean"},
            },
            "required": ["correlationMethod", "productVersionInfo"],
            "additionalProperties": True,
        },
        handler=_linked_ids_product_version_info,
    )
)
