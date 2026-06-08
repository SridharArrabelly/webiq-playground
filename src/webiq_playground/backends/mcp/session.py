"""Auth + transport helpers for the WebIQ MCP server (Streamable HTTP, JSON-RPC 2.0)."""

from __future__ import annotations

from webiq_playground.core.config import WEBIQ_API_SCOPE, get_api_key


def auth_headers() -> dict[str, str]:
    """Build the HTTP headers used to authenticate to the WebIQ MCP server.

    Uses ``x-apikey`` when WEBIQ_API_KEY is set; otherwise requests an Entra ID
    bearer token via DefaultAzureCredential (install the `entra` extra).
    """
    api_key = get_api_key()
    if api_key:
        return {"x-apikey": api_key}

    try:
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise RuntimeError(
            "No WEBIQ_API_KEY set and azure-identity is not installed. Set "
            "WEBIQ_API_KEY in .env, or install the Entra extra: uv sync --extra entra"
        ) from exc

    token = DefaultAzureCredential().get_token(WEBIQ_API_SCOPE).token
    return {"Authorization": f"Bearer {token}"}
