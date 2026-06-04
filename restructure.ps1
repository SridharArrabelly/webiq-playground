# Restructure webiq-playground into a src/ package layout.
# Run once from the project root:
#   cd C:\Users\sarrabelly\Documents\GitHub\webiq-playground
#   powershell -ExecutionPolicy Bypass -File .\restructure.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pkg = "src\webiq_playground"
New-Item -ItemType Directory -Force -Path $pkg, "tests" | Out-Null

# --- src/webiq_playground/__init__.py ---
Set-Content -Encoding UTF8 -Path "$pkg\__init__.py" -Value @'
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
'@

# --- src/webiq_playground/client.py ---
Set-Content -Encoding UTF8 -Path "$pkg\client.py" -Value @'
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
                "Entra ID env vars set but 'msal' is not installed. "
                "Run: uv sync --extra entra"
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
'@

# --- src/webiq_playground/web.py ---
Set-Content -Encoding UTF8 -Path "$pkg\web.py" -Value @'
"""Web Search v3 - POST /v3/search/web."""

from __future__ import annotations

from typing import Any

from .client import WebIQClient, build_query


def search_web(
    client: WebIQClient,
    query: str,
    *,
    site: str | None = None,
    max_results: int = 5,
    language: str = "en",
    region: str = "ZA",
    max_length: int = 2000,
    content_format: str = "passage",
) -> dict[str, Any]:
    payload = {
        "query": build_query(query, site),
        "maxResults": max_results,
        "language": language,
        "region": region,
        "maxLength": max_length,
        "contentFormat": content_format,
    }
    return client.post("search/web", payload)
'@

# --- src/webiq_playground/news.py ---
Set-Content -Encoding UTF8 -Path "$pkg\news.py" -Value @'
"""News Search v3 (Beta) - POST /v3/search/news."""

from __future__ import annotations

from typing import Any

from .client import WebIQClient, build_query


def search_news(
    client: WebIQClient,
    query: str,
    *,
    site: str | None = None,
    max_results: int = 5,
    language: str = "en",
    region: str = "ZA",
) -> dict[str, Any]:
    payload = {
        "query": build_query(query, site),
        "maxResults": max_results,
        "language": language,
        "region": region,
    }
    return client.post("search/news", payload)
'@

# --- src/webiq_playground/videos.py ---
Set-Content -Encoding UTF8 -Path "$pkg\videos.py" -Value @'
"""Videos Search v3 - POST /v3/search/videos."""

from __future__ import annotations

from typing import Any

from .client import WebIQClient, build_query


def search_videos(
    client: WebIQClient,
    query: str,
    *,
    site: str | None = None,
    max_results: int = 5,
    language: str = "en",
    region: str = "ZA",
) -> dict[str, Any]:
    payload = {
        "query": build_query(query, site),
        "maxResults": max_results,
        "language": language,
        "region": region,
    }
    return client.post("search/videos", payload)
'@

# --- src/webiq_playground/images.py ---
Set-Content -Encoding UTF8 -Path "$pkg\images.py" -Value @'
"""Images Search v3 (Beta) - POST /v3/search/images."""

from __future__ import annotations

from typing import Any

from .client import WebIQClient, build_query


def search_images(
    client: WebIQClient,
    query: str,
    *,
    site: str | None = None,
    max_results: int = 5,
    language: str = "en",
    region: str = "ZA",
) -> dict[str, Any]:
    payload = {
        "query": build_query(query, site),
        "maxResults": max_results,
        "language": language,
        "region": region,
    }
    return client.post("search/images", payload)
'@

# --- src/webiq_playground/cli.py ---
Set-Content -Encoding UTF8 -Path "$pkg\cli.py" -Value @'
"""WebIQ Playground CLI.

Usage (after `uv sync`):
  uv run webiq web "tax filing deadline" --site sars.gov.za
  uv run webiq news "budget speech" --site sars.gov.za --max 10
  uv run webiq videos "how to register for efiling"
  uv run webiq images "sars logo"
"""

from __future__ import annotations

import argparse
import json
import sys

from .client import WebIQClient, WebIQError
from .web import search_web
from .news import search_news
from .videos import search_videos
from .images import search_images

FEATURES = {
    "web": search_web,
    "news": search_news,
    "videos": search_videos,
    "images": search_images,
}

# Per-feature key holding the list of results in the JSON response.
RESULT_KEYS = {
    "web": "webResults",
    "news": "newsResults",
    "videos": "videoResults",
    "images": "imageResults",
}


def _print_results(feature: str, data: dict) -> None:
    print(f"[*] traceId: {data.get('traceId')}")
    key = RESULT_KEYS[feature]
    results = data.get(key) or []
    print(f"[*] {len(results)} result(s) in '{key}':")
    for i, r in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Title: {r.get('title')}")
        print(f"URL:   {r.get('url')}")
        content = (r.get("content") or r.get("snippet") or "").strip().replace("\n", " ")
        if content:
            print(f"Text:  {content[:400]}{'...' if len(content) > 400 else ''}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Microsoft Web IQ playground CLI")
    parser.add_argument("feature", choices=FEATURES.keys(), help="Which Web IQ API to call")
    parser.add_argument("query", help="Search query text")
    parser.add_argument("--site", default=None, help="Restrict results to a domain, e.g. sars.gov.za")
    parser.add_argument("--max", type=int, default=5, dest="max_results", help="Max results (1-50)")
    parser.add_argument("--region", default="ZA", help="2-letter region code (default ZA)")
    parser.add_argument("--language", default="en", help="2-letter language code (default en)")
    parser.add_argument("--save", default="webiq_response.json", help="Where to dump the full JSON")
    args = parser.parse_args(argv)

    try:
        client = WebIQClient()
    except WebIQError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 2

    fn = FEATURES[args.feature]
    query = f"{args.query} site:{args.site}" if args.site else args.query
    print(f"[*] {args.feature} search: {query!r}")

    try:
        data = fn(
            client,
            args.query,
            site=args.site,
            max_results=args.max_results,
            language=args.language,
            region=args.region,
        )
    except WebIQError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1

    _print_results(args.feature, data)

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n[*] Full response saved to {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'@

# --- tests/test_smoke.py ---
Set-Content -Encoding UTF8 -Path "tests\test_smoke.py" -Value @'
"""Offline smoke tests - no network calls."""

from webiq_playground import build_query


def test_build_query_adds_site_operator():
    assert build_query("tax", "sars.gov.za") == "tax site:sars.gov.za"


def test_build_query_without_site_is_unchanged():
    assert build_query("tax") == "tax"
'@

# --- test_webiq.py (root example, uses the installed package) ---
Set-Content -Encoding UTF8 -Path "test_webiq.py" -Value @'
"""Minimal example: a web search scoped to sars.gov.za.

Run:
  uv run python test_webiq.py
"""

from webiq_playground import WebIQClient, search_web


def main() -> None:
    client = WebIQClient()
    data = search_web(client, "tax filing deadline", site="sars.gov.za", max_results=5)
    print(f"traceId: {data.get('traceId')}")
    for i, r in enumerate(data.get("webResults", []), 1):
        print(f"{i}. {r.get('title')} -> {r.get('url')}")


if __name__ == "__main__":
    main()
'@

# --- pyproject.toml (add build backend + console script) ---
Set-Content -Encoding UTF8 -Path "pyproject.toml" -Value @'
[project]
name = "webiq-playground"
version = "0.1.0"
description = "A playground for the Microsoft Web IQ APIs (web, news, videos, images search)."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "python-dotenv>=1.2.2",
    "requests>=2.34.2",
]

[project.optional-dependencies]
entra = ["msal>=1.37.0"]

[dependency-groups]
dev = ["pytest>=8"]

[project.scripts]
webiq = "webiq_playground.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/webiq_playground"]
'@

# --- Remove the old flat modules + leftover junk ---
Remove-Item -ErrorAction SilentlyContinue `
    .\client.py, .\web.py, .\news.py, .\videos.py, .\images.py, .\cli.py, `
    .\test_webiq.py.tmp, .\.env.example.new

# --- Ensure pyproject.toml has no UTF-8 BOM (tomllib rejects it) ---
$pp = Join-Path $PSScriptRoot "pyproject.toml"
[System.IO.File]::WriteAllText($pp, (Get-Content $pp -Raw), (New-Object System.Text.UTF8Encoding($false)))

# --- Install the package (editable) so imports + the `webiq` command work ---
uv sync

Write-Host ""
Write-Host "Restructure complete. Try it:"
Write-Host "  uv run webiq web `"tax filing deadline`" --site sars.gov.za"
Write-Host "  uv run pytest -q"
