#!/usr/bin/env python3
"""Legacy adapter module now delegating to `server.stdio_adapter`.

Allows console script and direct invocation to remain stable after refactor.
"""
from __future__ import annotations

import importlib.util
import os
import site
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

def _ensure_user_site_when_missing(module_name: str) -> None:
    if importlib.util.find_spec(module_name) is not None:
        return
    os.environ.pop("PYTHONNOUSERSITE", None)
    user_site = site.getusersitepackages()
    if not user_site:
        return
    try:
        sys.path.remove(user_site)
    except ValueError:
        pass
    sys.path.append(user_site)


_ensure_user_site_when_missing("loguru")

# Ensure repo root stays ahead of user site-packages.
if str(_repo_root) in sys.path:
    sys.path.remove(str(_repo_root))
    sys.path.insert(0, str(_repo_root))


def main() -> None:
    from server.stdio_adapter import main as _main

    _main()

if __name__ == "__main__":  # pragma: no cover
    main()
