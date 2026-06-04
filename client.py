"""Shared HTTP client and auth for the Microsoft Web IQ APIs.

Auth precedence:
  1. WEBIQ_API_KEY  -> sent as the `x-apikey` header (quick start, default).
  2. Entra ID       -> AZURE_TENANT_ID + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET,
                       exchanged for a bearer token via MSAL (optional dependency).
"""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.microsoft.ai/v3"


class WebIQError(RuntimeError):
    """Raised when the Web IQ API returns a non-2xx response."""


class WebIQClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = BASE_URL,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or os.environ.get("WEBIQ_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token: str | None = None

        if not self.api_key:
            self._token = self._try_entra_token()

        if not self.api_key and not self._token:
            raise WebIQError(
                "No credentials found. Set WEBIQ_API_KEY in your .env, or configure "
                "AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET."
            )

    @staticmethod
    def _try_entra_token() -> str | None:
        tenant = os.environ.get("AZURE_TENANT_ID")
        client_id = os.environ.get("AZURE_CLIENT_ID")
        secret = os.environ.get("AZURE_CLIENT_SECRET")
        if not (tenant and client_id and secret):
            return None
        try:
            import msal  # optional dependency
        except ImportError as exc:  # pragma: no cover
            raise WebIQError(
                "Entra ID env vars set but 'msal' is not installed. Run: uv add msal"
            ) from exc

        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=f"https://login.microsoftonline.com/{tenant}",
            client_credential=secret,
        )
        result = app.acquire_token_for_client(
            scopes=["https://api.microsoft.ai/.default"]
        )
        if "access_token" not in result:
            raise WebIQError(f"Entra ID token acquisition failed: {result}")
        return result["access_token"]

    def _headers(self) -> dict[str, str]:
        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["x-apikey"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        resp = requests.post(
            url, headers=self._headers(), json=payload, timeout=self.timeout
        )
        if resp.status_code != 200:
            raise WebIQError(f"HTTP {resp.status_code} from {url}: {resp.text}")
        return resp.json()


def build_query(query: str, site: str | None = None) -> str:
    """Append a `site:` operator to scope results to a single domain."""
    if site:
        return f"{query} site:{site}"
    return query
