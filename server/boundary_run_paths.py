from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from server.config import settings

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOUNDARY_RUNS_DIR = "data/boundary_runs"


def _resolve_path(raw: str | Path) -> Path:
    path = raw if isinstance(raw, Path) else Path(str(raw))
    if not path.is_absolute():
        path = ROOT / path
    return path


def _path_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in str(raw).split(",") if part.strip()]


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[Path] = set()
    ordered: list[Path] = []
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        ordered.append(path)
    return ordered


def boundary_run_dir_candidates(raw: str | Path) -> list[Path]:
    path = _resolve_path(raw)
    candidates = [path]
    if path.name != "boundary_runs":
        candidates.append(path / "boundary_runs")
    return _dedupe_paths(candidates)


def resolve_boundary_run_dir(raw: str | Path | None = None) -> Path:
    configured = raw
    if configured is None:
        configured = getattr(settings, "BOUNDARY_RUNS_DIR", DEFAULT_BOUNDARY_RUNS_DIR)
    return _resolve_path(configured)


def configured_boundary_run_dir() -> Path:
    return resolve_boundary_run_dir()


def configured_boundary_run_search_dirs() -> list[Path]:
    paths: list[Path] = []
    for raw in _path_list(getattr(settings, "BOUNDARY_RUNS_SEARCH_DIRS", "")):
        paths.extend(boundary_run_dir_candidates(raw))
    return _dedupe_paths(paths)


def boundary_run_dirs(
    primary: str | Path | None = None,
    search_dirs: Iterable[str | Path] | None = None,
) -> list[Path]:
    if primary is None:
        paths: list[Path] = [resolve_boundary_run_dir(), *configured_boundary_run_search_dirs()]
    else:
        paths = boundary_run_dir_candidates(primary)
    for raw in search_dirs or []:
        paths.extend(boundary_run_dir_candidates(raw))
    return _dedupe_paths(paths)


def latest_boundary_run_report(
    primary: str | Path | None = None,
    search_dirs: Iterable[str | Path] | None = None,
) -> Path | None:
    best_path: Path | None = None
    best_key: tuple[str, int] | None = None
    for index, root in enumerate(boundary_run_dirs(primary, search_dirs)):
        if not root.exists():
            continue
        for report_path in root.glob("*/run_report.json"):
            key = (report_path.parent.name, -index)
            if best_key is None or key > best_key:
                best_key = key
                best_path = report_path
    return best_path
