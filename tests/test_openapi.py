"""Tests for the OpenAPI (REST) backend: search wiring, normalization, error mapping.

Offline — the httpx client's POST is monkeypatched, so no network is used.
"""

import httpx
import pytest

from webiq.errors import APIStatusError, RateLimitError

from webiq_playground.backends.openapi import backend as openapi_backend
from webiq_playground.backends.openapi.backend import OpenApiBackend


def _response(status_code, json_body=None, *, text="", headers=None):
    return httpx.Response(
        status_code,
        json=json_body if json_body is not None else None,
        text=None if json_body is not None else text,
        headers=headers or {},
        request=httpx.Request("POST", "https://example/search/web"),
    )


def test_search_posts_and_normalizes(monkeypatch):
    b = OpenApiBackend()
    captured = {}

    def fake_post(path, *, json, headers):
        captured["path"] = path
        captured["json"] = json
        captured["headers"] = headers
        return _response(
            200,
            {"webResults": [{"title": "T", "url": "U", "content": "C"}], "traceId": "tr"},
        )

    monkeypatch.setattr(b, "_ensure_client", lambda: type("C", (), {"post": staticmethod(fake_post)})())
    monkeypatch.setattr(openapi_backend, "auth_headers", lambda: {"x-apikey": "k"})

    result = b.search("web", "q", site="wikipedia.org", max_results=4)

    assert captured["path"] == "/search/web"
    assert captured["json"]["query"] == "q site:wikipedia.org"
    assert captured["json"]["maxResults"] == 4
    assert captured["headers"] == {"x-apikey": "k"}
    assert result.backend == "openapi"
    assert result.trace_id == "tr"
    assert result.items[0].title == "T"


def test_rate_limit_maps_to_rate_limit_error(monkeypatch):
    b = OpenApiBackend()

    def fake_post(path, *, json, headers):
        return _response(
            429,
            {"message": "Rate limit exceeded"},
            headers={"x-traceid": "tr-429"},
        )

    monkeypatch.setattr(b, "_ensure_client", lambda: type("C", (), {"post": staticmethod(fake_post)})())
    monkeypatch.setattr(openapi_backend, "auth_headers", lambda: {})

    with pytest.raises(RateLimitError) as exc:
        b.search("web", "q")
    assert exc.value.status_code == 429
    assert exc.value.trace_id == "tr-429"


def test_other_status_maps_to_api_status_error(monkeypatch):
    b = OpenApiBackend()

    def fake_post(path, *, json, headers):
        return _response(500, text="boom")

    monkeypatch.setattr(b, "_ensure_client", lambda: type("C", (), {"post": staticmethod(fake_post)})())
    monkeypatch.setattr(openapi_backend, "auth_headers", lambda: {})

    with pytest.raises(APIStatusError) as exc:
        b.search("web", "q")
    assert exc.value.status_code == 500


def test_unknown_feature_rejected():
    b = OpenApiBackend()
    with pytest.raises(ValueError):
        b.search("bogus", "q")
