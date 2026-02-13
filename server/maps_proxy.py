from __future__ import annotations

import json
import hashlib
import io
import math
import threading
import time
import re
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError

from server.config import settings
from server.circuit_breaker import get_circuit_breaker
from server.security import mask_in_text
from tools.os_common import DEFAULT_TIMEOUT, OSClient, classify_os_api_key_error, req_exc, requests

router = APIRouter()

_OS_BASE = OSClient.base_vector_tiles
_STYLE_INDEX_PATH = "vts/resources/styles"
_DEFAULT_STYLE_NAME = "OS_VTS_3857_Light.json"
_OSM_TILE_BASE = "https://tile.openstreetmap.org"
_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_STYLE_DIR = _REPO_ROOT / "submodules" / "os-vector-tile-api-stylesheets"
_MAPLIBRE_WORKER_PATH = _REPO_ROOT / "ui" / "vendor" / "maplibre-gl-csp-worker.js"
_OSM_CACHE_LOCK = threading.Lock()
_OSM_CACHE: "OrderedDict[str, dict[str, Any]]" = OrderedDict()
_OSM_CACHE_KEY_SEP = "/"
_TILE_SIZE = 256
_MAX_LAT = 85.05112878
_OS_BREAKER = get_circuit_breaker("os")
_OS_KEY_PLACEHOLDER = "OS_API_KEY"
_KEY_QUERY_RE = re.compile(r"([?&]key=)[^&#]+", re.IGNORECASE)


def _osm_tile_base() -> str:
    base = getattr(settings, "OSM_TILE_BASE", "") or _OSM_TILE_BASE
    return base.rstrip("/")


def _osm_cache_ttl() -> float:
    ttl = getattr(settings, "OSM_TILE_CACHE_TTL", 0.0)
    try:
        ttl = float(ttl)
    except (TypeError, ValueError):
        ttl = 0.0
    return max(ttl, 0.0)


def _osm_cache_size() -> int:
    size = getattr(settings, "OSM_TILE_CACHE_SIZE", 0)
    try:
        size = int(size)
    except (TypeError, ValueError):
        size = 0
    return max(size, 0)


def _osm_cache_enabled() -> bool:
    return _osm_cache_ttl() > 0 and _osm_cache_size() > 0


def _osm_cache_key(z: int, x: int, y: int) -> str:
    return f"{z}{_OSM_CACHE_KEY_SEP}{x}{_OSM_CACHE_KEY_SEP}{y}"


def _osm_cache_headers(etag: str | None = None) -> dict[str, str]:
    headers = {"Cache-Control": f"public, max-age={int(_osm_cache_ttl())}"}
    if etag:
        headers["ETag"] = etag
    return headers


def _get_cached_osm_tile(key: str) -> dict[str, Any] | None:
    if not _osm_cache_enabled():
        return None
    now = time.time()
    with _OSM_CACHE_LOCK:
        entry = _OSM_CACHE.get(key)
        if not entry:
            return None
        if now - entry["stored_at"] > _osm_cache_ttl():
            _OSM_CACHE.pop(key, None)
            return None
        _OSM_CACHE.move_to_end(key)
        return entry


def _store_osm_tile(key: str, content: bytes, content_type: str) -> str | None:
    if not _osm_cache_enabled():
        return None
    etag_hash = hashlib.sha256(content).hexdigest()[:16]
    entry = {
        "content": content,
        "content_type": content_type,
        "etag": f'W/"{etag_hash}"',
        "stored_at": time.time(),
    }
    with _OSM_CACHE_LOCK:
        _OSM_CACHE[key] = entry
        _OSM_CACHE.move_to_end(key)
        while len(_OSM_CACHE) > _osm_cache_size():
            _OSM_CACHE.popitem(last=False)
    return entry["etag"]


def _osm_user_agent() -> str:
    user_agent = (getattr(settings, "OSM_TILE_USER_AGENT", "") or "").strip() or "mcp-geo"
    contact = (getattr(settings, "OSM_TILE_CONTACT", "") or "").strip()
    if contact and contact not in user_agent:
        return f"{user_agent} ({contact})"
    return user_agent


def _osm_tile_url(z: int, x: int, y: int) -> str:
    base = _osm_tile_base()
    if "{z}" in base or "{x}" in base or "{y}" in base:
        return base.format(z=z, x=x, y=y)
    return f"{base}/{z}/{x}/{y}.png"


def _clamp_lat(lat: float) -> float:
    return max(-_MAX_LAT, min(_MAX_LAT, lat))


def _lonlat_to_pixel(lon: float, lat: float, zoom: int) -> tuple[float, float]:
    lat = _clamp_lat(lat)
    scale = _TILE_SIZE * (2 ** zoom)
    x = (lon + 180.0) / 360.0 * scale
    lat_rad = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0
    return x, y * scale


def _bbox_to_zoom(bbox: list[float], target_px: int) -> int:
    min_lon, min_lat, max_lon, max_lat = bbox
    for zoom in range(18, -1, -1):
        min_x, max_y = _lonlat_to_pixel(min_lon, min_lat, zoom)
        max_x, min_y = _lonlat_to_pixel(max_lon, max_lat, zoom)
        width = abs(max_x - min_x)
        height = abs(max_y - min_y)
        if width <= target_px and height <= target_px:
            return zoom
    return 0


def _bbox_center(bbox: list[float]) -> tuple[float, float]:
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lon + max_lon) / 2.0, (min_lat + max_lat) / 2.0


def _tile_for_lonlat(lon: float, lat: float, zoom: int) -> tuple[int, int]:
    x, y = _lonlat_to_pixel(lon, lat, zoom)
    return int(x // _TILE_SIZE), int(y // _TILE_SIZE)


def _tile_matrix_size(zoom: int) -> int:
    return 2 ** zoom


def _normalize_tile_x(x: int, zoom: int) -> int:
    n = _tile_matrix_size(zoom)
    return x % n


def _is_valid_tile_y(y: int, zoom: int) -> bool:
    n = _tile_matrix_size(zoom)
    return 0 <= y < n


def _get_osm_tile_bytes(z: int, x: int, y: int) -> tuple[bytes, str, str]:
    x = _normalize_tile_x(x, z)
    if not _is_valid_tile_y(y, z):
        raise HTTPException(status_code=400, detail="OSM tile y out of range")
    cache_key = _osm_cache_key(z, x, y)
    cached = _get_cached_osm_tile(cache_key)
    if cached:
        return (
            cached.get("content", b""),
            cached.get("content_type", "image/png"),
            "HIT",
        )
    url = _osm_tile_url(z, x, y)
    try:
        resp = requests.get(
            url,
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": _osm_user_agent()},
        )
    except (req_exc.ConnectionError, req_exc.Timeout) as exc:
        raise HTTPException(status_code=502, detail=f"OSM proxy error: {exc}") from exc
    content_type = resp.headers.get("content-type", "image/png")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch OSM tile")
    _store_osm_tile(cache_key, resp.content, content_type)
    return resp.content, content_type, "MISS"


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
        # Never embed the real key in returned styles/tiles (local-first hosts should provide OS_API_KEY
        # server-side). Keep a stable placeholder so clients don't accidentally copy/paste a secret.
        url = url.replace("{API_KEY}", _OS_KEY_PLACEHOLDER)
        url = url.replace("OS_API_KEY", _OS_KEY_PLACEHOLDER)
        if key:
            url = url.replace(key, _OS_KEY_PLACEHOLDER)
        url = _KEY_QUERY_RE.sub(rf"\1{_OS_KEY_PLACEHOLDER}", url)
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
                    base = (base_url or "").rstrip("/")
                    tile_base = f"{base}/maps/vector/vts/tile/{{z}}/{{y}}/{{x}}.pbf?srs={srs}"
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
    if not _OS_BREAKER.allow():
        raise HTTPException(status_code=503, detail="OS upstream circuit breaker is open.")
    try:
        return requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    except (req_exc.ConnectionError, req_exc.Timeout) as exc:
        safe = mask_in_text(str(exc), [key])
        _OS_BREAKER.record_failure()
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


def _apply_cors(response: Response, request: Request) -> Response:
    origin = request.headers.get("origin")
    if origin is None:
        return response
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    vary = response.headers.get("Vary")
    if vary:
        if "Origin" not in vary:
            response.headers["Vary"] = f"{vary}, Origin"
    else:
        response.headers["Vary"] = "Origin"
    return response


@router.get("/maps/worker/maplibre-gl-csp-worker.js")
def serve_maplibre_worker(request: Request) -> Response:
    if not _MAPLIBRE_WORKER_PATH.is_file():
        raise HTTPException(status_code=404, detail="MapLibre worker not found")
    response = Response(
        content=_MAPLIBRE_WORKER_PATH.read_bytes(),
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=86400"},
    )
    return _apply_cors(response, request)


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
        if resp.status_code >= 500:
            _OS_BREAKER.record_failure()
        auth_error = classify_os_api_key_error(resp.status_code, resp.text)
        if auth_error:
            code, message = auth_error
            response = JSONResponse(
                status_code=resp.status_code,
                content={"isError": True, "code": code, "message": message},
            )
            return _apply_cors(response, request)
        safe = mask_in_text(resp.text[:200], [key])
        response = JSONResponse(
            status_code=resp.status_code,
            content={
                "isError": True,
                "code": "OS_API_ERROR",
                "message": f"OS API error: {safe}",
            },
        )
        return _apply_cors(response, request)
    _OS_BREAKER.record_success()
    if "application/json" in content_type or "application/vnd.mapbox-style+json" in content_type:
        try:
            payload = resp.json()
        except json.JSONDecodeError:
            response = Response(
                content=resp.content, status_code=resp.status_code, media_type=content_type
            )
            return _apply_cors(response, request)
        rewritten = _rewrite_style_urls(payload, key, srs, str(request.base_url).rstrip("/"))
        response = JSONResponse(content=rewritten)
        return _apply_cors(response, request)
    response = Response(content=resp.content, status_code=resp.status_code, media_type=content_type)
    return _apply_cors(response, request)


@router.get("/maps/raster/osm/{z}/{x}/{y}.png")
def proxy_osm_tiles(z: int, x: int, y: int, request: Request) -> Response:
    if requests is None:
        raise HTTPException(status_code=501, detail="requests is not installed")
    cache_key = _osm_cache_key(z, x, y)
    cached = _get_cached_osm_tile(cache_key)
    if cached:
        if_none_match = request.headers.get("if-none-match")
        if if_none_match and if_none_match == cached.get("etag"):
            response = Response(status_code=304, headers=_osm_cache_headers(cached.get("etag")))
            return _apply_cors(response, request)
        headers = _osm_cache_headers(cached.get("etag"))
        headers["X-Cache"] = "HIT"
        response = Response(
            content=cached.get("content", b""),
            status_code=200,
            media_type=cached.get("content_type", "image/png"),
            headers=headers,
        )
        return _apply_cors(response, request)
    url = _osm_tile_url(z, x, y)
    try:
        resp = requests.get(
            url,
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": _osm_user_agent()},
        )
    except (req_exc.ConnectionError, req_exc.Timeout) as exc:
        raise HTTPException(status_code=502, detail=f"OSM proxy error: {exc}") from exc
    content_type = resp.headers.get("content-type", "image/png")
    if resp.status_code != 200:
        response = Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type=content_type,
        )
        return _apply_cors(response, request)
    etag = _store_osm_tile(cache_key, resp.content, content_type)
    headers = _osm_cache_headers(etag)
    headers["X-Cache"] = "MISS"
    response = Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=content_type,
        headers=headers,
    )
    return _apply_cors(response, request)


@router.get("/maps/static/osm")
def render_static_osm(
    request: Request,
    bbox: str,
    size: int = 256,
    zoom: int | None = None,
) -> Response:
    if requests is None:
        raise HTTPException(status_code=501, detail="requests is not installed")
    try:
        parts = [float(part) for part in bbox.split(",")]
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="bbox must be minLon,minLat,maxLon,maxLat"
        ) from exc
    if len(parts) != 4:
        raise HTTPException(status_code=400, detail="bbox must be minLon,minLat,maxLon,maxLat")
    min_lon, min_lat, max_lon, max_lat = parts
    bbox_vals = [min_lon, min_lat, max_lon, max_lat]
    target_px = max(64, min(int(size), 2048))
    map_zoom = zoom if zoom is not None else _bbox_to_zoom(bbox_vals, target_px)
    center_lon, center_lat = _bbox_center(bbox_vals)
    tile_x, tile_y = _tile_for_lonlat(center_lon, center_lat, map_zoom)
    if target_px <= _TILE_SIZE:
        content, content_type, cache_state = _get_osm_tile_bytes(map_zoom, tile_x, tile_y)
        headers = _osm_cache_headers()
        headers["X-Cache"] = cache_state
        headers["X-Map-Zoom"] = str(map_zoom)
        headers["X-Map-Tile"] = f"{tile_x},{tile_y}"
        response = Response(
            content=content,
            status_code=200,
            media_type=content_type,
            headers=headers,
        )
        return _apply_cors(response, request)

    center_px_x, center_px_y = _lonlat_to_pixel(center_lon, center_lat, map_zoom)
    half = target_px / 2.0
    min_px_x = center_px_x - half
    max_px_x = center_px_x + half
    min_px_y = center_px_y - half
    max_px_y = center_px_y + half
    min_tile_x = math.floor(min_px_x / _TILE_SIZE)
    max_tile_x = math.floor((max_px_x - 1) / _TILE_SIZE)
    min_tile_y = math.floor(min_px_y / _TILE_SIZE)
    max_tile_y = math.floor((max_px_y - 1) / _TILE_SIZE)

    canvas = Image.new("RGBA", (target_px, target_px))
    all_hits = True
    tiles_used = 0
    for ty in range(min_tile_y, max_tile_y + 1):
        if not _is_valid_tile_y(ty, map_zoom):
            continue
        for tx in range(min_tile_x, max_tile_x + 1):
            tile_bytes, _content_type, cache_state = _get_osm_tile_bytes(map_zoom, tx, ty)
            if cache_state != "HIT":
                all_hits = False
            try:
                tile_image = Image.open(io.BytesIO(tile_bytes)).convert("RGBA")
            except (UnidentifiedImageError, OSError) as exc:
                raise HTTPException(status_code=502, detail=f"Invalid OSM tile image: {exc}") from exc
            paste_x = int(round(tx * _TILE_SIZE - min_px_x))
            paste_y = int(round(ty * _TILE_SIZE - min_px_y))
            canvas.alpha_composite(tile_image, (paste_x, paste_y))
            tiles_used += 1

    if tiles_used == 0:
        raise HTTPException(status_code=502, detail="No OSM tiles available for requested map")
    rendered = io.BytesIO()
    canvas.save(rendered, format="PNG")
    rendered_bytes = rendered.getvalue()
    headers = _osm_cache_headers()
    headers["X-Cache"] = "HIT" if all_hits else "MISS"
    headers["X-Map-Zoom"] = str(map_zoom)
    headers["X-Map-Tile"] = f"{tile_x},{tile_y}"
    headers["X-Map-Tiles"] = str(tiles_used)
    response = Response(
        content=rendered_bytes,
        status_code=200,
        media_type="image/png",
        headers=headers,
    )
    return _apply_cors(response, request)
