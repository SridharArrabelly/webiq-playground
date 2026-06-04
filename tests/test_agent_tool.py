"""Agent tool tests - skipped if the `agent` extra is not installed."""

import json

import pytest

pytest.importorskip("azure.ai.projects")

from webiq_playground.agent import tools


class _DummyCtx:
    def __enter__(self):
        return object()

    def __exit__(self, *args):
        return False


def test_tool_is_defined():
    assert tools.WEB_SEARCH_TOOL is not None


def test_run_web_search_serializes(monkeypatch):
    web_result = type("W", (), {"title": "T", "url": "U", "content": "C"})()
    response = type("R", (), {"webResults": [web_result], "traceId": "trace-1"})()

    monkeypatch.setattr(tools, "get_client", lambda: _DummyCtx())
    monkeypatch.setattr(tools, "search_web", lambda *a, **k: response)

    out = json.loads(tools.run_web_search("q", ""))
    assert out["results"][0]["title"] == "T"
    assert out["traceId"] == "trace-1"


def test_registry_has_all_features():
    from webiq_playground.agent.registry import AGENTS, get_spec

    assert set(AGENTS) == {"web", "news", "videos", "images"}
    for feature, spec in AGENTS.items():
        assert spec.agent_name == f"webiq-{feature}-agent"
        assert spec.tool_name == spec.tool.name
        assert callable(spec.executor)
        assert get_spec(feature) is spec
