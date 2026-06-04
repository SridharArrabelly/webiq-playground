"""Web Search v3 - POST /v3/search/web."""

from __future__ import annotations

from typing import Any

from .client import WebIQClient, build_query


def search_web(
    client: WebIQClient,
    query: str,
    *,
    site: str | None = None,
    max_results: int = 5,
    language: str = "en",
    region: str = "ZA",
    max_length: int = 2000,
    content_format: str = "passage",
) -> dict[str, Any]:
    payload = {
        "query": build_query(query, site),
        "maxResults": max_results,
        "language": language,
        "region": region,
        "maxLength": max_length,
        "contentFormat": content_format,
    }
    return client.post("search/web", payload)
