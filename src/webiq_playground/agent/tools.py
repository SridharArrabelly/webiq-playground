"""Function tools + executors exposed to the WebIQ Foundry agents.

One `FunctionTool` schema and one `run_<feature>_search` executor per WebIQ feature.
The schema is identical across features (``query`` + ``site``); execution goes through
the active backend (SDK or MCP, selected by ``WEBIQ_BACKEND``), so the agent works the
same regardless of how WebIQ is accessed.
"""

from __future__ import annotations

import json

from azure.ai.projects.models import FunctionTool

from webiq_playground.backends.base import get_backend

MAX_RESULTS = 5


def make_search_tool(tool_name: str, description: str) -> FunctionTool:
    """Build a strict query+site search FunctionTool with the given name/description."""
    return FunctionTool(
        name=tool_name,
        description=description,
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g. 'SARS tax filing deadline 2025'.",
                },
                "site": {
                    "type": "string",
                    "description": (
                        "Optional domain to restrict results to, e.g. 'sars.gov.za'. "
                        "Use an empty string for no restriction."
                    ),
                },
            },
            "required": ["query", "site"],
            "additionalProperties": False,
        },
        strict=True,
    )


def _search_to_json(feature: str, query: str, site: str) -> str:
    """Run a WebIQ search via the active backend and return JSON to ground on."""
    with get_backend() as backend:
        result = backend.search(feature, query, site=site or None, max_results=MAX_RESULTS)
    return json.dumps(
        {"results": [item.to_dict() for item in result.items], "traceId": result.trace_id},
        ensure_ascii=False,
    )


def run_web_search(query: str, site: str = "") -> str:
    return _search_to_json("web", query, site)


def run_news_search(query: str, site: str = "") -> str:
    return _search_to_json("news", query, site)


def run_video_search(query: str, site: str = "") -> str:
    return _search_to_json("videos", query, site)


def run_image_search(query: str, site: str = "") -> str:
    return _search_to_json("images", query, site)


# Per-feature tools (kept as module constants for convenience / tests).
WEB_SEARCH_TOOL = make_search_tool(
    "web_search",
    "Search the live web with Microsoft WebIQ and return fresh source passages for "
    "grounding. Use this for any question that needs current, factual, or cited information.",
)
NEWS_SEARCH_TOOL = make_search_tool(
    "news_search",
    "Search recent news articles with Microsoft WebIQ and return fresh source passages "
    "for grounding. Use this for current events and time-sensitive reporting.",
)
VIDEO_SEARCH_TOOL = make_search_tool(
    "video_search",
    "Search for videos with Microsoft WebIQ and return matching video results (title and "
    "URL) for grounding. Use this when the user wants videos or visual demonstrations.",
)
IMAGE_SEARCH_TOOL = make_search_tool(
    "image_search",
    "Search for images with Microsoft WebIQ and return matching image results (title and "
    "URL) for grounding. Use this when the user wants images or pictures.",
)
