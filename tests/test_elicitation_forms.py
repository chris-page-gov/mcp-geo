from server.mcp import elicitation_forms as forms


def test_client_supports_elicitation_form_variants():
    assert forms.client_supports_elicitation_form("nope") is False
    assert forms.client_supports_elicitation_form({}) is False
    assert forms.client_supports_elicitation_form({"elicitation": None}) is False
    assert forms.client_supports_elicitation_form({"elicitation": "nope"}) is False
    assert forms.client_supports_elicitation_form({"elicitation": {}}) is True
    assert forms.client_supports_elicitation_form({"elicitation": {"url": {}}}) is False
    assert forms.client_supports_elicitation_form({"elicitation": {"form": {}}}) is True


def test_normalize_geography_level_blank_and_aliases():
    assert forms.normalize_ons_select_geography_level(" ") is None
    assert forms.normalize_ons_select_geography_level("Local authority") == "local_authority"
    assert forms.normalize_ons_select_geography_level("local-authority") == "local_authority"
    assert forms.normalize_ons_select_geography_level("nation") == "nation"
    assert forms.normalize_ons_select_geography_level("weird") == "weird"


def test_normalize_time_granularity_blank_and_aliases():
    assert forms.normalize_ons_select_time_granularity(" ") is None
    assert forms.normalize_ons_select_time_granularity("annual") == "year"
    assert forms.normalize_ons_select_time_granularity("quarterly") == "quarter"
    assert forms.normalize_ons_select_time_granularity("monthly") == "month"
    assert forms.normalize_ons_select_time_granularity("latest") == "latest"


def test_coerce_string_list_variants():
    assert forms._coerce_string_list(None) is None
    assert forms._coerce_string_list(["a", "", 123]) == ["a"]
    assert forms._coerce_string_list("a, b; c\n") == ["a", "b", "c"]
    assert forms._coerce_string_list("") is None


def test_build_ons_select_elicitation_params_defaults_and_message():
    payload = {
        "geographyLevel": "Local authority",
        "timeGranularity": "annual",
        "intentTags": ["inflation", "prices"],
    }
    params = forms.build_ons_select_elicitation_params(
        "inflation",
        payload,
        questions=["Which geography level?", "What time basis?"],
    )
    assert params.get("mode") == "form"
    assert "Which geography level?" in params.get("message", "")
    schema = params.get("requestedSchema", {})
    props = schema.get("properties", {})
    assert props["geographyLevel"]["default"] == "local_authority"
    assert props["timeGranularity"]["default"] == "year"
    assert props["intentTags"]["default"] == "inflation, prices"

    params = forms.build_ons_select_elicitation_params(
        "inflation",
        {"intentTags": "inflation, prices"},
        questions=None,
    )
    props = params.get("requestedSchema", {}).get("properties", {})
    assert props["intentTags"]["default"] == "inflation, prices"


def test_apply_ons_select_elicitation_result_actions_and_content_parsing():
    payload = {}
    changed, error = forms.apply_ons_select_elicitation_result(payload, {"action": "cancel"})
    assert changed is False
    assert error is None

    changed, error = forms.apply_ons_select_elicitation_result(payload, {"action": "unexpected"})
    assert changed is False
    assert error and error.get("code") == "ELICITATION_INVALID_RESULT"

    payload = {}
    changed, error = forms.apply_ons_select_elicitation_result(payload, {"action": "accept"})
    assert changed is False
    assert error is None

    payload = {}
    changed, error = forms.apply_ons_select_elicitation_result(
        payload,
        {
            "action": "accept",
            "content": {
                "geographyLevel": "local authority",
                "timeGranularity": "monthly",
                "intentTags": "foo, bar",
            },
        },
    )
    assert error is None
    assert changed is True
    assert payload["geographyLevel"] == "local_authority"
    assert payload["timeGranularity"] == "month"
    assert payload["intentTags"] == ["foo", "bar"]
