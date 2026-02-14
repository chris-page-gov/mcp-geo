#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image


REQUIRED_TRIALS = {
    "trial-3-geography-selector": "chromium-desktop",
    "trial-4-boundary-explorer": "chromium-desktop",
}

# Sampling and blank-map heuristics tuned from current trial captures:
# - dominant_ratio catches near-solid tiles/panels (blank-like output)
# - unique_colors catches low-detail renders with insufficient scene variation
SAMPLE_GRID_DIVISOR = 120
DOMINANT_COLOR_MAX_RATIO = 0.85
UNIQUE_COLOR_MIN_COUNT = 25


def quantize(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple((channel // 16) * 16 for channel in rgb)


def image_metrics(path: Path) -> dict[str, float]:
    img = Image.open(path).convert("RGB")
    width, height = img.size
    step = max(1, min(width, height) // SAMPLE_GRID_DIVISOR)
    sampled: list[tuple[int, int, int]] = []
    pixels = img.load()
    for y in range(0, height, step):
        for x in range(0, width, step):
            sampled.append(quantize(pixels[x, y]))
    counts = Counter(sampled)
    total = sum(counts.values()) or 1
    dominant = counts.most_common(1)[0][1] / total
    unique = len(counts)
    return {
        "width": float(width),
        "height": float(height),
        "sample_count": float(total),
        "dominant_ratio": float(dominant),
        "unique_colors": float(unique),
    }


def load_observations(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def resolve_path(path_text: str, repo_root: Path) -> Path:
    p = Path(path_text)
    if p.is_absolute():
        return p
    return (repo_root / p).resolve()


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def latest_observations(rows: list[dict]) -> dict[tuple[str, str], dict]:
    latest: dict[tuple[str, str], tuple[datetime | None, int, dict]] = {}
    for index, row in enumerate(rows):
        key = (row.get("trialId", ""), row.get("browser", ""))
        row_ts = parse_timestamp(row.get("timestamp"))
        current = latest.get(key)
        if current is None:
            latest[key] = (row_ts, index, row)
            continue
        current_ts, current_index, _ = current
        if row_ts and current_ts:
            if row_ts >= current_ts:
                latest[key] = (row_ts, index, row)
            continue
        if row_ts and not current_ts:
            latest[key] = (row_ts, index, row)
            continue
        if not row_ts and not current_ts and index >= current_index:
            latest[key] = (row_ts, index, row)
    return {key: item[2] for key, item in latest.items()}


def is_visually_blank(metrics: dict[str, float]) -> bool:
    dominant = metrics.get("dominant_ratio", 1.0)
    unique_colors = metrics.get("unique_colors", 0.0)
    return dominant >= DOMINANT_COLOR_MAX_RATIO or unique_colors < UNIQUE_COLOR_MIN_COUNT


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    obs_path = repo_root / "research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl"
    rows = load_observations(obs_path)
    if not rows:
        print(f"[map-verify] no observations found at {obs_path}", file=sys.stderr)
        return 1

    latest = latest_observations(rows)

    failures: list[str] = []
    for trial_id, browser in REQUIRED_TRIALS.items():
        key = (trial_id, browser)
        row = latest.get(key)
        if not row:
            failures.append(f"missing observation for {trial_id} ({browser})")
            continue
        details = row.get("details", {})
        map_panel = details.get("mapPanel")
        if not map_panel:
            failures.append(f"missing mapPanel screenshot path for {trial_id} ({browser})")
            continue
        panel_path = resolve_path(map_panel, repo_root)
        if not panel_path.exists():
            failures.append(f"mapPanel screenshot not found: {panel_path}")
            continue
        metrics = image_metrics(panel_path)
        dominant = metrics["dominant_ratio"]
        unique_colors = metrics["unique_colors"]
        if is_visually_blank(metrics):
            failures.append(
                f"{trial_id} ({browser}) appears visually blank: dominant={dominant:.3f}, "
                f"unique_colors={int(unique_colors)} ({panel_path})"
            )
        else:
            print(
                f"[map-verify] {trial_id} ({browser}) ok: dominant={dominant:.3f}, "
                f"unique_colors={int(unique_colors)}"
            )

    if failures:
        print("[map-verify] failed:")
        for msg in failures:
            print(f" - {msg}")
        return 1

    print("[map-verify] all required map panels have visible detail.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
