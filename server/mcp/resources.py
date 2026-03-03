import json
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header, Query, Response
from fastapi.responses import FileResponse, RedirectResponse

from server.mcp.resource_catalog import (
    DATA_RESOURCE_PREFIX,
    list_data_resources,
    list_skill_resources,
    list_ui_resources,
    load_data_content,
    load_skill_content,
    load_ui_content,
    resolve_data_resource,
    resolve_offline_pack_download,
    resolve_skill_resource,
    resolve_ui_resource,
    UI_DIR,
)

router = APIRouter()

_UI_SHARED_DIR = (UI_DIR / "shared").resolve()


def _etag_match(if_none_match: Optional[str], etag: str) -> bool:
    if not if_none_match:
        return False
    candidates = {token.strip() for token in if_none_match.split(",") if token.strip()}
    return etag in candidates or "*" in candidates


def _shared_asset_media_type(path: Path) -> str:
    if path.suffix == ".js":
        return "application/javascript"
    if path.suffix == ".css":
        return "text/css"
    return "application/octet-stream"

def _build_resource_list() -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    resources.extend(list_skill_resources())
    resources.extend(list_ui_resources())
    resources.extend(list_data_resources())
    return resources


def _read_result(
    uri: str,
    mime_type: Optional[str],
    text: str,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    item: Dict[str, Any] = {"uri": uri, "text": text}
    if mime_type:
        item["mimeType"] = mime_type
    if meta:
        item["_meta"] = meta
    return {"contents": [item]}


def _read_json_result(uri: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return _read_result(
        uri,
        "application/json",
        json.dumps(payload, ensure_ascii=True, separators=(",", ":")),
    )


@router.get("/resources/list")
def list_resources(limit: int = 10, page: int = 1) -> Dict[str, Any]:
    resources = _build_resource_list()
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(resources) else None
    return {"resources": resources[start:end], "nextPageToken": next_page_token}


@router.get("/resources/describe")
def describe_resources(limit: int = 10, page: int = 1) -> Dict[str, Any]:
    resources = _build_resource_list()
    start = (page - 1) * limit
    end = start + limit
    next_page_token = str(page + 1) if end < len(resources) else None
    return {"resources": resources[start:end], "nextPageToken": next_page_token}


@router.get("/resources/read")
def read_resource(
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
    if not name and not uri:
        raise HTTPException(status_code=400, detail="Missing resource name or uri")

    def _match_etag(etag: str) -> bool:
        if not if_none_match:
            return False
        candidates = {token.strip() for token in if_none_match.split(",") if token.strip()}
        return etag in candidates or "*" in candidates

    if uri:
        if uri.startswith(DATA_RESOURCE_PREFIX):
            entry = resolve_data_resource(uri)
            if entry:
                content, etag, meta = load_data_content(entry)
                if _match_etag(etag):
                    response.status_code = 304
                    response.headers["ETag"] = etag
                    return None
                response.headers["ETag"] = etag
                response.headers["Cache-Control"] = "public, max-age=300"
                return _read_result(uri, "application/json", content, meta)
            raise HTTPException(status_code=404, detail="Resource not found")
        else:
            ui_entry = resolve_ui_resource(uri)
            if ui_entry:
                content, etag = load_ui_content(ui_entry)
                if _match_etag(etag):
                    response.status_code = 304
                    response.headers["ETag"] = etag
                    return None
                response.headers["ETag"] = etag
                response.headers["Cache-Control"] = "public, max-age=300"
                return _read_result(
                    ui_entry["uri"],
                    ui_entry["mimeType"],
                    content,
                    ui_entry.get("resourceMeta"),
                )
            skill_entry = resolve_skill_resource(uri)
            if skill_entry:
                content, etag = load_skill_content()
                if _match_etag(etag):
                    response.status_code = 304
                    response.headers["ETag"] = etag
                    return None
                response.headers["ETag"] = etag
                response.headers["Cache-Control"] = "public, max-age=300"
                return _read_result(skill_entry["uri"], skill_entry["mimeType"], content)
            raise HTTPException(status_code=404, detail="Resource not found")

    if name:
        ui_entry = resolve_ui_resource(name)
        if ui_entry:
            content, etag = load_ui_content(ui_entry)
            if _match_etag(etag):
                response.status_code = 304
                response.headers["ETag"] = etag
                return None
            response.headers["ETag"] = etag
            response.headers["Cache-Control"] = "public, max-age=300"
            return _read_result(
                ui_entry["uri"],
                ui_entry["mimeType"],
                content,
                ui_entry.get("resourceMeta"),
            )
        skill_entry = resolve_skill_resource(name)
        if skill_entry:
            content, etag = load_skill_content()
            if _match_etag(etag):
                response.status_code = 304
                response.headers["ETag"] = etag
                return None
            response.headers["ETag"] = etag
            response.headers["Cache-Control"] = "public, max-age=300"
            return _read_result(skill_entry["uri"], skill_entry["mimeType"], content)
        if name.startswith(DATA_RESOURCE_PREFIX) or resolve_data_resource(name):
            entry = resolve_data_resource(name)
            if entry:
                content, etag, meta = load_data_content(entry)
                if _match_etag(etag):
                    response.status_code = 304
                    response.headers["ETag"] = etag
                    return None
                response.headers["ETag"] = etag
                response.headers["Cache-Control"] = "public, max-age=300"
                uri_value = name if name.startswith(DATA_RESOURCE_PREFIX) else f"{DATA_RESOURCE_PREFIX}{entry.get('slug','')}"
                return _read_result(uri_value, "application/json", content, meta)

    raise HTTPException(status_code=404, detail="Resource not found")


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
    content, etag = load_ui_content(ui_entry)
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


@router.get("/ui/shared/{asset_name}")
def render_ui_shared_asset(
    asset_name: str,
    response: Response,
    if_none_match: Optional[str] = Header(
        default=None, alias="If-None-Match", convert_underscores=False
    ),
) -> Response:
    # Serve compact contract assets for hosted UI widgets and iframe/srcdoc fallbacks.
    asset_path = (_UI_SHARED_DIR / asset_name).resolve()
    if asset_path.parent != _UI_SHARED_DIR or not asset_path.exists() or not asset_path.is_file():
        raise HTTPException(status_code=404, detail="UI shared asset not found")

    stat = asset_path.stat()
    etag = f'W/"{stat.st_mtime_ns:x}-{stat.st_size:x}"'
    if _etag_match(if_none_match, etag):
        response.status_code = 304
        response.headers["ETag"] = etag
        return response

    return FileResponse(
        path=str(asset_path),
        media_type=_shared_asset_media_type(asset_path),
        headers={"ETag": etag, "Cache-Control": "public, max-age=300"},
    )


@router.get("/simple-map-lab", include_in_schema=False)
def simple_map_lab_redirect() -> RedirectResponse:
    return RedirectResponse(url="/ui/simple-map-lab", status_code=307)


@router.get("/resources/download")
def download_resource(
    uri: str = Query(...),
) -> FileResponse:
    resolved = resolve_offline_pack_download(uri)
    if not resolved:
        raise HTTPException(status_code=404, detail="Offline pack not found")
    path, media_type = resolved
    return FileResponse(path=str(path), filename=path.name, media_type=media_type)
