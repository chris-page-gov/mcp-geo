from __future__ import annotations

from pathlib import Path

from PIL import Image

from scripts.map_trials.map_quality_checks import (
    QualityMetrics,
    build_report,
    classify,
    image_quality_metrics,
    load_quality_policy,
    latest_rows,
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

    status, findings, waiver = classify(
        trial_id="trial-scoped",
        browser="webkit-desktop",
        metrics=QualityMetrics(contrast=0.1, label_density=0.5),
        accessibility_present=True,
        waivers={"trial-scoped|webkit-desktop": "webkit rasterization accepted"},
    )
    assert status == "warning"
    assert waiver == "webkit rasterization accepted"
    assert any("waiver applied" in item for item in findings)

    status, findings, waiver = classify(
        trial_id="trial-threshold-override",
        browser="chromium-desktop",
        metrics=QualityMetrics(contrast=0.18, label_density=0.1),
        accessibility_present=True,
        waivers={},
        thresholds={"contrastFailMin": 0.17, "contrastWarnMin": 0.25},
    )
    assert status == "warning"
    assert waiver is None
    assert any("contrast below warn threshold" in item for item in findings)


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
    assert report["checks"][0]["mapPanel"] == "panel.png"


def test_latest_rows_prefers_newer_timestamp_not_last_index() -> None:
    rows = [
        {
            "trialId": "trial-1",
            "browser": "chromium-desktop",
            "timestamp": "2026-02-17T10:00:00Z",
            "details": {"value": "newest"},
        },
        {
            "trialId": "trial-1",
            "browser": "chromium-desktop",
            "timestamp": "2026-02-17T09:00:00Z",
            "details": {"value": "older"},
        },
    ]
    latest = latest_rows(rows)
    assert latest[("trial-1", "chromium-desktop")]["details"]["value"] == "newest"


def test_load_quality_policy_supports_thresholds_and_browser_scoped_waivers(tmp_path: Path) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text(
        """{
  "policyVersion": "2026-02-21",
  "owner": "@tests",
  "thresholds": {
    "contrastFailMin": 0.18,
    "contrastWarnMin": 0.26,
    "labelDensityWarnMin": 0.24,
    "labelDensityFailMin": 0.38
  },
  "waivers": [
    {"trialId": "story-3", "reason": "accepted"},
    {"trialId": "story-5", "browser": "webkit-desktop", "reason": "webkit accepted"}
  ]
}
""",
        encoding="utf-8",
    )
    waivers, thresholds, meta = load_quality_policy(policy)
    assert waivers["story-3"] == "accepted"
    assert waivers["story-5|webkit-desktop"] == "webkit accepted"
    assert thresholds["contrastFailMin"] == 0.18
    assert thresholds["labelDensityFailMin"] == 0.38
    assert meta["policyVersion"] == "2026-02-21"
    assert meta["owner"] == "@tests"
