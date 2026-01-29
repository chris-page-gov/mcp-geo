import json


def _write_prompts(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def _load_prompts_module(monkeypatch, path):
    from server.mcp import prompts

    monkeypatch.setattr(prompts, "PROMPTS_PATH", path)
    prompts._load_prompt_file.cache_clear()
    return prompts


def test_list_prompts_filters_and_meta(monkeypatch, tmp_path):
    path = tmp_path / "prompts.json"
    _write_prompts(
        path,
        {
            "prompts": [
                {
                    "name": "alpha",
                    "title": "Alpha Prompt",
                    "description": "Example",
                    "intent": "lookup",
                    "difficulty": "easy",
                    "requires_os_api": True,
                    "requires_ons_live": False,
                    "tags": ["demo"],
                },
                "bad",
                {"title": "Missing name"},
                {"name": 123, "description": "Wrong type"},
            ]
        },
    )
    prompts = _load_prompts_module(monkeypatch, path)
    results = prompts.list_prompts()
    assert len(results) == 1
    entry = results[0]
    assert entry["name"] == "alpha"
    assert entry["title"] == "Alpha Prompt"
    assert entry["description"] == "Example"
    meta = entry["_meta"]
    assert meta["intent"] == "lookup"
    assert meta["difficulty"] == "easy"
    assert meta["requires_os_api"] is True
    assert meta["requires_ons_live"] is False
    assert meta["tags"] == ["demo"]


def test_get_prompt_returns_messages(monkeypatch, tmp_path):
    path = tmp_path / "prompts.json"
    _write_prompts(
        path,
        {
            "prompts": [
                "bad",
                {
                    "name": "alpha",
                    "question": "What is this?",
                    "description": "Prompt description",
                    "intent": "lookup",
                    "difficulty": "medium",
                }
            ]
        },
    )
    prompts = _load_prompts_module(monkeypatch, path)
    result = prompts.get_prompt("alpha")
    assert result is not None
    assert result["description"] == "Prompt description"
    assert result["_meta"]["intent"] == "lookup"
    assert result["_meta"]["difficulty"] == "medium"
    assert result["_meta"]["requires_os_api"] is False
    assert result["_meta"]["requires_ons_live"] is False
    assert result["_meta"]["tags"] == []
    assert result["messages"] == [
        {"role": "user", "content": {"type": "text", "text": "What is this?"}}
    ]


def test_get_prompt_missing_returns_none(monkeypatch, tmp_path):
    path = tmp_path / "prompts.json"
    _write_prompts(path, {"prompts": [{"name": "alpha", "question": "Q"}]})
    prompts = _load_prompts_module(monkeypatch, path)
    assert prompts.get_prompt("missing") is None


def test_list_prompts_missing_file(monkeypatch, tmp_path):
    path = tmp_path / "missing.json"
    prompts = _load_prompts_module(monkeypatch, path)
    assert prompts.list_prompts() == []


def test_list_prompts_invalid_json(monkeypatch, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{", encoding="utf-8")
    prompts = _load_prompts_module(monkeypatch, path)
    assert prompts.list_prompts() == []
