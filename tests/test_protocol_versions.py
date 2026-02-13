from server.protocol import (
    HTTP_DEFAULT_PROTOCOL_VERSION,
    PROTOCOL_VERSION,
    SUPPORTED_PROTOCOL_VERSIONS,
    is_supported_protocol_version,
    negotiate_protocol_version,
    normalize_protocol_version,
)


def test_protocol_defaults_and_ordering():
    assert SUPPORTED_PROTOCOL_VERSIONS[0] == PROTOCOL_VERSION
    assert HTTP_DEFAULT_PROTOCOL_VERSION in SUPPORTED_PROTOCOL_VERSIONS


def test_negotiate_protocol_version_supported_passthrough():
    assert negotiate_protocol_version("2025-11-25") == "2025-11-25"
    assert negotiate_protocol_version("2025-03-26") == "2025-03-26"


def test_negotiate_protocol_version_falls_back_for_unsupported_or_invalid():
    assert negotiate_protocol_version("1999-01-01") == PROTOCOL_VERSION
    assert negotiate_protocol_version(None) == PROTOCOL_VERSION
    assert negotiate_protocol_version(123) == PROTOCOL_VERSION


def test_protocol_version_helpers():
    assert normalize_protocol_version(" 2025-11-25 ") == "2025-11-25"
    assert normalize_protocol_version("") is None
    assert normalize_protocol_version(None) is None
    assert is_supported_protocol_version("2025-11-25") is True
    assert is_supported_protocol_version("2099-01-01") is False
