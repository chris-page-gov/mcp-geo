from fastapi import APIRouter, HTTPException, Header, Response, Query
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from typing_extensions import TypedDict
class AdminBoundariesPayload(TypedDict):
    name: str
    count: int
    etag: str
    provenance: Dict[str, str]
    data: Dict[str, Any]

router = APIRouter()

_ADMIN_PROVENANCE = {
    "name": "admin_boundaries",
    "version": "2025.09.17-alpha",
    "source": "ONS / Ordnance Survey open data (sample subset)",
    "license": "Open Government Licence v3",
    "retrievedAt": datetime.now(timezone.utc).isoformat(),
}


def _admin_boundaries_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "resources" / "admin_boundaries.json"


def _admin_etag(variant_key: str = "") -> str:
    path = _admin_boundaries_path()
    try:
        raw = path.read_bytes()
    except FileNotFoundError:  # pragma: no cover
        return "missing"
    base = raw + _ADMIN_PROVENANCE["version"].encode() + variant_key.encode()
    h = hashlib.sha256(base).hexdigest()[:16]
    return f"W/\"{h}\""  # weak ETag


def _ons_observations_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "resources" / "ons_observations.json"


def _ons_etag(variant_key: str = "") -> str:
    path = _ons_observations_path()
    try:
        raw = path.read_bytes()
    except FileNotFoundError:  # pragma: no cover
        return "missing"
    # Basic provenance read to incorporate version if present
    try:
        parsed = json.loads(raw.decode())
        version = parsed.get("provenance", {}).get("version", "v0")
    except Exception:  # pragma: no cover
        version = "v0"
    base = raw + version.encode() + variant_key.encode()
    h = hashlib.sha256(base).hexdigest()[:16]
    return f"W/\"{h}\""


@router.get("/resources/list")
def list_resources(limit: int = 10, page: int = 1) -> Dict[str, Any]:
    resources: list[dict[str, Any]] = [
        {
            "name": "admin_boundaries",
            "type": "boundary_hierarchy",
            "version": _ADMIN_PROVENANCE["version"],
            "license": _ADMIN_PROVENANCE["license"],
            "source": _ADMIN_PROVENANCE["source"],
            "description": "Sample administrative boundary chain",
        },
        {
            "name": "ons_observations",
            "type": "dataset",
            "version": None,
            "license": "Open Government Licence v3",
            "source": "ONS (sample synthetic subset)",
            "description": "Sample ONS quarterly GDP observations (synthetic)",
        },
        {
            "name": "address_classification_codes",
            "type": "code_list",
            "version": "2025.11.03-alpha",
            "license": "Open Government Licence v3",
            "source": "OS AddressBase (sample subset)",
            "description": "Address classification code descriptions",
        },
        {
            "name": "custodian_codes",
            "type": "code_list",
            "version": "2025.11.03-alpha",
            "license": "Open Government Licence v3",
            "source": "Local Authority Codes (sample)",
            "description": "Local custodian code to name mapping",
        },
        {
            "name": "boundaries_wards",
            "type": "boundary",
            "version": "2025.11.03-alpha",
            "license": "Open Government Licence v3",
            "source": "Sample Ward Boundaries (synthetic subset)",
            "description": "Ward-level bounding boxes (sample subset)",
        },
    ]
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(resources) else None
    return {"resources": resources[start:end], "nextPageToken": next_page_token}


@router.get("/resources/get")
def get_resource(
    name: str,
    response: Response,
    if_none_match: Optional[str] = Header(default=None, alias="If-None-Match", convert_underscores=False),
    limit: int = Query(default=100, ge=1, le=500),
    page: int = Query(default=1, ge=1),
    level: Optional[str] = Query(default=None),
    nameContains: Optional[str] = Query(default=None),
    geography: Optional[str] = Query(default=None),
    measure: Optional[str] = Query(default=None),
) -> Optional[AdminBoundariesPayload]:
    if name == "admin_boundaries":
        path = _admin_boundaries_path()
        if not path.exists():  # pragma: no cover - defensive
            raise HTTPException(status_code=404, detail="Resource not found")
        # Load raw data for filtering
        data = json.loads(path.read_text())
        features = data.get("features", [])
        # Apply filters
        filtered: list[dict[str, Any]] = []
        lvl = level.upper() if level else None
        needle = nameContains.lower() if nameContains else None
        for f in features:
            if lvl and f.get("level") != lvl:
                continue
            if needle and needle not in str(f.get("name", "")).lower():
                continue
            filtered.append(f)
        # Pagination
        start = (page - 1) * limit
        end = start + limit
        page_items: list[dict[str, Any]] = filtered[start:end]
        next_page_token = str(page + 1) if end < len(filtered) else None
        variant_key = f"v1|{lvl or '*'}|{needle or '*'}|{page}|{limit}"
        etag = _admin_etag(variant_key)
        if if_none_match:
            # Support multiple ETags in header (comma-separated) per RFC 7232
            candidates = {token.strip() for token in if_none_match.split(',') if token.strip()}
            if etag in candidates or "*" in candidates:
                response.status_code = 304
                response.headers["ETag"] = etag
                return None
        payload: AdminBoundariesPayload = {
            "name": name,
            "count": len(filtered),
            "etag": etag,
            "provenance": {**_ADMIN_PROVENANCE, "retrievedAt": datetime.now(timezone.utc).isoformat()},
            "data": {
                "features": page_items,
                "total": len(filtered),
                "limit": limit,
                "page": page,
                "nextPageToken": next_page_token,
            },
        }
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=300"
        return payload
    if name == "ons_observations":
        path = _ons_observations_path()
        if not path.exists():  # pragma: no cover
            raise HTTPException(status_code=404, detail="Resource not found")
        parsed = json.loads(path.read_text())
        observations = parsed.get("observations", [])
        geography_param = geography
        measure_param = measure
        if geography_param or measure_param:
            filtered_obs: list[dict[str, Any]] = []
            for o in observations:
                if geography_param and o.get("geography") != geography_param:
                    continue
                if measure_param and o.get("measure") != measure_param:
                    continue
                filtered_obs.append(o)
            observations = filtered_obs
        start = (page - 1) * limit
        end = start + limit
        page_items: list[dict[str, Any]] = observations[start:end]
        next_page_token = str(page + 1) if end < len(observations) else None
        variant_key = f"obs|{geography_param or '*'}|{measure_param or '*'}|{page}|{limit}"
        etag = _ons_etag(variant_key)
        if if_none_match:
            candidates = {token.strip() for token in if_none_match.split(',') if token.strip()}
            if etag in candidates or "*" in candidates:
                response.status_code = 304
                response.headers["ETag"] = etag
                return None
        provenance = parsed.get("provenance", {})
        payload = {
            "name": name,
            "count": len(observations),
            "etag": etag,
            "provenance": {**provenance, "retrievedAt": datetime.now(timezone.utc).isoformat()},
            "data": {
                "observations": page_items,
                "total": len(observations),
                "limit": limit,
                "page": page,
                "nextPageToken": next_page_token,
                "dimensions": parsed.get("dimensions", {}),
                "appliedFilters": {
                    "geography": geography_param,
                    "measure": measure_param,
                },
            },
        }
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=300"
        return payload  # type: ignore[return-value]

    # Code lists & ward boundaries (simple pagination + ETag varianting)
    def _generic_resource(path: Path, variant_key: str) -> Optional[Dict[str, Any]]:
        if not path.exists():
            raise HTTPException(status_code=404, detail="Resource not found")
        parsed = json.loads(path.read_text())
        items = parsed.get("codes") or parsed.get("features") or []
        start = (page - 1) * limit
        end = start + limit
        page_items = items[start:end]
        next_page_token = str(page + 1) if end < len(items) else None
        provenance = parsed.get("provenance", {})
        etag = _ons_etag(f"{name}|{variant_key}|{page}|{limit}")
        if if_none_match:
            candidates = {token.strip() for token in if_none_match.split(',') if token.strip()}
            if etag in candidates or "*" in candidates:
                response.status_code = 304
                response.headers["ETag"] = etag
                return None
        payload = {
            "name": name,
            "count": len(items),
            "etag": etag,
            "provenance": {**provenance, "retrievedAt": datetime.now(timezone.utc).isoformat()},
            "data": {
                "items": page_items,
                "total": len(items),
                "limit": limit,
                "page": page,
                "nextPageToken": next_page_token,
            },
        }
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "public, max-age=86400"
        return payload

    base_path = Path(__file__).resolve().parent.parent.parent / "resources"
    if name in {"address_classification_codes", "custodian_codes", "boundaries_wards"}:
        return _generic_resource(base_path / f"{name}.json", "base")

    raise HTTPException(status_code=404, detail="Resource not found")
