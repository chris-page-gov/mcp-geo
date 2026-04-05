from server.config import (
    Settings,
    _coerce_fallback_setting_value,
    _populate_fallback_settings,
    hydrate_env_secret_from_file,
    normalize_env_secret,
)


def test_hydrate_env_secret_from_file_sets_key(tmp_path):
    secret_file = tmp_path / "os_api_key.txt"
    secret_file.write_text("test-key-from-file\n", encoding="utf-8")
    env: dict[str, str] = {"OS_API_KEY_FILE": str(secret_file)}

    hydrate_env_secret_from_file("OS_API_KEY", env)

    assert env["OS_API_KEY"] == "test-key-from-file"


def test_hydrate_env_secret_from_file_preserves_existing_key(tmp_path):
    secret_file = tmp_path / "os_api_key.txt"
    secret_file.write_text("test-key-from-file\n", encoding="utf-8")
    env: dict[str, str] = {
        "OS_API_KEY": "existing-key",
        "OS_API_KEY_FILE": str(secret_file),
    }

    hydrate_env_secret_from_file("OS_API_KEY", env)

    assert env["OS_API_KEY"] == "existing-key"


def test_hydrate_env_secret_from_file_ignores_missing_file(tmp_path):
    env: dict[str, str] = {"OS_API_KEY_FILE": str(tmp_path / "missing.txt")}

    hydrate_env_secret_from_file("OS_API_KEY", env)

    assert "OS_API_KEY" not in env


def test_hydrate_env_secret_from_file_replaces_placeholder_value(tmp_path):
    secret_file = tmp_path / "os_api_key.txt"
    secret_file.write_text("test-key-from-file\n", encoding="utf-8")
    env: dict[str, str] = {
        "OS_API_KEY": "${env:OS_API_KEY}",
        "OS_API_KEY_FILE": str(secret_file),
    }

    hydrate_env_secret_from_file("OS_API_KEY", env)

    assert env["OS_API_KEY"] == "test-key-from-file"


def test_normalize_env_secret_clears_literal_placeholder():
    env: dict[str, str] = {"OS_API_KEY": "${env:OS_API_KEY}"}

    normalize_env_secret("OS_API_KEY", env)

    assert "OS_API_KEY" not in env


def test_settings_reads_env_without_pydantic_settings(monkeypatch):
    monkeypatch.setenv("OS_API_KEY", "env-key")

    settings = Settings()

    assert settings.OS_API_KEY == "env-key"


def test_coerce_fallback_setting_value_handles_basic_typed_env_values():
    assert _coerce_fallback_setting_value("207", int) == 207
    assert _coerce_fallback_setting_value("false", bool) is False
    assert _coerce_fallback_setting_value("true", bool) is True
    assert _coerce_fallback_setting_value("30.5", float) == 30.5


def test_coerce_fallback_setting_value_preserves_default_on_invalid_typed_value():
    assert _coerce_fallback_setting_value("flase", bool, False) is False
    assert _coerce_fallback_setting_value("abc", int, 207) == 207
    assert _coerce_fallback_setting_value("oops", float, 60.0) == 60.0


def test_populate_fallback_settings_coerces_env_backed_defaults():
    class DummySettings:
        RATE_LIMIT_PER_MIN: int = 207
        RATE_LIMIT_BYPASS: bool = False
        ONS_CACHE_TTL: float = 60.0
        LOG_JSON: bool = True
        OS_API_KEY: str = ""

    dummy = DummySettings()
    env = {
        "RATE_LIMIT_PER_MIN": "207",
        "RATE_LIMIT_BYPASS": "false",
        "ONS_CACHE_TTL": "30.5",
        "LOG_JSON": "true",
        "OS_API_KEY": "env-key",
    }

    _populate_fallback_settings(dummy, {}, env)

    assert dummy.RATE_LIMIT_PER_MIN == 207
    assert dummy.RATE_LIMIT_BYPASS is False
    assert dummy.ONS_CACHE_TTL == 30.5
    assert dummy.LOG_JSON is True
    assert dummy.OS_API_KEY == "env-key"


def test_populate_fallback_settings_preserves_defaults_for_invalid_typed_env_values():
    class DummySettings:
        RATE_LIMIT_PER_MIN: int = 207
        RATE_LIMIT_BYPASS: bool = False
        ONS_CACHE_TTL: float = 60.0

    dummy = DummySettings()
    env = {
        "RATE_LIMIT_PER_MIN": "abc",
        "RATE_LIMIT_BYPASS": "flase",
        "ONS_CACHE_TTL": "oops",
    }

    _populate_fallback_settings(dummy, {}, env)

    assert dummy.RATE_LIMIT_PER_MIN == 207
    assert dummy.RATE_LIMIT_BYPASS is False
    assert dummy.ONS_CACHE_TTL == 60.0


def test_populate_fallback_settings_ignores_empty_env_values():
    class DummySettings:
        RATE_LIMIT_PER_MIN: int = 207
        RATE_LIMIT_BYPASS: bool = False
        ONS_DATASET_API_BASE: str = "https://api.beta.ons.gov.uk/v1"

    dummy = DummySettings()
    env = {
        "RATE_LIMIT_PER_MIN": "",
        "RATE_LIMIT_BYPASS": "",
        "ONS_DATASET_API_BASE": "",
    }

    _populate_fallback_settings(dummy, {}, env)

    assert dummy.RATE_LIMIT_PER_MIN == 207
    assert dummy.RATE_LIMIT_BYPASS is False
    assert dummy.ONS_DATASET_API_BASE == "https://api.beta.ons.gov.uk/v1"


def test_populate_fallback_settings_ignores_placeholder_env_values():
    class DummySettings:
        RATE_LIMIT_PER_MIN: int = 207
        RATE_LIMIT_BYPASS: bool = False
        ONS_DATASET_API_BASE: str = "https://api.beta.ons.gov.uk/v1"

    dummy = DummySettings()
    env = {
        "RATE_LIMIT_PER_MIN": "${env:RATE_LIMIT_PER_MIN}",
        "RATE_LIMIT_BYPASS": "${env:RATE_LIMIT_BYPASS}",
        "ONS_DATASET_API_BASE": "${env:ONS_DATASET_API_BASE}",
    }

    _populate_fallback_settings(dummy, {}, env)

    assert dummy.RATE_LIMIT_PER_MIN == 207
    assert dummy.RATE_LIMIT_BYPASS is False
    assert dummy.ONS_DATASET_API_BASE == "https://api.beta.ons.gov.uk/v1"
