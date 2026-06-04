"""Tests for the client layer: build_query + get_client auth selection (offline)."""

import sys
import types

from webiq_playground import client as client_mod


def test_build_query_adds_site_operator():
    assert client_mod.build_query("tax", "sars.gov.za") == "tax site:sars.gov.za"


def test_build_query_without_site_is_unchanged():
    assert client_mod.build_query("tax") == "tax"


class _FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


def test_get_client_uses_api_key(monkeypatch):
    monkeypatch.setattr(client_mod, "WebIQClient", _FakeClient)
    monkeypatch.setenv("WEBIQ_API_KEY", "secret")

    c = client_mod.get_client()
    assert c.kwargs == {"api_key": "secret"}


def test_get_client_falls_back_to_entra(monkeypatch):
    monkeypatch.setattr(client_mod, "WebIQClient", _FakeClient)
    monkeypatch.delenv("WEBIQ_API_KEY", raising=False)

    # Inject a fake azure.identity so the test does not require the entra extra.
    sentinel = object()
    fake_identity = types.ModuleType("azure.identity")
    fake_identity.DefaultAzureCredential = lambda: sentinel
    monkeypatch.setitem(sys.modules, "azure", types.ModuleType("azure"))
    monkeypatch.setitem(sys.modules, "azure.identity", fake_identity)

    c = client_mod.get_client()
    assert c.kwargs == {"credential": sentinel}
