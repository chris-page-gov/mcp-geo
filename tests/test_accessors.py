from tools.accessors import get_gaz, get_dpa

def test_accessors_missing_and_present():
    empty = {}
    assert get_gaz(empty) == {}
    assert get_dpa(empty) == {}
    data = {"GAZETTEER_ENTRY": {"ID": "123"}, "DPA": {"UPRN": "999"}}
    assert get_gaz(data) == {"ID": "123"}
    assert get_dpa(data) == {"UPRN": "999"}
