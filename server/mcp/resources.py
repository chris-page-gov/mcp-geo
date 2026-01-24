import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Header, Query, Response

from server.mcp.resource_catalog import (
    DATA_RESOURCE_PREFIX,
    list_skill_resources,
    list_ui_resources,
    load_skill_content,
    load_ui_content,
    resolve_skill_resource,
    resolve_ui_resource,
)

router = APIRouter()

def _build_resource_list() -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    resources.extend(list_skill_resources())
    resources.extend(list_ui_resources())
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
            name = uri[len(DATA_RESOURCE_PREFIX):]
            raise HTTPException(status_code=404, detail="Resource not available in live-only mode")
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
        if name.startswith(DATA_RESOURCE_PREFIX):
            raise HTTPException(status_code=404, detail="Resource not available in live-only mode")

    raise HTTPException(status_code=404, detail="Resource not found")
