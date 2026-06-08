"""SDK backend: calls the official `webiq` SDK and normalizes the result."""

from __future__ import annotations

from typing import Any

from webiq_playground.backends.base import TEXT_FEATURES, SearchBackend, _validate_feature
from webiq_playground.backends.sdk.client import get_client
from webiq_playground.core.config import DEFAULT_REGION
from webiq_playground.core.models import SearchResult, normalize_payload
from webiq_playground.core.query import build_query


def _to_payload(response: Any) -> dict[str, Any]:
    """Convert an SDK response (pydantic v2 model) to a plain dict."""
    for attr in ("model_dump", "to_dict", "dict"):
        fn = getattr(response, attr, None)
        if callable(fn):
            try:
                return fn()
            except TypeError:
                return fn(by_alias=True)  # pragma: no cover - defensive
    return dict(response) if isinstance(response, dict) else {}


class SdkBackend(SearchBackend):
    """WebIQ access via the official `webiq` Python SDK."""

    name = "sdk"

    def __init__(self) -> None:
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            self._client = get_client()
        return self._client

    def close(self) -> None:
        client = self._client
        self._client = None
        if client is not None and hasattr(client, "close"):
            client.close()

    def search(
        self,
        feature: str,
        query: str,
        *,
        site: str | None = None,
        max_results: int = 5,
        language: str = "en",
        region: str = DEFAULT_REGION,
        max_length: int = 2000,
    ) -> SearchResult:
        _validate_feature(feature)
        client = self._ensure_client()
        namespace = getattr(client, feature)

        kwargs: dict[str, Any] = {
            "max_results": max_results,
            "language": language,
            "region": region,
        }
        if feature in TEXT_FEATURES:
            from webiq.types import ContentFormat

            kwargs["content_format"] = ContentFormat.text
            kwargs["max_length"] = max_length

        response = namespace.search(build_query(query, site), **kwargs)
        return normalize_payload(feature, self.name, _to_payload(response))
