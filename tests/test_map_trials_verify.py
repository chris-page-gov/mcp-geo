from pathlib import Path

from PIL import Image

from scripts.map_trials.verify_map_screenshots import (
    image_metrics,
    is_visually_blank,
    latest_observations,
)


def test_image_metrics_returns_expected_fields(tmp_path: Path):
    image_path = tmp_path / "checker.png"
    img = Image.new("RGB", (64, 64), (255, 255, 255))
    pixels = img.load()
    for y in range(64):
        for x in range(64):
            if (x // 8 + y // 8) % 2 == 0:
                pixels[x, y] = (0, 0, 0)
    img.save(image_path)

    metrics = image_metrics(image_path)

    assert metrics["width"] == 64
    assert metrics["height"] == 64
    assert metrics["sample_count"] > 0
    assert 0.0 <= metrics["dominant_ratio"] <= 1.0
    assert metrics["unique_colors"] >= 2


def test_is_visually_blank_detects_solid_panel():
    blank_like = {"dominant_ratio": 0.95, "unique_colors": 3}
    assert is_visually_blank(blank_like) is True


def test_is_visually_blank_accepts_detailed_panel():
    detailed = {"dominant_ratio": 0.45, "unique_colors": 60}
    assert is_visually_blank(detailed) is False


def test_latest_observations_prefers_newest_timestamp_not_row_order():
    rows = [
        {
            "trialId": "trial-3-geography-selector",
            "browser": "chromium-desktop",
            "timestamp": "2026-02-13T23:40:00Z",
            "details": {"mapPanel": "newest.png"},
        },
        {
            "trialId": "trial-3-geography-selector",
            "browser": "chromium-desktop",
            "timestamp": "2026-02-13T23:10:00Z",
            "details": {"mapPanel": "older.png"},
        },
    ]

    latest = latest_observations(rows)
    row = latest[("trial-3-geography-selector", "chromium-desktop")]
    assert row["details"]["mapPanel"] == "newest.png"
