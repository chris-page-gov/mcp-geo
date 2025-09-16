from server.security import mask_in_text, redact


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
