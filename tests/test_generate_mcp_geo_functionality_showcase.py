from pathlib import Path

from scripts.generate_mcp_geo_functionality_showcase import (
    PeninsulaCounts,
    WheelchairTownMetrics,
    build_github_blob_url,
    parse_peninsula_counts,
    parse_wheelchair_comparison,
)


def test_build_github_blob_url_strips_git_suffix() -> None:
    url = build_github_blob_url(
        "https://github.com/chris-page-gov/mcp-geo.git",
        "main",
        Path("README.md"),
    )
    assert url == "https://github.com/chris-page-gov/mcp-geo/blob/main/README.md"


def test_parse_peninsula_counts_from_live_note() -> None:
    path = Path("docs/reports/teignmouth_peninsula_building_profile_brief_2026-03-06.md")
    counts = parse_peninsula_counts(path.read_text(encoding="utf-8"))
    assert counts == PeninsulaCounts(
        buildings=743,
        building_parts=915,
        road_links=297,
        path_links=254,
    )


def test_parse_wheelchair_comparison_from_live_note() -> None:
    path = Path("docs/reports/teignmouth_exmouth_sidmouth_access_comparison_2026-03-07.md")
    metrics = parse_wheelchair_comparison(path.read_text(encoding="utf-8"))
    assert metrics == [
        WheelchairTownMetrics(
            name="Teignmouth",
            road_links=422,
            path_links=306,
            pavements=145,
            preferred_km=2.84,
            care_km=4.17,
            barrier_km=1.25,
            anchor_gap_1="Teignmouth station about 26 m",
            anchor_gap_2="Shopmobility about 27 m",
        ),
        WheelchairTownMetrics(
            name="Exmouth",
            road_links=910,
            path_links=532,
            pavements=276,
            preferred_km=5.32,
            care_km=18.90,
            barrier_km=2.60,
            anchor_gap_1="Exmouth railway station about 22 m",
            anchor_gap_2="Exmouth indoor market about 28 m",
        ),
        WheelchairTownMetrics(
            name="Sidmouth",
            road_links=237,
            path_links=140,
            pavements=85,
            preferred_km=1.26,
            care_km=5.68,
            barrier_km=0.44,
            anchor_gap_1="Tourist Information Centre about 5 m",
            anchor_gap_2="Sidmouth Market about 12 m",
        ),
    ]
