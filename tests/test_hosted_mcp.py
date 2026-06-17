"""Tests for the hosted (server-side) WebIQ MCP agent (offline).

Skipped unless the `agent` extra is installed (azure-ai-projects + openai).
"""

import pytest

pytest.importorskip("azure.ai.projects")
pytest.importorskip("openai")

from azure.ai.projects.models import MCPTool

from webiq_playground.agent import hosted_mcp


def test_build_tool_wires_connection(monkeypatch):
    monkeypatch.setenv("WEBIQ_MCP_CONNECTION_ID", "WebIQ-MCP")
    tool = hosted_mcp.build_tool()
    assert isinstance(tool, MCPTool)
    assert tool.type == "mcp"
    assert tool.server_label == hosted_mcp.WEBIQ_MCP_SERVER_LABEL
    assert tool.project_connection_id == "WebIQ-MCP"
    assert tool.require_approval == "never"
    assert tool.allowed_tools == hosted_mcp.WEBIQ_MCP_TOOLS


def test_build_tool_requires_connection_id(monkeypatch):
    monkeypatch.delenv("WEBIQ_MCP_CONNECTION_ID", raising=False)
    with pytest.raises(KeyError):
        hosted_mcp.build_tool()


def test_create_agent_attaches_single_mcp_tool(monkeypatch):
    monkeypatch.setenv("WEBIQ_MCP_CONNECTION_ID", "WebIQ-MCP")
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example")
    monkeypatch.setenv("FOUNDRY_MODEL_NAME", "gpt-4o")

    captured: dict = {}

    class _Agents:
        def create_version(self, agent_name, definition):
            captured["agent_name"] = agent_name
            captured["definition"] = definition
            return type("A", (), {"name": agent_name, "version": "1", "id": "id1"})()

    class _ProjectClient:
        agents = _Agents()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class _Credential:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(hosted_mcp, "DefaultAzureCredential", lambda: _Credential())
    monkeypatch.setattr(hosted_mcp, "AIProjectClient", lambda **kwargs: _ProjectClient())

    name = hosted_mcp.create_agent()
    assert name == hosted_mcp.HOSTED_AGENT_NAME
    tools = captured["definition"].tools
    assert len(tools) == 1
    assert isinstance(tools[0], MCPTool)
    assert tools[0].server_label == hosted_mcp.WEBIQ_MCP_SERVER_LABEL
    assert tools[0].project_connection_id == "WebIQ-MCP"


def test_ask_returns_output_text_without_tool_loop(monkeypatch):
    monkeypatch.setenv("FOUNDRY_PROJECT_ENDPOINT", "https://example")
    calls = {"create": 0}

    class _OpenAIClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        @property
        def responses(self):
            return self

        def create(self, **kwargs):
            calls["create"] += 1
            assert "[Current date:" in kwargs["input"]
            return type("R", (), {"output_text": "ANSWER"})()

    class _ProjectClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get_openai_client(self):
            return _OpenAIClient()

    class _Credential:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(hosted_mcp, "DefaultAzureCredential", lambda: _Credential())
    monkeypatch.setattr(hosted_mcp, "AIProjectClient", lambda **kwargs: _ProjectClient())

    assert hosted_mcp.ask("hello") == "ANSWER"
    assert calls["create"] == 1
