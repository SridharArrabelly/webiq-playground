"""Central configuration shared by every backend.

Loads `.env` once and exposes the endpoints, default region and Entra scope used by
the SDK, MCP and (later) OpenAPI backends.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Default region for searches (2-letter country code).
DEFAULT_REGION = "US"

# Microsoft Web IQ endpoints.
REST_BASE_URL = "https://api.microsoft.ai/v3"
MCP_ENDPOINT = os.environ.get("WEBIQ_MCP_ENDPOINT", "https://api.microsoft.ai/v3/mcp")

# Entra ID scope for app-only tokens (used when no API key is configured).
WEBIQ_API_SCOPE = "https://api.microsoft.ai/.default"


def get_api_key() -> str | None:
    """Return the WebIQ API key from the environment, if set."""
    return os.environ.get("WEBIQ_API_KEY")
