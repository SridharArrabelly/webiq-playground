"""Shared authentication for HTTP-based WebIQ backends (MCP and OpenAPI).

Produces the HTTP headers used to authenticate to the WebIQ endpoints: ``x-apikey`` when
``WEBIQ_API_KEY`` is set, otherwise an Entra ID bearer token via ``DefaultAzureCredential``
(scope :data:`~webiq_playground.core.config.WEBIQ_API_SCOPE`). The credential is created
once and reused; a fresh token is requested on each call so token refresh still works.
"""

from __future__ import annotations

from typing import Any

from webiq_playground.core.config import WEBIQ_API_SCOPE, get_api_key

_credential: Any | None = None


def _get_credential() -> Any:
    """Return a cached ``DefaultAzureCredential`` (created lazily)."""
    global _credential
    if _credential is None:
        try:
            from azure.identity import DefaultAzureCredential
        except ImportError as exc:
            raise RuntimeError(
                "No WEBIQ_API_KEY set and azure-identity is not installed. Set "
                "WEBIQ_API_KEY in .env, or install the Entra extra: uv sync --extra entra"
            ) from exc
        _credential = DefaultAzureCredential()
    return _credential


def auth_headers() -> dict[str, str]:
    """Build authentication headers for a WebIQ HTTP request."""
    api_key = get_api_key()
    if api_key:
        return {"x-apikey": api_key}

    token = _get_credential().get_token(WEBIQ_API_SCOPE).token
    return {"Authorization": f"Bearer {token}"}
