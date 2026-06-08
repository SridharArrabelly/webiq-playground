"""Build a `webiq` SDK client from the environment."""

from __future__ import annotations

from webiq import WebIQClient

from webiq_playground.core.config import get_api_key


def get_client() -> WebIQClient:
    """Create a WebIQ SDK client from the environment.

    Uses WEBIQ_API_KEY when present; otherwise falls back to Entra ID via
    DefaultAzureCredential (install the `entra` extra: uv sync --extra entra).
    """
    api_key = get_api_key()
    if api_key:
        return WebIQClient(api_key=api_key)

    try:
        from azure.identity import DefaultAzureCredential
    except ImportError as exc:
        raise RuntimeError(
            "No WEBIQ_API_KEY set and azure-identity is not installed. Set "
            "WEBIQ_API_KEY in .env, or install the Entra extra: uv sync --extra entra"
        ) from exc
    return WebIQClient(credential=DefaultAzureCredential())
