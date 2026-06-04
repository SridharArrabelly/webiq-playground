"""Images Search (beta) via the official webiq SDK."""

from __future__ import annotations

from typing import Any

from webiq import WebIQClient

from .client import DEFAULT_REGION, build_query


def search_images(
    client: WebIQClient,
    query: str,
    *,
    site: str | None = None,
    max_results: int = 5,
    language: str = "en",
    region: str = DEFAULT_REGION,
) -> Any:
    return client.images.search(
        build_query(query, site),
        max_results=max_results,
        language=language,
        region=region,
    )
