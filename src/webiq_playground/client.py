"""Thin convenience layer over the official `webiq` SDK.

Provides:
  * get_client()   - build a webiq client from the environment (.env)
  * build_query()  - add a `site:` operator to scope a query to one domain
  * DEFAULT_REGION - default region used by the feature wrappers
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from webiq import WebIQClient

load_dotenv()

DEFAULT_REGION = "ZA"


def get_client() -> WebIQClient:
    """Create a WebIQ client from the environment.

    Uses WEBIQ_API_KEY when present; otherwise falls back to Entra ID via
    DefaultAzureCredential (install the `entra` extra: uv sync --extra entra).
    """
    api_key = os.environ.get("WEBIQ_API_KEY")
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


def build_query(query: str, site: str | None = None) -> str:
    """Append a `site:` operator to scope results to a single domain."""
    if site:
        return f"{query} site:{site}"
    return query
