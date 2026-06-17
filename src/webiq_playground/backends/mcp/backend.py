"""MCP backend: calls the WebIQ MCP server tools and normalizes the result.

The official `mcp` Python SDK is async, so each call opens a short-lived Streamable HTTP
session and is wrapped with ``asyncio.run`` to present the same synchronous interface as
the SDK backend. Import of `mcp` is lazy so the package loads even without the extra.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from webiq_playground.backends.base import SearchBackend
from webiq_playground.backends.mcp.session import auth_headers
from webiq_playground.core.config import MCP_ENDPOINT


def _payload_from_result(result: Any) -> dict[str, Any]:
    """Extract the JSON payload from an MCP CallToolResult."""
    structured = getattr(result, "structuredContent", None) or getattr(
        result, "structured_content", None
    )
    if isinstance(structured, dict):
        return structured

    for block in getattr(result, "content", None) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except (ValueError, TypeError):
                continue
    return {}


class McpBackend(SearchBackend):
    """WebIQ access via the MCP server (Streamable HTTP, JSON-RPC 2.0)."""

    name = "mcp"

    def __init__(self, endpoint: str | None = None) -> None:
        self.endpoint = endpoint or MCP_ENDPOINT

    async def _call_tool(self, tool: str, args: dict[str, Any]) -> Any:
        from mcp import ClientSession
        from mcp.client.streamable_http import streamablehttp_client

        async with streamablehttp_client(self.endpoint, headers=auth_headers()) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await session.call_tool(tool, args)

    def _run(self, feature: str, params: dict[str, Any]) -> dict[str, Any]:
        result = asyncio.run(self._call_tool(feature, params))
        return _payload_from_result(result)
