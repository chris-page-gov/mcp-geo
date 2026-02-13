#!/usr/bin/env python3
"""Legacy adapter module now delegating to `server.stdio_adapter`.

Allows console script and direct invocation to remain stable after refactor.
"""
from __future__ import annotations

import sys
from pathlib import Path


_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from server.stdio_adapter import main  # re-export

if __name__ == "__main__":  # pragma: no cover
    main()
