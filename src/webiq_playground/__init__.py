"""WebIQ Playground — multi-backend access to the Microsoft Web IQ APIs.

Features (web, news, videos, images) are reachable through interchangeable backends:
SDK (`webiq`), MCP (the WebIQ MCP server), and later OpenAPI.
"""

__version__ = "0.2.0"

from .backends.base import FEATURES, get_backend
from .core.config import DEFAULT_REGION
from .core.models import SearchItem, SearchResult
from .core.query import build_query

__all__ = [
    "FEATURES",
    "get_backend",
    "build_query",
    "SearchItem",
    "SearchResult",
    "DEFAULT_REGION",
]
