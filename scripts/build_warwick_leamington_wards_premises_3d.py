from __future__ import annotations

import json
import math
import random
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from tools.registry import get as get_tool

# Ensure tool modules are imported and registered.
import server.mcp.tools  # noqa: F401


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = REPO_ROOT / "data" / "exports"
UI_DIR = REPO_ROOT / "ui"

WARWICK_DISTRICT_ID = "E07000222"


@dataclass(frozen=True)
class Ward:
    id: str
    name: str


def _point_in_ring(x: float, y: float, ring: list[list[float]]) -> bool:
    # Ray casting algorithm. Assumes ring coordinates are [lon,lat].
    inside = False
    if len(ring) < 3:
        return False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        intersects = (yi > y) != (yj > y) and (
            x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _point_in_polygon(x: float, y: float, rings: list[list[list[float]]]) -> bool:
    # For our ward use-case, the ArcGIS geometry rings are simple and typically
    # single-ring polygons. Treat the first ring as outer; remaining rings as holes.
    if not rings:
        return False
    if not _point_in_ring(x, y, rings[0]):
        return False
    for hole in rings[1:]:
        if _point_in_ring(x, y, hole):
            return False
    return True


def _reservoir_sample(items: Iterable[dict[str, Any]], k: int, *, seed: int) -> list[dict[str, Any]]:
    rnd = random.Random(seed)
    out: list[dict[str, Any]] = []
    for i, item in enumerate(items, start=1):
        if len(out) < k:
            out.append(item)
            continue
        j = rnd.randint(1, i)
        if j <= k:
            out[j - 1] = item
    return out


def _load_wards() -> list[Ward]:
    find = get_tool("admin_lookup.find_by_name")
    reverse = get_tool("admin_lookup.reverse_hierarchy")
    if not find or not reverse:
        raise RuntimeError("Required admin_lookup tools not registered")

    candidates: dict[str, str] = {}
    for text in ("Warwick", "Leamington"):
        status, payload = find.call({"tool": "admin_lookup.find_by_name", "text": text, "level": "WARD"})
        if status != 200 or not isinstance(payload, dict):
            raise RuntimeError(f"admin_lookup.find_by_name failed for '{text}': {status} {payload}")
        for hit in payload.get("results", []) or []:
            if not isinstance(hit, dict):
                continue
            area_id = str(hit.get("id") or "").strip()
            name = str(hit.get("name") or "").strip()
            if area_id and name:
                candidates[area_id] = name

    wards: list[Ward] = []
    for area_id, name in sorted(candidates.items(), key=lambda kv: kv[1].lower()):
        status, payload = reverse.call({"tool": "admin_lookup.reverse_hierarchy", "id": area_id})
        if status != 200 or not isinstance(payload, dict):
            continue
        chain = payload.get("chain", []) or []
        if not isinstance(chain, list):
            continue
        district_ids = {
            str(item.get("id"))
            for item in chain
            if isinstance(item, dict) and item.get("level") == "DISTRICT"
        }
        if WARWICK_DISTRICT_ID in district_ids:
            wards.append(Ward(id=area_id, name=name))
    return wards


def _fetch_ward_geometry(ward_id: str) -> tuple[list[float], list[list[list[float]]]]:
    area_geom = get_tool("admin_lookup.area_geometry")
    if not area_geom:
        raise RuntimeError("admin_lookup.area_geometry not registered")

    status, payload = area_geom.call(
        {"tool": "admin_lookup.area_geometry", "id": ward_id, "includeGeometry": True}
    )
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"admin_lookup.area_geometry failed for {ward_id}: {status} {payload}")

    bbox = payload.get("bbox")
    geom = payload.get("geometry")
    if not (isinstance(bbox, list) and len(bbox) == 4):
        raise RuntimeError(f"Invalid bbox for {ward_id}: {bbox}")
    if not (isinstance(geom, dict) and isinstance(geom.get("rings"), list)):
        raise RuntimeError(f"Missing geometry rings for {ward_id}")

    rings: list[list[list[float]]] = []
    for ring in geom.get("rings") or []:
        if not isinstance(ring, list):
            continue
        coords: list[list[float]] = []
        for pt in ring:
            if not (isinstance(pt, list) and len(pt) >= 2):
                continue
            try:
                x = float(pt[0])
                y = float(pt[1])
            except Exception:
                continue
            coords.append([x, y])
        if coords:
            rings.append(coords)
    return [float(v) for v in bbox], rings


def _fetch_places_in_bbox(bbox: list[float]) -> list[dict[str, Any]]:
    within = get_tool("os_places.within")
    if not within:
        raise RuntimeError("os_places.within not registered")

    status, payload = within.call({"tool": "os_places.within", "bbox": bbox})
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"os_places.within failed: {status} {payload}")

    results = payload.get("results", []) or []
    if not isinstance(results, list):
        return []
    return [item for item in results if isinstance(item, dict)]


def _build_fc(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def _build_html(*, wards_geojson: dict[str, Any], premises_geojson: dict[str, Any], summary: dict[str, Any]) -> str:
    html_template = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MCP Geo - Warwick + Leamington (Wards + Premises Types, 3D)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap"
      rel="stylesheet"
    />
    <link
      rel="stylesheet"
      href="https://unpkg.com/maplibre-gl@5.7.1/dist/maplibre-gl.css"
    />
    <style>
      :root {
        --bg-1: #f6f7fb;
        --bg-2: #eef3f0;
        --ink: #1d2420;
        --muted: rgba(29, 36, 32, 0.72);
        --panel: rgba(255, 255, 255, 0.92);
        --line: rgba(29, 36, 32, 0.12);
        --shadow: 0 22px 52px rgba(17, 22, 20, 0.18);
        --radius: 18px;
        --font: "Sora", system-ui, -apple-system, Segoe UI, sans-serif;
      }

      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: var(--font);
        color: var(--ink);
        background: radial-gradient(circle at top, #ffffff 0%, var(--bg-1) 42%, var(--bg-2) 100%);
      }

      header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        padding: 20px 22px 10px;
        max-width: 1500px;
        margin: 0 auto;
      }

      .title {
        font-size: 26px;
        font-weight: 650;
        letter-spacing: -0.01em;
      }

      .subtitle {
        font-size: 13px;
        color: var(--muted);
        max-width: 920px;
        line-height: 1.35;
      }

      .shell {
        max-width: 1500px;
        margin: 0 auto;
        padding: 0 22px 22px;
      }

      .grid {
        display: grid;
        grid-template-columns: minmax(300px, 420px) 1fr;
        gap: 16px;
        align-items: start;
      }

      .panel {
        background: var(--panel);
        border-radius: var(--radius);
        padding: 14px;
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
      }

      .panel h3 {
        margin: 0 0 10px;
        font-size: 14px;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        color: rgba(29, 36, 32, 0.78);
      }

      .map {
        background: var(--panel);
        border-radius: var(--radius);
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
        overflow: hidden;
        position: relative;
        min-height: 760px;
      }

      #map { position: absolute; inset: 0; }

      .btns {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 10px;
      }

      button {
        border: 1px solid rgba(29, 36, 32, 0.16);
        background: rgba(255, 255, 255, 0.95);
        padding: 9px 12px;
        border-radius: 12px;
        cursor: pointer;
        font-size: 13px;
        transition: transform 0.08s ease, background 0.15s ease, border-color 0.15s ease;
      }

      button:hover {
        background: rgba(22, 106, 69, 0.07);
        border-color: rgba(22, 106, 69, 0.35);
      }

      button:active { transform: translateY(1px); }

      .kvs {
        font-size: 12px;
        color: rgba(29, 36, 32, 0.75);
        line-height: 1.35;
      }

      .kvs div {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        padding: 6px 0;
        border-bottom: 1px solid rgba(29, 36, 32, 0.08);
      }

      .legend {
        display: grid;
        gap: 6px;
        margin-top: 10px;
        font-size: 12px;
        color: rgba(29, 36, 32, 0.78);
      }

      .swatch {
        width: 12px;
        height: 12px;
        border-radius: 999px;
        display: inline-block;
        margin-right: 8px;
        border: 1px solid rgba(0,0,0,0.12);
      }

      .tip {
        position: absolute;
        pointer-events: none;
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid rgba(29, 36, 32, 0.14);
        border-radius: 12px;
        padding: 10px 12px;
        box-shadow: 0 14px 30px rgba(17, 22, 20, 0.22);
        font-size: 12px;
        color: rgba(29, 36, 32, 0.82);
        display: none;
        max-width: 340px;
      }
    </style>
  </head>
  <body>
    <header>
      <div>
        <div class="title">Warwick + Royal Leamington Spa: wards + premises types (3D)</div>
        <div class="subtitle">
          Wards are extruded by the number of sampled OS Places results inside each ward polygon.
          Points are colored by OS AddressBase classification group (RD/CM/RC/OT).
        </div>
      </div>
      <div class="subtitle" style="text-align:right">
        Data generated by <code>scripts/build_warwick_leamington_wards_premises_3d.py</code><br />
        Wards: __WARD_COUNT__; Premises points: __POINT_COUNT__
      </div>
    </header>
    <div class="shell">
      <div class="grid">
        <div class="panel">
          <h3>Controls</h3>
          <div class="btns">
            <button id="btn3d">Toggle 3D</button>
            <button id="btnFit">Fit Bounds</button>
            <button id="btnPoints">Toggle Points</button>
          </div>
          <h3>Summary</h3>
          <div class="kvs" id="summary"></div>
          <div class="legend">
            <div><span class="swatch" style="background:#1b7a51"></span>RD Residential</div>
            <div><span class="swatch" style="background:#1769aa"></span>CM Commercial</div>
            <div><span class="swatch" style="background:#b85d1f"></span>RC Mixed</div>
            <div><span class="swatch" style="background:#66717a"></span>OT Other</div>
          </div>
          <p class="subtitle" style="margin-top:10px">
            Note: OS Places bbox search applies upstream limits; treat counts as sample-level.
          </p>
        </div>
        <div class="map">
          <div id="map"></div>
          <div class="tip" id="tip"></div>
        </div>
      </div>
    </div>

    <script src="https://unpkg.com/maplibre-gl@5.7.1/dist/maplibre-gl.js"></script>
    <script>
      // Local worker file must be served over HTTP (file:// blocks Workers in most browsers).
      maplibregl.workerUrl = 'vendor/maplibre-gl-csp-worker.js';

      const WARDS = __WARDS__;
      const PREMISES = __PREMISES__;
      const SUMMARY = __SUMMARY__;

      const bounds = SUMMARY.unionBbox;
      const map = new maplibregl.Map({
        container: 'map',
        style: 'https://demotiles.maplibre.org/style.json',
        center: [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2],
        zoom: 12,
        pitch: 60,
        bearing: -18,
        antialias: true
      });
      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

      const tip = document.getElementById('tip');
      const summaryEl = document.getElementById('summary');
      const fmt = new Intl.NumberFormat();

      function addKV(key, value) {
        const row = document.createElement('div');
        const k = document.createElement('span');
        k.textContent = key;
        const v = document.createElement('span');
        v.textContent = value;
        row.appendChild(k);
        row.appendChild(v);
        summaryEl.appendChild(row);
      }

      addKV('Wards', fmt.format(SUMMARY.wards.length));
      addKV('Premises points (sample)', fmt.format(SUMMARY.premisesPoints));
      addKV('Top type', SUMMARY.topPremisesTypes[0] ? SUMMARY.topPremisesTypes[0].type : 'n/a');

      const groupCounts = SUMMARY.premisesByGroup || {};
      for (const k of ['RD','CM','RC','OT']) {
        if (groupCounts[k] != null) {
          addKV(k, fmt.format(groupCounts[k]));
        }
      }

      function groupColor(group) {
        switch ((group || '').toUpperCase()) {
          case 'RD': return '#1b7a51';
          case 'CM': return '#1769aa';
          case 'RC': return '#b85d1f';
          default: return '#66717a';
        }
      }

      function showTip(html, x, y) {
        tip.style.display = 'block';
        tip.style.left = (x + 12) + 'px';
        tip.style.top = (y + 12) + 'px';
        tip.innerHTML = html;
      }
      function hideTip() { tip.style.display = 'none'; }

      map.on('load', () => {
        map.addSource('wards', { type: 'geojson', data: WARDS });
        map.addLayer({
          id: 'ward-extrusion',
          type: 'fill-extrusion',
          source: 'wards',
          paint: {
            'fill-extrusion-color': [
              'case',
              ['has', 'premisesCount'],
              ['interpolate', ['linear'], ['get', 'premisesCount'],
                0, 'rgba(22,106,69,0.20)',
                250, 'rgba(22,106,69,0.34)',
                800, 'rgba(22,106,69,0.50)',
                1400, 'rgba(22,106,69,0.66)'
              ],
              'rgba(22,106,69,0.20)'
            ],
            'fill-extrusion-height': [
              'interpolate', ['linear'], ['sqrt', ['get', 'premisesCount']],
              0, 0,
              10, 600,
              30, 1600,
              50, 2600
            ],
            'fill-extrusion-opacity': 0.88
          }
        });
        map.addLayer({
          id: 'ward-outline',
          type: 'line',
          source: 'wards',
          paint: { 'line-color': 'rgba(29,36,32,0.55)', 'line-width': 1.3 }
        });
        map.addLayer({
          id: 'ward-labels',
          type: 'symbol',
          source: 'wards',
          layout: {
            'text-field': ['get', 'name'],
            'text-font': ['Open Sans Semibold'],
            'text-size': 12,
            'text-allow-overlap': false
          },
          paint: {
            'text-color': 'rgba(29,36,32,0.82)',
            'text-halo-color': 'rgba(255,255,255,0.90)',
            'text-halo-width': 1.2
          }
        });

        map.addSource('premises', { type: 'geojson', data: PREMISES });
        map.addLayer({
          id: 'premises-points',
          type: 'circle',
          source: 'premises',
          minzoom: 10.5,
          paint: {
            'circle-radius': 3.2,
            'circle-color': [
              'match',
              ['get', 'classificationGroup'],
              'RD', '#1b7a51',
              'CM', '#1769aa',
              'RC', '#b85d1f',
              '#66717a'
            ],
            'circle-opacity': 0.76,
            'circle-stroke-width': 0.5,
            'circle-stroke-color': 'rgba(255,255,255,0.65)'
          }
        });

        map.fitBounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]], { padding: 64, duration: 900 });

        map.on('mousemove', (e) => {
          const features = map.queryRenderedFeatures(e.point, { layers: ['premises-points', 'ward-extrusion'] });
          if (!features.length) { hideTip(); map.getCanvas().style.cursor = 'default'; return; }
          const f = features[0];
          const p = f.properties || {};

          if (f.layer.id === 'premises-points') {
            const group = p.classificationGroup || 'OT';
            const code = p.classificationCode || '';
            const desc = p.classificationDescription || code || 'n/a';
            showTip(
              `<div style="font-weight:650;margin-bottom:4px">${desc}</div>` +
              `<div><span style="color:rgba(29,36,32,0.65)">Ward</span>: ${p.wardName || 'n/a'}</div>` +
              `<div><span style="color:rgba(29,36,32,0.65)">Group</span>: <span style="color:${groupColor(group)}">${group}</span></div>`,
              e.originalEvent.clientX,
              e.originalEvent.clientY
            );
            map.getCanvas().style.cursor = 'pointer';
            return;
          }

          if (f.layer.id === 'ward-extrusion') {
            let top = 'n/a';
            try {
              const arr = JSON.parse(p.topPremisesTypesJson || '[]');
              top = (arr && arr.length) ? `${arr[0].type} (${arr[0].count})` : 'n/a';
            } catch (_e) {}
            showTip(
              `<div style="font-weight:650;margin-bottom:4px">${p.name || p.id}</div>` +
              `<div><span style="color:rgba(29,36,32,0.65)">Premises (sample)</span>: ${p.premisesCount || 0}</div>` +
              `<div><span style="color:rgba(29,36,32,0.65)">Top type</span>: ${top}</div>`,
              e.originalEvent.clientX,
              e.originalEvent.clientY
            );
            map.getCanvas().style.cursor = 'default';
            return;
          }
        });

        map.on('mouseleave', 'premises-points', () => hideTip());
      });

      let is3d = true;
      let pointsVisible = true;

      document.getElementById('btn3d').addEventListener('click', () => {
        is3d = !is3d;
        map.easeTo({ pitch: is3d ? 60 : 0, bearing: is3d ? -18 : 0, duration: 700 });
      });
      document.getElementById('btnFit').addEventListener('click', () => {
        map.fitBounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]], { padding: 64, duration: 900 });
      });
      document.getElementById('btnPoints').addEventListener('click', () => {
        pointsVisible = !pointsVisible;
        map.setLayoutProperty('premises-points', 'visibility', pointsVisible ? 'visible' : 'none');
      });
    </script>
  </body>
</html>
"""
    return (
        html_template
        .replace("__WARDS__", json.dumps(wards_geojson, separators=(",", ":")))
        .replace("__PREMISES__", json.dumps(premises_geojson, separators=(",", ":")))
        .replace("__SUMMARY__", json.dumps(summary, separators=(",", ":")))
        .replace("__WARD_COUNT__", str(len(summary.get("wards", []))))
        .replace("__POINT_COUNT__", str(summary.get("premisesPoints", 0)))
    )


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    wards = _load_wards()
    if not wards:
        raise RuntimeError("No Warwick District wards found for 'Warwick'/'Leamington' queries")

    ward_features: list[dict[str, Any]] = []
    premise_features: list[dict[str, Any]] = []

    overall_types: Counter[str] = Counter()
    overall_groups: Counter[str] = Counter()

    # Hard caps to keep the HTML responsive.
    max_points_total = 6000
    max_points_per_ward = 1200

    union_bbox = [math.inf, math.inf, -math.inf, -math.inf]

    for ward in wards:
        bbox, rings = _fetch_ward_geometry(ward.id)
        union_bbox[0] = min(union_bbox[0], bbox[0])
        union_bbox[1] = min(union_bbox[1], bbox[1])
        union_bbox[2] = max(union_bbox[2], bbox[2])
        union_bbox[3] = max(union_bbox[3], bbox[3])

        raw_places = _fetch_places_in_bbox(bbox)
        filtered: list[dict[str, Any]] = []
        for place in raw_places:
            try:
                lon = float(place.get("lon"))
                lat = float(place.get("lat"))
            except Exception:
                continue
            if not _point_in_polygon(lon, lat, rings):
                continue
            filtered.append(place)

        ward_seed = zlib.adler32(ward.id.encode("utf-8")) & 0xFFFFFFFF
        filtered = _reservoir_sample(filtered, max_points_per_ward, seed=ward_seed)

        type_counts: Counter[str] = Counter()
        group_counts: Counter[str] = Counter()

        for place in filtered:
            code = str(place.get("classification") or "").strip()
            desc = str(place.get("classificationDescription") or "").strip()
            if not code:
                continue
            group = code[:2].upper() if len(code) >= 2 else "OT"
            if group not in {"RD", "CM", "RC", "OT"}:
                group = "OT"
            label = desc or code
            type_counts[label] += 1
            group_counts[group] += 1
            overall_types[label] += 1
            overall_groups[group] += 1

            premise_features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "wardId": ward.id,
                    "wardName": ward.name,
                    "uprn": place.get("uprn"),
                    "classificationCode": code,
                    "classificationGroup": group,
                    "classificationDescription": desc or None,
                },
            })

        top_types = [{"type": t, "count": c} for (t, c) in type_counts.most_common(6)]

        ward_features.append({
            "type": "Feature",
            "id": ward.id,
            # Keep geometry simple: single Polygon outer ring (ward boundaries are simple for this query).
            "geometry": {"type": "Polygon", "coordinates": [rings[0]]} if rings else None,
            "properties": {
                "id": ward.id,
                "name": ward.name,
                "bbox": bbox,
                "premisesCount": int(sum(type_counts.values())),
                "topPremisesTypesJson": json.dumps(top_types, separators=(",", ":")),
                "groupCountsJson": json.dumps(dict(group_counts), separators=(",", ":")),
            },
        })

    if len(premise_features) > max_points_total:
        premise_features = _reservoir_sample(premise_features, max_points_total, seed=0xC0DE)

    wards_geojson = _build_fc(ward_features)
    premises_geojson = _build_fc(premise_features)

    summary = {
        "wards": [{"id": w.id, "name": w.name} for w in wards],
        "unionBbox": union_bbox,
        "premisesPoints": len(premise_features),
        "topPremisesTypes": [{"type": t, "count": c} for (t, c) in overall_types.most_common(12)],
        "premisesByGroup": dict(overall_groups),
        "note": (
            "Premises points come from OS Places bbox searches tiled to satisfy upstream limits. "
            "Results are a sample (per-tile result limits apply)."
        ),
    }

    (EXPORT_DIR / "warwick_leamington_wards.geojson").write_text(
        json.dumps(wards_geojson, indent=2), encoding="utf-8"
    )
    (EXPORT_DIR / "warwick_leamington_premises.geojson").write_text(
        json.dumps(premises_geojson, indent=2), encoding="utf-8"
    )
    (EXPORT_DIR / "warwick_leamington_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    html_path = UI_DIR / "warwick_leamington_3d.html"
    html_path.write_text(
        _build_html(wards_geojson=wards_geojson, premises_geojson=premises_geojson, summary=summary),
        encoding="utf-8",
    )

    print(f"Wrote: {html_path}")
    print(f"Wrote: {EXPORT_DIR / 'warwick_leamington_summary.json'}")


if __name__ == "__main__":
    main()

