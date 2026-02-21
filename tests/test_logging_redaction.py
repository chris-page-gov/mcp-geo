from __future__ import annotations

from server.config import settings
from server.logging import configure_logging, log_upstream_error


def test_log_upstream_error_masks_configured_and_token_like_values(monkeypatch, capsys):
    monkeypatch.setattr(settings, "LOG_JSON", True, raising=False)
    monkeypatch.setattr(settings, "OS_API_KEY", "os-secret-key", raising=False)
    monkeypatch.setattr(settings, "NOMIS_UID", "uid-secret", raising=False)
    monkeypatch.setattr(settings, "NOMIS_SIGNATURE", "sig-secret", raising=False)

    configure_logging()
    log_upstream_error(
        service="nomis",
        code="NOMIS_API_ERROR",
        url="https://example.test/nomis",
        params={
            "uid": "uid-secret",
            "signature": "sig-secret",
            "Authorization": "Bearer random-token",
            "api_key": "inline-api-key",
            "nested": {
                "token": "nested-token-value",
            },
        },
        detail="upstream failed for os-secret-key uid-secret sig-secret",
    )

    output = capsys.readouterr().out
    assert output
    for raw in (
        "os-secret-key",
        "uid-secret",
        "sig-secret",
        "random-token",
        "inline-api-key",
        "nested-token-value",
    ):
        assert raw not in output
    assert "[REDACTED]" in output
