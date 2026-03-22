from server.config import Settings, hydrate_env_secret_from_file, normalize_env_secret


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
