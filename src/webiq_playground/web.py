"""Web Search via the official webiq SDK."""

from __future__ import annotations

from typing import Any

from webiq import WebIQClient
from webiq.types import ContentFormat

from .client import DEFAULT_REGION, build_query


def search_web(
    client: WebIQClient,
    query: str,
    *,
    site: str | None = None,
    max_results: int = 5,
    language: str = "en",
    region: str = DEFAULT_REGION,
    max_length: int = 2000,
    content_format: ContentFormat = ContentFormat.text,
) -> Any:
    return client.web.search(
        build_query(query, site),
        max_results=max_results,
        language=language,
        region=region,
        max_length=max_length,
        content_format=content_format,
    )
