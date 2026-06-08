"""MCP backend: calls the WebIQ MCP server tools and normalizes the result.

The official `mcp` Python SDK is async, so each call opens a short-lived Streamable HTTP
session and is wrapped with ``asyncio.run`` to present the same synchronous interface as
the SDK backend. Import of `mcp` is lazy so the package loads even without the extra.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from webiq_playground.backends.base import TEXT_FEATURES, SearchBackend, _validate_feature
from webiq_playground.core.config import DEFAULT_REGION, MCP_ENDPOINT
from webiq_playground.core.models import SearchResult, normalize_payload
from webiq_playground.core.query import build_query
from webiq_playground.backends.mcp.session import auth_headers


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

    def _build_args(
        self,
        feature: str,
        query: str,
        site: str | None,
        max_results: int,
        language: str,
        region: str,
        max_length: int,
    ) -> dict[str, Any]:
        args: dict[str, Any] = {
            "query": build_query(query, site),
            "maxResults": max_results,
            "language": language,
            "region": region,
        }
        if feature in TEXT_FEATURES:
            args["contentFormat"] = "text"
            args["maxLength"] = max_length
        return args

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

    def search(
        self,
        feature: str,
        query: str,
        *,
        site: str | None = None,
        max_results: int = 5,
        language: str = "en",
        region: str = DEFAULT_REGION,
        max_length: int = 2000,
    ) -> SearchResult:
        _validate_feature(feature)
        args = self._build_args(
            feature, query, site, max_results, language, region, max_length
        )
        result = asyncio.run(self._call_tool(feature, args))
        return normalize_payload(feature, self.name, _payload_from_result(result))
