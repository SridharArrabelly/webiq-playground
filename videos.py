"""Videos Search v3 - POST /v3/search/videos."""

from __future__ import annotations

from typing import Any

from client import WebIQClient, build_query


def search_videos(
    client: WebIQClient,
    query: str,
    *,
    site: str | None = None,
    max_results: int = 5,
    language: str = "en",
    region: str = "ZA",
) -> dict[str, Any]:
    payload = {
        "query": build_query(query, site),
        "maxResults": max_results,
        "language": language,
        "region": region,
    }
    return client.post("search/videos", payload)
