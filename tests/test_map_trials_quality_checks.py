from __future__ import annotations

from pathlib import Path

from PIL import Image

from scripts.map_trials.map_quality_checks import (
    QualityMetrics,
    build_report,
    classify,
    image_quality_metrics,
)


def test_image_quality_metrics_detects_contrast_and_density(tmp_path: Path) -> None:
    image_path = tmp_path / "checker.png"
    img = Image.new("RGB", (80, 80), (255, 255, 255))
    pixels = img.load()
    for y in range(80):
        for x in range(80):
            if (x // 8 + y // 8) % 2 == 0:
                pixels[x, y] = (0, 0, 0)
    img.save(image_path)
    metrics = image_quality_metrics(image_path)
    assert metrics.contrast > 0.7
    assert metrics.label_density > 0.1


def test_classify_pass_warning_fail_and_waiver() -> None:
    status, findings, waiver = classify(
        trial_id="trial-pass",
        metrics=QualityMetrics(contrast=0.5, label_density=0.1),
        accessibility_present=True,
        waivers={},
    )
    assert status == "pass"
    assert findings == []
    assert waiver is None

    status, findings, waiver = classify(
        trial_id="trial-warn",
        metrics=QualityMetrics(contrast=0.25, label_density=0.1),
        accessibility_present=False,
        waivers={},
    )
    assert status == "warning"
    assert findings
    assert waiver is None

    status, findings, waiver = classify(
        trial_id="trial-fail",
        metrics=QualityMetrics(contrast=0.1, label_density=0.5),
        accessibility_present=True,
        waivers={},
    )
    assert status == "fail"
    assert findings
    assert waiver is None

    status, findings, waiver = classify(
        trial_id="trial-waived",
        metrics=QualityMetrics(contrast=0.1, label_density=0.5),
        accessibility_present=True,
        waivers={"trial-waived": "accepted for baseline style"},
    )
    assert status == "warning"
    assert waiver == "accepted for baseline style"
    assert any("waiver applied" in item for item in findings)


def test_build_report_includes_status_counts(tmp_path: Path) -> None:
    panel = tmp_path / "panel.png"
    Image.new("RGB", (64, 64), (255, 255, 255)).save(panel)
    observations = [
        {
            "trialId": "trial-1",
            "browser": "chromium-desktop",
            "timestamp": "2026-02-14T00:00:00Z",
            "details": {"mapPanel": str(panel), "accessibility": {"altText": "Map panel"}},
        }
    ]
    report = build_report(repo_root=tmp_path, observations=observations, waivers={})
    assert "statusCounts" in report
    assert report["checks"]
