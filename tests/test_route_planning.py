from server import route_planning


def test_normalize_route_profile_aliases():
    assert route_planning.normalize_route_profile("car") == "drive"
    assert route_planning.normalize_route_profile("WALKING") == "walk"
    assert route_planning.normalize_route_profile("bike") == "cycle"
    assert route_planning.normalize_route_profile("multi modal") == "multimodal"
    assert route_planning.normalize_route_profile(None) == "drive"


def test_normalize_coordinates_supports_multiple_shapes():
    assert route_planning.normalize_coordinates([-1.5, 52.4]) == [-1.5, 52.4]
    assert route_planning.normalize_coordinates({"lat": 52.4, "lon": -1.5}) == [-1.5, 52.4]
    assert route_planning.normalize_coordinates("52.4,-1.5") == [-1.5, 52.4]
    assert route_planning.normalize_coordinates("not-a-coordinate") is None


def test_normalize_stop_variants():
    assert route_planning.normalize_stop("100023336959") == {"query": "100023336959"}
    assert route_planning.normalize_stop({"uprn": "100023336959"}) == {"uprn": "100023336959"}
    assert route_planning.normalize_stop({"coordinates": {"lat": 52.4, "lon": -1.5}}) == {
        "coordinates": [-1.5, 52.4]
    }
    assert route_planning.normalize_stop({"query": "Coventry"}) == {"query": "Coventry"}
    assert route_planning.normalize_stop({"bad": True}) is None


def test_stop_from_text_prefers_coordinates_and_uprn():
    assert route_planning.stop_from_text("52.4081,-1.5106") == {
        "coordinates": [-1.5106, 52.4081]
    }
    assert route_planning.stop_from_text("UPRN 100023336959") == {"uprn": "100023336959"}
    assert route_planning.stop_from_text("Retford Library, DN22 6PE") == {
        "query": "Retford Library, DN22 6PE"
    }


def test_looks_like_route_query_requires_structure():
    assert route_planning.looks_like_route_query("Show emergency route from A to B") is True
    assert route_planning.looks_like_route_query("origin: A destination: B") is False
    assert route_planning.looks_like_route_query("Find Westminster") is False


def test_extract_route_request_parses_sg03_shape():
    request = route_planning.extract_route_request(
        "What is the best emergency route from Retford Library, 17 Churchgate, Retford, DN22 6PE "
        "to Goodwin Hall, Chancery Lane, Retford, DN22 6DF and avoid flood-risk-zone reference "
        "167647/3 if possible?"
    )
    assert request is not None
    assert request["profile"] == "emergency"
    assert request["stops"][0]["query"].startswith("Retford Library")
    assert request["stops"][1]["query"] == "Goodwin Hall, Chancery Lane, Retford, DN22 6DF"
    assert request["constraints"]["avoidIds"] == ["167647/3"]
    assert request["constraints"]["softAvoid"] is True


def test_extract_route_request_parses_labeled_origin_destination():
    request = route_planning.extract_route_request(
        """
        origin: Coventry rail station
        destination: London Euston
        route mode: multimodal
        optional constraints: avoid central cordon if possible
        """
    )
    assert request is not None
    assert request["stops"] == [{"query": "Coventry rail station"}, {"query": "London Euston"}]
    assert request["profile"] == "multimodal"
    assert request["constraints"]["avoidAreas"] == ["central cordon"]


def test_extract_route_request_parses_via_segments():
    request = route_planning.extract_route_request(
        "Give me walking directions from 51.5034,-0.1276 to Westminster Abbey via Big Ben and St James's Park"
    )
    assert request is not None
    assert request["profile"] == "walk"
    assert request["stops"][0]["coordinates"] == [-0.1276, 51.5034]
    assert request["via"] == [{"query": "Big Ben"}, {"query": "St James's Park"}]


def test_strip_constraints_and_clean_text():
    text = route_planning.strip_constraints_text(
        "Route from A to B avoid flood-risk-zone 167647/3 with major restrictions"
    )
    assert "avoid" not in text.lower()
    assert route_planning.clean_stop_text("origin: Westminster, please.") == "Westminster"
