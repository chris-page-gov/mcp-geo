from server.error_taxonomy import classify_error


def test_classify_error_known():
    assert classify_error("INVALID_INPUT") == "input"
    assert classify_error("OS_API_ERROR") == "upstream"


def test_classify_error_unknown():
    assert classify_error("NOT_A_CODE") == "unknown"
    assert classify_error(None) == "unknown"
