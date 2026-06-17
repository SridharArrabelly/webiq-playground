"""Tests for the get_backend() factory in backends/base.py (offline).

Per-backend behavior lives in test_sdk.py, test_mcp.py and test_openapi.py; this file
only covers backend selection (default, WEBIQ_BACKEND env, explicit override, errors).
"""

import pytest

from webiq_playground.backends import base


def test_get_backend_defaults_to_sdk(monkeypatch):
    monkeypatch.delenv("WEBIQ_BACKEND", raising=False)
    assert base.get_backend().name == "sdk"


def test_get_backend_honors_env(monkeypatch):
    monkeypatch.setenv("WEBIQ_BACKEND", "mcp")
    assert base.get_backend().name == "mcp"


def test_get_backend_explicit_overrides_env(monkeypatch):
    monkeypatch.setenv("WEBIQ_BACKEND", "mcp")
    assert base.get_backend("sdk").name == "sdk"


def test_get_backend_supports_openapi(monkeypatch):
    monkeypatch.delenv("WEBIQ_BACKEND", raising=False)
    assert base.get_backend("openapi").name == "openapi"


def test_get_backend_unknown_raises():
    with pytest.raises(ValueError):
        base.get_backend("nope")
