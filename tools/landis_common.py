from __future__ import annotations

from typing import Any

from server.landis import (
    PIPE_RISK_CAVEATS,
    PIPE_RISK_CHECKLIST,
    SOILSCAPE_CAVEATS,
    landis_registry_meta,
    resolve_area_input,
)
from tools.registry import ToolResult
from tools.typing_utils import is_strict_int

_DEFAULT_LIMIT = 25
_MAX_LIMIT = 100


def error(message: str, *, code: str = "INVALID_INPUT", status: int = 400) -> ToolResult:
    return status, {"isError": True, "code": code, "message": message}


def parse_limit(value: Any) -> int | None:
    if value is None:
        return _DEFAULT_LIMIT
    if is_strict_int(value) and 1 <= value <= _MAX_LIMIT:
        return value
    return None


def parse_offset(value: Any) -> int | None:
    if value is None:
        return 0
    if is_strict_int(value):
        return value if value >= 0 else None
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return 0
        if raw.isdigit():
            return int(raw)
    return None


def paginate(
    items: list[dict[str, Any]],
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], str | None]:
    page = items[offset: offset + limit]
    next_offset = offset + limit
    next_page = str(next_offset) if next_offset < len(items) else None
    return page, next_page


def product_summary(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": product.get("id"),
        "title": product.get("title"),
        "family": product.get("family"),
        "coverage": product.get("coverage"),
        "spatialType": product.get("spatialType"),
        "resolution": product.get("resolution"),
        "scale": product.get("scale"),
        "accessTier": product.get("accessTier"),
        "resourceUri": product.get("resourceUri"),
        "datasetVersion": product.get("datasetVersion"),
        "updatedAt": product.get("updatedAt"),
        "tags": product.get("tags", []),
    }


def product_metadata(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "abstract": product.get("abstract"),
        "lineage": product.get("lineage"),
        "limitations": product.get("limitations", []),
        "citations": product.get("citations", []),
        "availableResources": product.get("availableResources", []),
        "sourceUrl": product.get("sourceUrl"),
        "license": product.get("license"),
        "lastReviewed": product.get("lastReviewed"),
    }


def pipe_risk_explanation(risk_band: str, scores: dict[str, Any]) -> str:
    worst_corrosion = scores.get("worstCorrosion")
    worst_shrink = scores.get("worstShrinkSwell")
    weighted_corrosion = scores.get("weightedCorrosion")
    weighted_shrink = scores.get("weightedShrinkSwell")
    return (
        f"Pipe risk is screened as {risk_band} because the intersected area includes "
        f"corrosion score {worst_corrosion} and shrink-swell score {worst_shrink}, with "
        f"weighted averages of {weighted_corrosion} and {weighted_shrink} respectively."
    )


def soilscape_response_payload(lat: float, lon: float, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "location": {"lat": lat, "lon": lon},
        "soilscape": row["soilscape"],
        "caveats": SOILSCAPE_CAVEATS,
        "provenance": row["provenance"],
    }


def area_summary_payload(area_input: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "input": area_input,
        "areaSqM": summary["areaSqM"],
        "classes": summary["classes"],
        "dominantClass": summary["dominantClass"],
        "caveats": SOILSCAPE_CAVEATS,
        "provenance": summary["provenance"],
    }


def pipe_risk_payload(area_input: dict[str, Any], summary: dict[str, Any]) -> dict[str, Any]:
    risk_band = str(summary["riskBand"])
    return {
        "input": area_input,
        "riskBand": risk_band,
        "scores": summary["scores"],
        "rawEvidence": {
            "corrosionClasses": summary["corrosionClasses"],
            "shrinkSwellClasses": summary["shrinkSwellClasses"],
        },
        "explanation": pipe_risk_explanation(risk_band, summary["scores"]),
        "caveats": PIPE_RISK_CAVEATS,
        "verificationChecklist": PIPE_RISK_CHECKLIST,
        "provenance": summary["provenance"],
    }


def registry_payload() -> dict[str, Any]:
    return landis_registry_meta()


__all__ = [
    "PIPE_RISK_CAVEATS",
    "PIPE_RISK_CHECKLIST",
    "SOILSCAPE_CAVEATS",
    "area_summary_payload",
    "error",
    "paginate",
    "parse_limit",
    "parse_offset",
    "pipe_risk_payload",
    "product_metadata",
    "product_summary",
    "registry_payload",
    "resolve_area_input",
    "soilscape_response_payload",
]
