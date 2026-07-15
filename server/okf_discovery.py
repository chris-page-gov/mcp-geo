from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from server.mcp.http_route_auth import apply_auth_headers, authorize_http_route

router = APIRouter()

_ROOT = Path(__file__).resolve().parent.parent
_DEMO_ROOT = _ROOT / "resources" / "okf_geo_discovery"
_ASSETS: dict[str, Path] = {
    "data/descriptor.json": _DEMO_ROOT / "descriptor.json",
    "data/manifest.json": _DEMO_ROOT / "manifest.json",
    "data/overview.json": _DEMO_ROOT / "overview.json",
    "data/records.json": _DEMO_ROOT / "records.json",
    "data/spatial-index.json": _DEMO_ROOT / "spatial-index.json",
    "data/mcp-bindings.json": _DEMO_ROOT / "mcp-bindings.json",
}


def _media_type(path: Path) -> str:
    return {
        ".css": "text/css",
        ".html": "text/html",
        ".js": "application/javascript",
        ".json": "application/json",
    }.get(path.suffix.lower(), "application/octet-stream")


def _matches_etag(if_none_match: str | None, etag: str) -> bool:
    if not if_none_match:
        return False
    candidates = {token.strip() for token in if_none_match.split(",") if token.strip()}
    return etag in candidates or "*" in candidates


def _asset_response(
    asset_name: str,
    request: Request,
    response: Response,
    if_none_match: str | None,
) -> Response:
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error

    path = _ASSETS.get(asset_name)
    if path is None or not path.is_file():
        raise HTTPException(status_code=404, detail="OKF discovery asset not found")

    content = path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()[:16]
    etag = f'W/"{digest}"'
    if _matches_etag(if_none_match, etag):
        response.status_code = 304
        response.headers["ETag"] = etag
        apply_auth_headers(response, auth_headers)
        return response

    headers = {"Cache-Control": "public, max-age=300", "ETag": etag}
    headers.update(auth_headers)
    return Response(content=content, media_type=_media_type(path), headers=headers)


@router.get("/okf-discovery", include_in_schema=False)
@router.get("/okf-discovery/", include_in_schema=False)
def okf_discovery_index(
    request: Request,
) -> Response:
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    return RedirectResponse(
        url="/ui/okf-discovery",
        status_code=307,
        headers=auth_headers,
    )


@router.get("/okf-discovery/{asset_name:path}", include_in_schema=False)
def okf_discovery_asset(
    asset_name: str,
    request: Request,
    response: Response,
    if_none_match: str | None = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    return _asset_response(asset_name, request, response, if_none_match)
