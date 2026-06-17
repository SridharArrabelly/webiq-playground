"""Tests for the MCP backend: result parsing + search wiring (offline, no network).

Skipped unless the `mcp` extra is installed.
"""

import pytest

pytest.importorskip("mcp")

from webiq_playground.backends.mcp import backend as mcp_backend


def test_payload_from_structured_content():
    result = type("R", (), {"structuredContent": {"webResults": [{"title": "T"}]}})()
    assert mcp_backend._payload_from_result(result) == {"webResults": [{"title": "T"}]}


def test_payload_from_text_content_json():
    block = type("B", (), {"text": '{"webResults": [{"title": "T2"}]}'})()
    result = type("R", (), {"content": [block]})()
    assert mcp_backend._payload_from_result(result) == {"webResults": [{"title": "T2"}]}


def test_payload_from_result_empty():
    result = type("R", (), {"content": []})()
    assert mcp_backend._payload_from_result(result) == {}


def test_search_normalizes(monkeypatch):
    b = mcp_backend.McpBackend()

    captured = {}

    async def fake_call_tool(tool, args):
        captured["tool"] = tool
        captured["args"] = args
        return type("R", (), {"structuredContent": {
            "webResults": [{"title": "T", "url": "U", "content": "C"}],
            "traceId": "tr",
        }})()

    monkeypatch.setattr(b, "_call_tool", fake_call_tool)

    result = b.search("web", "q", site="sars.gov.za", max_results=4)

    assert captured["tool"] == "web"
    assert captured["args"]["query"] == "q site:sars.gov.za"
    assert captured["args"]["maxResults"] == 4
    assert result.backend == "mcp"
    assert result.trace_id == "tr"
    assert result.items[0].title == "T"
