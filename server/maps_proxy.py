from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from server.config import settings
from server.security import mask_in_text
from tools.os_common import DEFAULT_TIMEOUT, OSClient, classify_os_api_key_error, req_exc, requests

router = APIRouter()

_OS_BASE = OSClient.base_vector_tiles
_STYLE_INDEX_PATH = "vts/resources/styles"
_DEFAULT_STYLE_NAME = "OS_VTS_3857_Light.json"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_STYLE_DIR = _REPO_ROOT / "submodules" / "os-vector-tile-api-stylesheets"


def _get_api_key(request: Request) -> str:
    key = request.query_params.get("key")
    if key in ("OS_API_KEY", "{API_KEY}"):
        key = None
    key = key or settings.OS_API_KEY
    if not key:
        raise HTTPException(
            status_code=401,
            detail="OS API key required. Provide OS_API_KEY or ?key=",
        )
    return key


def _rewrite_style_urls(
    style: dict[str, Any],
    key: str,
    srs: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    sprite_override = style.get("_sprite")
    if isinstance(sprite_override, str):
        style["sprite"] = sprite_override

    def rewrite(url: str) -> str:
        if _OS_BASE in url:
            url = url.replace(_OS_BASE, "/maps/vector")
        url = url.replace("{API_KEY}", key)
        url = url.replace("OS_API_KEY", key)
        if "/maps/vector" in url and "key=" not in url:
            joiner = "&" if "?" in url else "?"
            url = f"{url}{joiner}key={key}"
        if srs and "/maps/vector/vts" in url and "srs=" not in url:
            joiner = "&" if "?" in url else "?"
            url = f"{url}{joiner}srs={srs}"
        if base_url and not urlparse(url).scheme:
            if url.startswith("/"):
                url = f"{base_url}{url}"
            else:
                url = f"{base_url}/{url}"
        return url

    if isinstance(style.get("sprite"), str):
        style["sprite"] = rewrite(style["sprite"])
    if isinstance(style.get("glyphs"), str):
        style["glyphs"] = rewrite(style["glyphs"])
    tiles = style.get("tiles")
    if isinstance(tiles, list):
        style["tiles"] = [rewrite(tile) if isinstance(tile, str) else tile for tile in tiles]
    if isinstance(style.get("url"), str):
        style["url"] = rewrite(style["url"])
    sources = style.get("sources")
    if isinstance(sources, dict):
        for source in sources.values():
            if isinstance(source, dict):
                tiles = source.get("tiles")
                if isinstance(tiles, list):
                    source["tiles"] = [
                        rewrite(tile) if isinstance(tile, str) else tile for tile in tiles
                    ]
                if isinstance(source.get("url"), str):
                    source["url"] = rewrite(source["url"])
                url = source.get("url")
                if (
                    isinstance(url, str)
                    and "/maps/vector/vts" in url
                    and source.get("type") == "vector"
                    and srs
                ):
                    tile_base = f"{base_url}/maps/vector/vts/tile/{{z}}/{{y}}/{{x}}.pbf?key={key}&srs={srs}"
                    source["tiles"] = [tile_base]
                    source["tileSize"] = source.get("tileSize") or 512
                    source.pop("url", None)
    return style


def _normalize_style_name(style_name: str | None) -> str:
    name = (style_name or "").strip()
    if not name:
        return _DEFAULT_STYLE_NAME
    name = Path(name).name
    if not name.endswith(".json"):
        name = f"{name}.json"
    return name


def _infer_srs(style_name: str | None) -> str | None:
    if not style_name:
        return None
    lowered = style_name.lower()
    if "27700" in lowered:
        return "27700"
    if "3857" in lowered:
        return "3857"
    return None


def _load_local_style(style_name: str | None) -> dict[str, Any] | None:
    if not _LOCAL_STYLE_DIR.exists():
        return None
    name = _normalize_style_name(style_name)
    path = _LOCAL_STYLE_DIR / name
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid style JSON: {name}") from exc


def _is_style_doc(payload: Any) -> bool:
    return isinstance(payload, dict) and "version" in payload and "sources" in payload


def _extract_style_url(payload: Any, style_name: str | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    styles = payload.get("styles")
    if not isinstance(styles, list):
        return None
    lowered = style_name.lower() if isinstance(style_name, str) else None

    def _url_from_style(style: dict[str, Any]) -> str | None:
        for key in ("url", "href", "uri"):
            value = style.get(key)
            if isinstance(value, str):
                return value
        links = style.get("links")
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict):
                    href = link.get("href")
                    if isinstance(href, str):
                        return href
        return None

    if lowered:
        for style in styles:
            if not isinstance(style, dict):
                continue
            for key in ("id", "name", "title"):
                value = style.get(key)
                if isinstance(value, str) and value.lower() == lowered:
                    return _url_from_style(style)
    for style in styles:
        if not isinstance(style, dict):
            continue
        for key in ("default", "isDefault", "is_default"):
            if style.get(key) is True:
                return _url_from_style(style)
    for style in styles:
        if isinstance(style, dict):
            return _url_from_style(style)
    return None


def _normalize_style_url(url: str, key: str) -> tuple[str, bool]:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = urljoin(f"{_OS_BASE}/", url)
        parsed = urlparse(url)
    if "{API_KEY}" in url:
        url = url.replace("{API_KEY}", key)
        parsed = urlparse(url)
    has_key = "key=" in (parsed.query or "")
    return url, has_key


def _get_upstream(url: str, params: dict[str, Any], key: str) -> requests.Response:
    try:
        return requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    except (req_exc.ConnectionError, req_exc.Timeout) as exc:
        safe = mask_in_text(str(exc), [key])
        raise HTTPException(status_code=502, detail=f"OS proxy error: {safe}") from exc


def _get_upstream_style(style_name: str | None, params: dict[str, Any], key: str) -> requests.Response:
    candidates: list[tuple[str, dict[str, Any]]] = []
    variants: list[str] = []
    if style_name:
        variants.append(style_name)
        normalized = style_name.removesuffix(".json")
        if normalized != style_name:
            variants.append(normalized)

    for variant in variants:
        style_file = variant if variant.endswith(".json") else f"{variant}.json"
        candidates.extend(
            [
                (f"{_OS_BASE}/{_STYLE_INDEX_PATH}/{style_file}", {}),
                (f"{_OS_BASE}/{_STYLE_INDEX_PATH}", {"style": variant}),
            ]
        )
    candidates.append((f"{_OS_BASE}/{_STYLE_INDEX_PATH}", {}))

    last_resp: requests.Response | None = None
    for url, extra in candidates:
        merged = {**params, **extra}
        resp = _get_upstream(url, merged, key)
        if resp.status_code == 200:
            try:
                payload = resp.json()
            except json.JSONDecodeError:
                return resp
            if _is_style_doc(payload):
                return resp
            style_url = _extract_style_url(payload, style_name)
            if style_url:
                resolved, has_key = _normalize_style_url(style_url, key)
                if has_key:
                    return _get_upstream(resolved, {}, key)
                return _get_upstream(resolved, params, key)
            return resp
        if resp.status_code != 404:
            return resp
        last_resp = resp
    return last_resp if last_resp is not None else resp


@router.get("/maps/vector/{path:path}")
def proxy_vector_tiles(path: str, request: Request) -> Response:
    if requests is None:
        raise HTTPException(status_code=501, detail="requests is not installed")
    key = _get_api_key(request)
    params = dict(request.query_params)
    params.pop("key", None)
    params["key"] = key
    srs = request.query_params.get("srs")
    try:
        if path.startswith("styles/"):
            style_name = path.split("/", 1)[1]
            local_style = _load_local_style(style_name)
            if local_style:
                return JSONResponse(
                    content=_rewrite_style_urls(
                        local_style,
                        key,
                        _infer_srs(style_name) or srs,
                        str(request.base_url).rstrip("/"),
                    )
                )
            resp = _get_upstream_style(style_name, params, key)
        elif path == "styles" or path == "styles.json":
            style_name = request.query_params.get("style")
            local_style = _load_local_style(style_name)
            if local_style:
                return JSONResponse(
                    content=_rewrite_style_urls(
                        local_style,
                        key,
                        _infer_srs(style_name) or srs,
                        str(request.base_url).rstrip("/"),
                    )
                )
            resp = _get_upstream_style(style_name, params, key)
        else:
            upstream_url = f"{_OS_BASE}/{path}"
            resp = _get_upstream(upstream_url, params, key)
    except (req_exc.ConnectionError, req_exc.Timeout) as exc:
        safe = mask_in_text(str(exc), [key])
        raise HTTPException(status_code=502, detail=f"OS proxy error: {safe}") from exc
    content_type = resp.headers.get("content-type", "application/octet-stream")
    if resp.status_code != 200:
        auth_error = classify_os_api_key_error(resp.status_code, resp.text)
        if auth_error:
            code, message = auth_error
            return JSONResponse(
                status_code=resp.status_code,
                content={"isError": True, "code": code, "message": message},
            )
        safe = mask_in_text(resp.text[:200], [key])
        return JSONResponse(
            status_code=resp.status_code,
            content={
                "isError": True,
                "code": "OS_API_ERROR",
                "message": f"OS API error: {safe}",
            },
        )
    if "application/json" in content_type or "application/vnd.mapbox-style+json" in content_type:
        try:
            payload = resp.json()
        except json.JSONDecodeError:
            return Response(
                content=resp.content, status_code=resp.status_code, media_type=content_type
            )
        rewritten = _rewrite_style_urls(payload, key, srs, str(request.base_url).rstrip("/"))
        return JSONResponse(content=rewritten)
    return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)
