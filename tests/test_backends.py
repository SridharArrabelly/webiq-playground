"""Tests for the backend layer: SDK backend behavior + the get_backend factory (offline).

Parametrized across every feature so adding one is a single row. Verifies the SDK backend
hits the right namespace, applies `site:` scoping, passes content_format/max_length only
for text features (web, news), and normalizes the response.
"""

import pytest

from webiq_playground.backends import base
from webiq_playground.backends.sdk import backend as sdk_backend


class _FakeNamespace:
    def __init__(self, payload):
        self._payload = payload
        self.called_query = None
        self.called_kwargs = None

    def search(self, query, **kwargs):
        self.called_query = query
        self.called_kwargs = kwargs
        return _FakeResponse(self._payload)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def model_dump(self):
        return self._payload


class _FakeClient:
    def __init__(self):
        self.web = _FakeNamespace({"webResults": [{"title": "W", "url": "u", "content": "c"}],
                                   "traceId": "t"})
        self.news = _FakeNamespace({"newsResults": [{"title": "N", "url": "u", "snippet": "s"}]})
        self.videos = _FakeNamespace({"videoResults": [{"name": "V", "contentUrl": "cu"}]})
        self.images = _FakeNamespace({"imageResults": [{"name": "I", "contentUrl": "cu"}]})


# (feature, passes content_format/max_length)
CASES = [("web", True), ("news", True), ("videos", False), ("images", False)]


@pytest.mark.parametrize("feature,has_content_format", CASES)
def test_sdk_backend_search(monkeypatch, feature, has_content_format):
    fake = _FakeClient()
    monkeypatch.setattr(sdk_backend, "get_client", lambda: fake)

    b = sdk_backend.SdkBackend()
    result = b.search(feature, "deadline", site="sars.gov.za", max_results=3, region="ZA")

    ns = getattr(fake, feature)
    assert ns.called_query == "deadline site:sars.gov.za"
    assert ns.called_kwargs["max_results"] == 3
    assert ns.called_kwargs["region"] == "ZA"

    if has_content_format:
        assert "content_format" in ns.called_kwargs
        assert "max_length" in ns.called_kwargs
    else:
        assert "content_format" not in ns.called_kwargs
        assert "max_length" not in ns.called_kwargs

    assert result.feature == feature
    assert result.backend == "sdk"
    assert len(result.items) == 1
    assert result.items[0].title in {"W", "N", "V", "I"}


def test_sdk_backend_rejects_unknown_feature(monkeypatch):
    monkeypatch.setattr(sdk_backend, "get_client", lambda: _FakeClient())
    with pytest.raises(ValueError):
        sdk_backend.SdkBackend().search("audio", "q")


def test_get_backend_defaults_to_sdk(monkeypatch):
    monkeypatch.delenv("WEBIQ_BACKEND", raising=False)
    assert get_backend_name(base.get_backend()) == "sdk"


def test_get_backend_honors_env(monkeypatch):
    monkeypatch.setenv("WEBIQ_BACKEND", "mcp")
    assert get_backend_name(base.get_backend()) == "mcp"


def test_get_backend_explicit_overrides_env(monkeypatch):
    monkeypatch.setenv("WEBIQ_BACKEND", "mcp")
    assert get_backend_name(base.get_backend("sdk")) == "sdk"


def test_get_backend_unknown_raises():
    with pytest.raises(ValueError):
        base.get_backend("nope")


def get_backend_name(backend):
    return backend.name
