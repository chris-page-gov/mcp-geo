from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _assert_ca_refresh_precedes_apt(text: str) -> None:
    first_refresh = text.index("update-ca-certificates")
    first_apt_update = text.index("apt-get update")
    assert first_refresh < first_apt_update


def test_repo_line_endings_policy_is_tracked() -> None:
    gitattributes = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    editorconfig = (REPO_ROOT / ".editorconfig").read_text(encoding="utf-8")

    assert "* text=auto eol=lf" in gitattributes
    assert "*.bat text eol=crlf" in gitattributes
    assert "end_of_line = lf" in editorconfig
    assert "insert_final_newline = true" in editorconfig


def test_devcontainer_supports_proxy_env_and_optional_ngrok() -> None:
    compose_text = (REPO_ROOT / ".devcontainer" / "docker-compose.yml").read_text(
        encoding="utf-8"
    )
    dockerfile_text = (REPO_ROOT / ".devcontainer" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    env_example = (REPO_ROOT / ".devcontainer" / ".env.example").read_text(
        encoding="utf-8"
    )

    assert 'INSTALL_NGROK: "${INSTALL_NGROK:-false}"' in compose_text
    assert 'HTTP_PROXY: "${HTTP_PROXY:-}"' in compose_text
    assert 'HTTPS_PROXY: "${HTTPS_PROXY:-}"' in compose_text
    assert 'NO_PROXY: "${NO_PROXY:-}"' in compose_text
    assert 'HTTP_PROXY="${HTTP_PROXY}"' in dockerfile_text
    assert 'ARG INSTALL_NGROK="false"' in dockerfile_text
    assert "Skipping ngrok install" in dockerfile_text
    assert "HTTP_PROXY=http://proxy.example:8080" in env_example
    assert "INSTALL_NGROK=false" in env_example


def test_container_images_use_system_ca_bundle_and_local_cert_drop_point() -> None:
    devcontainer_dockerfile = (REPO_ROOT / ".devcontainer" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    postgis_dockerfile = (REPO_ROOT / ".devcontainer" / "postgis.Dockerfile").read_text(
        encoding="utf-8"
    )
    repo_dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    cert_ignore = (REPO_ROOT / ".devcontainer" / "certs" / ".gitignore").read_text(
        encoding="utf-8"
    )

    for text in (devcontainer_dockerfile, repo_dockerfile):
        assert "REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt" in text
        assert "COPY .devcontainer/certs/" in text
        assert "HTTP_PROXY=${HTTP_PROXY}" not in text
        _assert_ca_refresh_precedes_apt(text)

    assert "COPY .devcontainer/certs/ /tmp/devcontainer-certs/" in devcontainer_dockerfile
    assert "COPY .devcontainer/certs/ /tmp/devcontainer-certs/" in postgis_dockerfile
    assert "SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt" in devcontainer_dockerfile
    assert "ca-certificates" in postgis_dockerfile
    _assert_ca_refresh_precedes_apt(postgis_dockerfile)
    assert cert_ignore.strip() == "*\n!.gitignore"
