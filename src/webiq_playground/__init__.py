"""WebIQ Playground - a thin wrapper around the official Microsoft webiq SDK."""

__version__ = "0.1.0"

from .client import build_query, get_client
from .web import search_web
from .news import search_news
from .videos import search_videos
from .images import search_images

__all__ = [
    "build_query",
    "get_client",
    "search_web",
    "search_news",
    "search_videos",
    "search_images",
]
