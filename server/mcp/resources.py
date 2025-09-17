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


@router.get("/resources/list")
def list_resources(limit: int = 10, page: int = 1) -> Dict[str, Any]:
    resources = [
        {
            "name": "code_lists",
        },
        {
            "name": "admin_boundaries",
            "version": _ADMIN_PROVENANCE["version"],
            "license": _ADMIN_PROVENANCE["license"],
            "source": _ADMIN_PROVENANCE["source"],
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
            "provenance": _ADMIN_PROVENANCE,
            "data": {
                "features": page_items,
                "total": len(filtered),
                "limit": limit,
                "page": page,
                "nextPageToken": next_page_token,
            },
        }
        response.headers["ETag"] = etag
        return payload
    raise HTTPException(status_code=404, detail="Resource not found")
