#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HostCapabilityProfile:
    profile_id: str
    ui_supported: bool
    degradation_mode: str
    description: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_fixture_path() -> Path:
    return _repo_root() / "playground" / "trials" / "fixtures" / "host_capability_profiles.json"


def load_profiles(path: Path) -> list[HostCapabilityProfile]:
    if not path.exists():
        raise FileNotFoundError(f"Fixture file not found: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    rows = obj.get("profiles")
    if not isinstance(rows, list):
        raise ValueError("Fixture must contain a 'profiles' array")
    profiles: list[HostCapabilityProfile] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        profile_id = raw.get("id")
        if not isinstance(profile_id, str) or not profile_id.strip():
            continue
        profiles.append(
            HostCapabilityProfile(
                profile_id=profile_id.strip(),
                ui_supported=bool(raw.get("uiSupported", False)),
                degradation_mode=str(raw.get("degradationMode") or "unknown"),
                description=str(raw.get("description") or "").strip(),
            )
        )
    if not profiles:
        raise ValueError("Fixture does not contain any valid profiles")
    return sorted(profiles, key=lambda row: row.profile_id)


def build_replay_matrix(
    profiles: list[HostCapabilityProfile],
    *,
    engines: list[str] | None = None,
) -> list[dict[str, Any]]:
    matrix_engines = engines or ["chromium-desktop", "firefox-desktop", "webkit-desktop"]
    rows: list[dict[str, Any]] = []
    for engine in matrix_engines:
        for profile in profiles:
            rows.append(
                {
                    "engine": engine,
                    "profileId": profile.profile_id,
                    "uiSupported": profile.ui_supported,
                    "degradationMode": profile.degradation_mode,
                }
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit deterministic map host-simulation replay matrix."
    )
    parser.add_argument(
        "--fixture",
        default=str(_default_fixture_path()),
        help="Path to host capability fixture JSON.",
    )
    parser.add_argument(
        "--engines",
        default="chromium-desktop,firefox-desktop,webkit-desktop",
        help="Comma-separated engine identifiers.",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional output path for JSON matrix.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = Path(args.fixture).resolve()
    profiles = load_profiles(fixture)
    engines = [item.strip() for item in str(args.engines).split(",") if item.strip()]
    matrix = build_replay_matrix(profiles, engines=engines)
    payload = {"fixture": str(fixture), "count": len(matrix), "matrix": matrix}
    text = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    out = str(args.out).strip()
    if out:
        out_path = Path(out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(out_path)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
