"""Normalized result models shared across backends.

Every backend (SDK, MCP, OpenAPI) returns a :class:`SearchResult` so the CLI and the
Foundry agent never depend on a particular backend's payload shape. ``normalize_payload``
maps a raw WebIQ JSON payload (the same shape across REST and MCP) into these models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Response keys that hold the list of results, in priority order.
_RESULT_LIST_KEYS = (
    "webResults",
    "newsResults",
    "videoResults",
    "imageResults",
    "value",
    "results",
)

# Per-item field fallbacks (WebIQ uses different names per feature).
_TITLE_KEYS = ("title", "name")
_URL_KEYS = ("url", "contentUrl", "hostPageUrl")
_CONTENT_KEYS = ("content", "snippet", "description")


@dataclass
class SearchItem:
    """A single normalized result item."""

    title: str | None = None
    url: str | None = None
    content: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "url": self.url, "content": self.content}


@dataclass
class SearchResult:
    """A normalized search response from any backend."""

    feature: str
    backend: str
    items: list[SearchItem] = field(default_factory=list)
    trace_id: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature": self.feature,
            "backend": self.backend,
            "traceId": self.trace_id,
            "results": [item.to_dict() for item in self.items],
        }


def _first(mapping: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value:
            return value
    return None


def _extract_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in _RESULT_LIST_KEYS:
        items = payload.get(key)
        if items:
            return [i for i in items if isinstance(i, dict)]
    return []


def normalize_payload(feature: str, backend: str, payload: dict[str, Any]) -> SearchResult:
    """Map a raw WebIQ payload dict into a :class:`SearchResult`."""
    payload = payload or {}
    items = [
        SearchItem(
            title=_first(item, _TITLE_KEYS),
            url=_first(item, _URL_KEYS),
            content=_first(item, _CONTENT_KEYS),
            raw=item,
        )
        for item in _extract_list(payload)
    ]
    return SearchResult(
        feature=feature,
        backend=backend,
        items=items,
        trace_id=payload.get("traceId"),
        raw=payload,
    )
