"""Tests for the shared request contract (wire_params), used by every backend."""

from webiq_playground.core.params import (
    DEFAULT_MAX_LENGTH,
    DEFAULT_MAX_RESULTS,
    wire_params,
)


def test_text_feature_includes_content_format():
    params = wire_params(
        "deadline site:wikipedia.org",
        max_results=7,
        language="en",
        region="ZA",
        max_length=1500,
        text=True,
    )
    assert params == {
        "query": "deadline site:wikipedia.org",
        "maxResults": 7,
        "language": "en",
        "region": "ZA",
        "contentFormat": "text",
        "maxLength": 1500,
    }


def test_media_feature_omits_content_format():
    params = wire_params(
        "logo",
        max_results=5,
        language="en",
        region="ZA",
        max_length=2000,
        text=False,
    )
    assert "contentFormat" not in params
    assert "maxLength" not in params
    assert params["query"] == "logo"


def test_defaults_applied():
    params = wire_params("q", region="US", text=False)
    assert params["maxResults"] == DEFAULT_MAX_RESULTS
    assert params["language"] == "en"


def test_default_max_length_for_text():
    params = wire_params("q", region="US", text=True)
    assert params["maxLength"] == DEFAULT_MAX_LENGTH
