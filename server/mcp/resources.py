import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header, Query, Request, Response
from fastapi.responses import FileResponse, RedirectResponse

from server.mcp.http_route_auth import apply_auth_headers, authorize_http_route
from server.mcp.resource_access import read_resource_content, read_result_payload
from server.mcp.resource_catalog import (
    list_data_resources,
    list_skill_resources,
    list_ui_resources,
    load_ui_content,
    resolve_offline_pack_download,
    resolve_ui_resource,
    UI_DIR,
)

router = APIRouter()

_UI_SHARED_DIR = (UI_DIR / "shared").resolve()
_UI_VENDOR_DIR = (UI_DIR / "vendor").resolve()
_UI_SHARED_COMPACT_CONTRACT_CSS = _UI_SHARED_DIR / "compact_contract.css"
_UI_SHARED_COMPACT_CONTRACT_JS = _UI_SHARED_DIR / "compact_contract.js"
_UI_VENDOR_MAPLIBRE_CSS = _UI_VENDOR_DIR / "maplibre-gl.css"
_UI_VENDOR_MAPLIBRE_JS = _UI_VENDOR_DIR / "maplibre-gl.js"
_UI_VENDOR_MAPLIBRE_WORKER_JS = _UI_VENDOR_DIR / "maplibre-gl-csp-worker.js"
_UI_VENDOR_SHP_JS = _UI_VENDOR_DIR / "shp.min.js"
_UI_STATIC_ASSETS: dict[str, Path] = {
    "shared/compact_contract.css": _UI_SHARED_COMPACT_CONTRACT_CSS,
    "shared/compact_contract.js": _UI_SHARED_COMPACT_CONTRACT_JS,
    "vendor/maplibre-gl.css": _UI_VENDOR_MAPLIBRE_CSS,
    "vendor/maplibre-gl.js": _UI_VENDOR_MAPLIBRE_JS,
    "vendor/maplibre-gl-csp-worker.js": _UI_VENDOR_MAPLIBRE_WORKER_JS,
    "vendor/shp.min.js": _UI_VENDOR_SHP_JS,
}

def _etag_match(if_none_match: Optional[str], etag: str) -> bool:
    if not if_none_match:
        return False
    candidates = {token.strip() for token in if_none_match.split(",") if token.strip()}
    return etag in candidates or "*" in candidates


def _raise_http_route_error(
    status_code: int,
    detail: str,
    auth_headers: dict[str, str],
) -> None:
    raise HTTPException(status_code=status_code, detail=detail, headers=auth_headers)


def _ui_asset_media_type(path: Path) -> str:
    if path.suffix == ".js":
        return "application/javascript"
    if path.suffix == ".css":
        return "text/css"
    if path.suffix == ".json":
        return "application/json"
    return "application/octet-stream"


def _static_asset_response(
    asset_name: str, response: Response, if_none_match: Optional[str]
) -> Response:
    asset_path = _UI_STATIC_ASSETS.get(asset_name)
    if asset_path is None:
        raise HTTPException(status_code=404, detail="UI asset not found")
    if not asset_path.exists() or not asset_path.is_file():
        raise HTTPException(status_code=404, detail="UI asset not found")

    stat = asset_path.stat()
    etag = f'W/"{stat.st_mtime_ns:x}-{stat.st_size:x}"'
    if _etag_match(if_none_match, etag):
        response.status_code = 304
        response.headers["ETag"] = etag
        return response

    return Response(
        content=asset_path.read_bytes(),
        media_type=_ui_asset_media_type(asset_path),
        headers={"ETag": etag, "Cache-Control": "public, max-age=300"},
    )


def _binary_file_response(path: Path, media_type: str, headers: dict[str, str]) -> FileResponse:
    return FileResponse(
        path=path,
        media_type=media_type,
        headers=dict(headers),
        filename=path.name,
    )


def _build_resource_list() -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    resources.extend(list_skill_resources())
    resources.extend(list_ui_resources())
    resources.extend(list_data_resources())
    return resources


def _read_result(
    uri: str,
    mime_type: str | None,
    text: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {"uri": uri, "mimeType": mime_type, "text": text, "_meta": meta}
    return read_result_payload(payload)


def _read_json_result(uri: str, payload: dict[str, Any]) -> dict[str, Any]:
    return _read_result(
        uri,
        "application/json",
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
    )


@router.get("/resources/list")
def list_resources(request: Request, response: Response, limit: int = 10, page: int = 1) -> Any:
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    resources = _build_resource_list()
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(resources) else None
    return {"resources": resources[start:end], "nextPageToken": next_page_token}


@router.get("/resources/describe")
def describe_resources(request: Request, response: Response, limit: int = 10, page: int = 1) -> Any:
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    resources = _build_resource_list()
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(resources) else None
    return {"resources": resources[start:end], "nextPageToken": next_page_token}


@router.get("/resources/read")
def read_resource(
    request: Request,
    response: Response,
    name: str | None = Query(default=None),
    uri: str | None = Query(default=None),
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
    limit: int = Query(default=100, ge=1, le=500),
    page: int = Query(default=1, ge=1),
    level: Optional[str] = Query(default=None),
    nameContains: Optional[str] = Query(default=None),
    geography: Optional[str] = Query(default=None),
    measure: Optional[str] = Query(default=None),
) -> Optional[Dict[str, Any]]:
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    apply_auth_headers(response, auth_headers)
    if not name and not uri:
        _raise_http_route_error(400, "Missing resource name or uri", auth_headers)

    def _match_etag(etag: str) -> bool:
        if not if_none_match:
            return False
        candidates = {token.strip() for token in if_none_match.split(",") if token.strip()}
        return etag in candidates or "*" in candidates

    try:
        resource = read_resource_content(name=name, uri=uri, asset_mode="absolute")
    except ValueError as exc:
        _raise_http_route_error(400, str(exc), auth_headers)
    except LookupError:
        _raise_http_route_error(404, "Resource not found", auth_headers)

    etag = str(resource["etag"])
    if _match_etag(etag):
        response.status_code = 304
        response.headers["ETag"] = etag
        return None
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "public, max-age=300"
    return read_result_payload(resource)


@router.get("/ui/{slug}")
def render_ui_resource(
    slug: str,
    response: Response,
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    uri = f"ui://mcp-geo/{slug}"
    ui_entry = resolve_ui_resource(uri)
    if not ui_entry:
        raise HTTPException(status_code=404, detail="UI resource not found")
    content, etag = load_ui_content(ui_entry, asset_mode="absolute")
    if if_none_match:
        candidates = {token.strip() for token in if_none_match.split(",") if token.strip()}
        if etag in candidates or "*" in candidates:
            response.status_code = 304
            response.headers["ETag"] = etag
            return response
    cache_control = (
        "no-store, max-age=0" if slug == "simple-map-lab" else "public, max-age=300"
    )
    return Response(
        content=content,
        media_type="text/html",
        headers={"ETag": etag, "Cache-Control": cache_control},
    )


@router.get("/ui/shared/compact_contract.css")
def render_ui_shared_compact_contract_css(
    response: Response,
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    return _static_asset_response(
        "shared/compact_contract.css", response, if_none_match
    )


@router.get("/ui/shared/compact_contract.js")
def render_ui_shared_compact_contract_js(
    response: Response,
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    return _static_asset_response(
        "shared/compact_contract.js", response, if_none_match
    )


@router.get("/ui/vendor/maplibre-gl.css")
def render_ui_vendor_maplibre_css(
    response: Response,
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    return _static_asset_response("vendor/maplibre-gl.css", response, if_none_match)


@router.get("/ui/vendor/maplibre-gl.js")
def render_ui_vendor_maplibre_js(
    response: Response,
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    return _static_asset_response("vendor/maplibre-gl.js", response, if_none_match)


@router.get("/ui/vendor/maplibre-gl-csp-worker.js")
def render_ui_vendor_maplibre_worker_js(
    response: Response,
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    return _static_asset_response(
        "vendor/maplibre-gl-csp-worker.js", response, if_none_match
    )


@router.get("/ui/vendor/shp.min.js")
def render_ui_vendor_shp_js(
    response: Response,
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    return _static_asset_response("vendor/shp.min.js", response, if_none_match)


@router.get("/simple-map-lab", include_in_schema=False)
def simple_map_lab_redirect() -> RedirectResponse:
    return RedirectResponse(url="/ui/simple-map-lab", status_code=307)


@router.get("/resources/download")
def download_resource(
    request: Request,
    uri: str = Query(...),
) -> Any:
    auth_headers, auth_error = authorize_http_route(request)
    if auth_error is not None:
        return auth_error
    resolved = resolve_offline_pack_download(uri)
    if not resolved:
        raise HTTPException(status_code=404, detail="Offline pack not found")
    path, media_type = resolved
    return _binary_file_response(path, media_type, auth_headers)
