from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class DatasetCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(":", "_")
        return self.root / f"{safe}.json"

    def read(self, key: str) -> dict[str, Any] | None:
        path = self._path_for(key)
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except Exception:
            return None

    def write(self, key: str, data: dict[str, Any]) -> None:
        path = self._path_for(key)
        payload = {"cached_at": time.time(), **data}
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)
