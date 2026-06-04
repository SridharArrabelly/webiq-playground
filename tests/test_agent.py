"""Tests for the agent layer: tools, registry, and the engine tool loop (offline).

Skipped unless the `agent` extra is installed (azure-ai-projects + openai).
"""

import json

import pytest

pytest.importorskip("azure.ai.projects")
pytest.importorskip("openai")

from webiq_playground.agent import tools
from webiq_playground.agent.registry import AGENTS, AgentSpec, get_spec


class _DummyCtx:
    def __enter__(self):
        return object()

    def __exit__(self, *args):
        return False


def test_tool_is_defined():
    assert tools.WEB_SEARCH_TOOL is not None
    assert tools.WEB_SEARCH_TOOL.name == "web_search"


def test_run_web_search_serializes(monkeypatch):
    web_result = type("W", (), {"title": "T", "url": "U", "content": "C"})()
    response = type("R", (), {"webResults": [web_result], "traceId": "trace-1"})()

    monkeypatch.setattr(tools, "get_client", lambda: _DummyCtx())
    monkeypatch.setattr(tools, "search_web", lambda *a, **k: response)

    out = json.loads(tools.run_web_search("q", ""))
    assert out["results"][0]["title"] == "T"
    assert out["traceId"] == "trace-1"


def test_registry_has_all_features():
    assert set(AGENTS) == {"web", "news", "videos", "images"}
    for feature, spec in AGENTS.items():
        assert spec.agent_name == f"webiq-{feature}-agent"
        assert spec.tool_name == spec.tool.name
        assert callable(spec.executor)
        assert get_spec(feature) is spec


def test_engine_ask_runs_tool_loop(monkeypatch):
    from webiq_playground.agent import engine

    calls = {"executor": 0}

    def fake_executor(query, site=""):
        calls["executor"] += 1
        return json.dumps({"results": []})

    spec = AgentSpec(
        feature="web",
        agent_name="a",
        tool_name="web_search",
        instructions="",
        tool=None,
        executor=fake_executor,
    )

    function_call = type(
        "FC",
        (),
        {
            "type": "function_call",
            "name": "web_search",
            "arguments": '{"query": "q", "site": ""}',
            "call_id": "c1",
        },
    )()
    resp1 = type("R1", (), {"output": [function_call], "id": "r1", "output_text": ""})()
    resp2 = type("R2", (), {"output": [], "id": "r2", "output_text": "FINAL"})()

    class _OpenAIClient:
        def __init__(self):
            self.n = 0

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @property
        def responses(self):
            return self

        def create(self, **kwargs):
            self.n += 1
            return resp1 if self.n == 1 else resp2

    openai_client = _OpenAIClient()

    class _ProjectClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get_openai_client(self):
            return openai_client

    class _Credential:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example")
    monkeypatch.setattr(engine, "DefaultAzureCredential", lambda: _Credential())
    monkeypatch.setattr(engine, "AIProjectClient", lambda **kwargs: _ProjectClient())

    out = engine.ask(spec, "hello")
    assert out == "FINAL"
    assert calls["executor"] == 1
