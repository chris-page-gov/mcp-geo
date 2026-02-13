from tools.typing_utils import parse_float

def test_parse_float_various_inputs():
    assert parse_float(None) == 0.0
    assert parse_float(5) == 5.0
    assert parse_float(3.14) == 3.14
    assert parse_float(" 7.5 ") == 7.5
    assert parse_float("") == 0.0
    assert parse_float("not-a-number") == 0.0
