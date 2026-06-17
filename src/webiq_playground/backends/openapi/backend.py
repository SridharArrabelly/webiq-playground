"""OpenAPI backend: calls the WebIQ REST API directly over HTTP via ``httpx``.

This backend talks to the documented REST endpoints (``POST /search/{feature}``) described
by the WebIQ OpenAPI specification, independent of the official SDK and the MCP protocol.
Requests and responses use the same shapes as the SDK, so results flow through the shared
:func:`~webiq_playground.core.models.normalize_payload`. HTTP errors are mapped to
``webiq.errors`` types so the CLI handles every backend's failures uniformly.
"""

from __future__ import annotations

from typing import Any

import httpx
from webiq.errors import (
    APIStatusError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    WebIQError,
)

from webiq_playground.backends.base import SearchBackend
from webiq_playground.core.auth import auth_headers
from webiq_playground.core.config import REST_BASE_URL

_REQUEST_TIMEOUT = 30.0

# HTTP status -> specific webiq error (everything else -> APIStatusError).
_STATUS_ERRORS: dict[int, type[APIStatusError]] = {
    401: AuthenticationError,
    403: PermissionDeniedError,
    429: RateLimitError,
}


def _raise_for_status(response: httpx.Response) -> None:
    """Raise a ``webiq.errors`` exception for a non-2xx response."""
    if response.is_success:
        return

    try:
        body: Any = response.json()
    except ValueError:
        body = None

    message = None
    if isinstance(body, dict):
        message = body.get("errorMessage") or body.get("message") or body.get("error")
    if not message:
        text = response.text.strip()
        message = text[:200] if text else f"HTTP {response.status_code}"

    trace_id = response.headers.get("x-traceid")
    if not trace_id and isinstance(body, dict):
        trace_id = body.get("traceId")

    error_cls = _STATUS_ERRORS.get(response.status_code, APIStatusError)
    raise error_cls(response.status_code, message, body=body, trace_id=trace_id)


class OpenApiBackend(SearchBackend):
    """WebIQ access via the REST API (the OpenAPI-described HTTP endpoints)."""

    name = "openapi"

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or REST_BASE_URL
        self._client: httpx.Client | None = None

    def _ensure_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(base_url=self._base_url, timeout=_REQUEST_TIMEOUT)
        return self._client

    def close(self) -> None:
        client = self._client
        self._client = None
        if client is not None:
            client.close()

    def _run(self, feature: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._ensure_client().post(
                f"/search/{feature}", json=params, headers=auth_headers()
            )
        except httpx.HTTPError as exc:
            raise WebIQError(f"WebIQ REST request failed: {exc}") from exc

        _raise_for_status(response)
        return response.json()
