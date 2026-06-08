"""Interchangeable WebIQ backends (SDK, MCP, OpenAPI)."""

from webiq_playground.backends.base import (
    BACKENDS,
    FEATURES,
    TEXT_FEATURES,
    SearchBackend,
    get_backend,
)

__all__ = ["BACKENDS", "FEATURES", "TEXT_FEATURES", "SearchBackend", "get_backend"]
