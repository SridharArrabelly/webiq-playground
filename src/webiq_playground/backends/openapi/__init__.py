"""OpenAPI backend: call the WebIQ REST API directly over HTTP.

Exposes the same :class:`~webiq_playground.backends.base.SearchBackend` contract as the
SDK and MCP backends, driving the documented REST endpoints (``POST /search/{feature}``)
with ``httpx``.
"""

from webiq_playground.backends.openapi.backend import OpenApiBackend

__all__ = ["OpenApiBackend"]
