"""Tests for the core layer: build_query + payload normalization (offline)."""

from webiq_playground.core.query import build_query
from webiq_playground.core.models import normalize_payload


def test_build_query_adds_site_operator():
    assert build_query("tax", "sars.gov.za") == "tax site:sars.gov.za"


def test_build_query_without_site_is_unchanged():
    assert build_query("tax") == "tax"


def test_build_query_multiple_includes_are_or_grouped():
    assert (
        build_query("llm", ["github.com", "huggingface.co"])
        == "llm (site:github.com OR site:huggingface.co)"
    )


def test_build_query_comma_separated_string():
    assert (
        build_query("llm", "github.com, huggingface.co")
        == "llm (site:github.com OR site:huggingface.co)"
    )


def test_build_query_excludes_are_repeated():
    assert (
        build_query("rag", "-wikipedia.org,-github.com")
        == "rag -site:wikipedia.org -site:github.com"
    )


def test_build_query_mixes_includes_and_excludes():
    assert (
        build_query("rag", ["arxiv.org", "-wikipedia.org"])
        == "rag site:arxiv.org -site:wikipedia.org"
    )


def test_build_query_tolerates_site_prefix_and_blanks():
    assert build_query("rag", ["site:arxiv.org", "", "  "]) == "rag site:arxiv.org"


def test_normalize_web_payload():
    payload = {
        "webResults": [
            {"title": "T", "url": "U", "content": "C", "extra": 1},
        ],
        "traceId": "trace-1",
    }
    result = normalize_payload("web", "sdk", payload)

    assert result.feature == "web"
    assert result.backend == "sdk"
    assert result.trace_id == "trace-1"
    assert len(result.items) == 1
    item = result.items[0]
    assert (item.title, item.url, item.content) == ("T", "U", "C")
    assert item.raw["extra"] == 1


def test_normalize_uses_field_fallbacks():
    # videos/images use name + contentUrl; news uses snippet.
    payload = {"videoResults": [{"name": "N", "contentUrl": "CU", "description": "D"}]}
    result = normalize_payload("videos", "mcp", payload)

    item = result.items[0]
    assert (item.title, item.url, item.content) == ("N", "CU", "D")


def test_normalize_empty_payload():
    result = normalize_payload("web", "sdk", {})
    assert result.items == []
    assert result.trace_id is None
