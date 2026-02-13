from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
PROMPTS_PATH = ROOT / "resources" / "prompts" / "evaluation_prompts.json"


@lru_cache(maxsize=1)
def _load_prompt_file() -> Dict[str, Any]:
    if not PROMPTS_PATH.exists():
        return {"prompts": []}
    try:
        return json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"prompts": []}


def list_prompts() -> List[Dict[str, Any]]:
    data = _load_prompt_file()
    prompts = data.get("prompts", [])
    output: List[Dict[str, Any]] = []
    for prompt in prompts:
        if not isinstance(prompt, dict):
            continue
        name = prompt.get("name")
        if not isinstance(name, str):
            continue
        meta = {
            "intent": prompt.get("intent"),
            "difficulty": prompt.get("difficulty"),
            "requires_os_api": prompt.get("requires_os_api", False),
            "requires_ons_live": prompt.get("requires_ons_live", False),
            "tags": prompt.get("tags", []),
        }
        output.append(
            {
                "name": name,
                "title": prompt.get("title") or name,
                "description": prompt.get("description") or "",
                "_meta": meta,
            }
        )
    return output


def get_prompt(name: str) -> Optional[Dict[str, Any]]:
    data = _load_prompt_file()
    prompts = data.get("prompts", [])
    for prompt in prompts:
        if not isinstance(prompt, dict):
            continue
        if prompt.get("name") != name:
            continue
        question = prompt.get("question") or ""
        meta = {
            "intent": prompt.get("intent"),
            "difficulty": prompt.get("difficulty"),
            "requires_os_api": prompt.get("requires_os_api", False),
            "requires_ons_live": prompt.get("requires_ons_live", False),
            "tags": prompt.get("tags", []),
        }
        return {
            "description": prompt.get("description") or "",
            "messages": [
                {"role": "user", "content": {"type": "text", "text": question}}
            ],
            "_meta": meta,
        }
    return None
