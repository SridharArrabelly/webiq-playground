"""SDK backend: calls the official `webiq` SDK and normalizes the result."""

from __future__ import annotations

from typing import Any

from webiq_playground.backends.base import SearchBackend
from webiq_playground.backends.sdk.client import get_client


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

    def _run(self, feature: str, params: dict[str, Any]) -> dict[str, Any]:
        namespace = getattr(self._ensure_client(), feature)

        kwargs: dict[str, Any] = {
            "max_results": params["maxResults"],
            "language": params["language"],
            "region": params["region"],
        }
        if "contentFormat" in params:
            from webiq.types import ContentFormat

            kwargs["content_format"] = ContentFormat(params["contentFormat"])
            kwargs["max_length"] = params["maxLength"]

        response = namespace.search(params["query"], **kwargs)
        return _to_payload(response)
