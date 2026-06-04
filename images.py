"""Images Search v3 (Beta) - POST /v3/search/images."""

from __future__ import annotations

from typing import Any

from client import WebIQClient, build_query


def search_images(
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
    return client.post("search/images", payload)
