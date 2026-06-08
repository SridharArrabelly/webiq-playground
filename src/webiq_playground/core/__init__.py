"""Shared, backend-agnostic building blocks (config, query helpers, models)."""

from webiq_playground.core.config import DEFAULT_REGION, MCP_ENDPOINT, REST_BASE_URL, WEBIQ_API_SCOPE
from webiq_playground.core.models import SearchItem, SearchResult, normalize_payload
from webiq_playground.core.query import build_query

__all__ = [
    "DEFAULT_REGION",
    "MCP_ENDPOINT",
    "REST_BASE_URL",
    "WEBIQ_API_SCOPE",
    "SearchItem",
    "SearchResult",
    "normalize_payload",
    "build_query",
]
