from server.security import configured_secrets, mask_in_text, mask_in_value, redact


def test_redact_empty():
    assert redact(None) == ""
    assert redact("") == ""

def test_redact_short():
    assert redact("abc") == "[REDACTED]"


def test_redact_long():
    token = redact("supersecretvalue")
    assert token.startswith("sup")
    assert token.endswith("lue"[-3:])
    assert "..." in token


def test_mask_in_text():
    original = "The key ABC123XYZ should be hidden."
    masked = mask_in_text(original, ["ABC123XYZ"])
    assert "[REDACTED]" in masked
    assert "ABC123XYZ" not in masked


def test_mask_in_value_masks_sensitive_keys_and_nested_values():
    value = {
        "safe": "hello",
        "signature": "sig-secret",
        "nested": {
            "authorization": "Bearer token-abc",
            "api_key": "api-secret",
            "list": [{"token": "tok-secret"}],
        },
    }
    masked = mask_in_value(value, ["sig-secret", "token-abc", "api-secret", "tok-secret"])
    assert masked["safe"] == "hello"
    assert masked["signature"] == "[REDACTED]"
    assert masked["nested"]["authorization"] == "[REDACTED]"
    assert masked["nested"]["api_key"] == "[REDACTED]"
    assert masked["nested"]["list"][0]["token"] == "[REDACTED]"


def test_configured_secrets_collects_expected_settings():
    class _Cfg:
        OS_API_KEY = "os-secret"
        NOMIS_UID = "nomis-uid"
        NOMIS_SIGNATURE = "nomis-signature"
        MCP_HTTP_AUTH_TOKEN = "http-auth-token"
        MCP_HTTP_JWT_HS256_SECRET = "jwt-secret"

    assert configured_secrets(_Cfg()) == [
        "os-secret",
        "nomis-uid",
        "nomis-signature",
        "http-auth-token",
        "jwt-secret",
    ]
