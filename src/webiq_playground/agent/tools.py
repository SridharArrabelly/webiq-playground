"""Function tools + executors exposed to the WebIQ Foundry agents.

One `FunctionTool` schema and one `run_<feature>_search` executor per WebIQ feature.
The schema is identical across features (``query`` + ``site``); only the underlying
SDK call and the result attribute differ, so both are produced by small factories.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from azure.ai.projects.models import FunctionTool

from webiq_playground.client import get_client
from webiq_playground.web import search_web
from webiq_playground.news import search_news
from webiq_playground.videos import search_videos
from webiq_playground.images import search_images

MAX_RESULTS = 5

# Result list attribute names the WebIQ SDK may use across features.
_RESULT_ATTRS = (
    "webResults",
    "newsResults",
    "videoResults",
    "imageResults",
    "value",
    "results",
)


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


def _pick(item: Any, names: tuple[str, ...]) -> Any:
    for name in names:
        value = getattr(item, name, None)
        if value:
            return value
    return None


def _extract_items(response: Any) -> list[Any]:
    for attr in _RESULT_ATTRS:
        items = getattr(response, attr, None)
        if items:
            return list(items)
    return []


def _search_to_json(search_fn: Callable[..., Any], query: str, site: str) -> str:
    """Run a WebIQ search wrapper and return JSON the model can ground on."""
    with get_client() as client:
        response = search_fn(client, query, site=site or None, max_results=MAX_RESULTS)

    results = []
    for r in _extract_items(response):
        results.append(
            {
                "title": _pick(r, ("title", "name")),
                "url": _pick(r, ("url", "contentUrl", "hostPageUrl")),
                "content": _pick(r, ("content", "description", "snippet")),
            }
        )
    return json.dumps(
        {"results": results, "traceId": getattr(response, "traceId", None)},
        ensure_ascii=False,
    )


def run_web_search(query: str, site: str = "") -> str:
    return _search_to_json(search_web, query, site)


def run_news_search(query: str, site: str = "") -> str:
    return _search_to_json(search_news, query, site)


def run_video_search(query: str, site: str = "") -> str:
    return _search_to_json(search_videos, query, site)


def run_image_search(query: str, site: str = "") -> str:
    return _search_to_json(search_images, query, site)


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
