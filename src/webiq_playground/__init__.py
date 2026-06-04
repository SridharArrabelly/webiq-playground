"""WebIQ Playground - a wrapper around the Microsoft Web IQ search APIs."""

__version__ = "0.1.0"

from .client import WebIQClient, WebIQError, build_query
from .web import search_web
from .news import search_news
from .videos import search_videos
from .images import search_images

__all__ = [
    "WebIQClient",
    "WebIQError",
    "build_query",
    "search_web",
    "search_news",
    "search_videos",
    "search_images",
]
