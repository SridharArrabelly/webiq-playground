"""Backend abstraction: one contract, swappable implementations (SDK / MCP / OpenAPI).

Each backend exposes the same ``search(feature, query, ...)`` method and returns a
normalized :class:`~webiq_playground.core.models.SearchResult`, so the CLI and the agent
are backend-agnostic. Pick a backend with :func:`get_backend` (or the ``WEBIQ_BACKEND``
environment variable).
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Sequence

from webiq_playground.core.config import DEFAULT_REGION
from webiq_playground.core.models import SearchResult, normalize_payload
from webiq_playground.core.params import DEFAULT_MAX_LENGTH, DEFAULT_MAX_RESULTS, wire_params
from webiq_playground.core.query import build_query

# Search features common to every backend.
FEATURES: tuple[str, ...] = ("web", "news", "videos", "images")

# Features whose tools accept content_format / max_length (text content); the others
# (videos, images) do not.
TEXT_FEATURES: frozenset[str] = frozenset({"web", "news"})

# Known backend names.
BACKENDS: tuple[str, ...] = ("sdk", "mcp", "openapi")

DEFAULT_BACKEND = "sdk"


class SearchBackend(ABC):
    """Common interface implemented by every WebIQ backend.

    ``search`` is a template method: it validates the feature, builds the shared request
    parameters and normalizes the response. Each backend only implements :meth:`_run`,
    which performs the transport-specific call and returns the raw WebIQ payload.
    """

    #: Short backend identifier, e.g. "sdk" or "mcp".
    name: str

    def search(
        self,
        feature: str,
        query: str,
        *,
        site: str | Sequence[str] | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        language: str = "en",
        region: str = DEFAULT_REGION,
        max_length: int = DEFAULT_MAX_LENGTH,
    ) -> SearchResult:
        """Run ``feature`` search for ``query`` and return a normalized result."""
        _validate_feature(feature)
        params = wire_params(
            build_query(query, site),
            max_results=max_results,
            language=language,
            region=region,
            max_length=max_length,
            text=feature in TEXT_FEATURES,
        )
        payload = self._run(feature, params)
        return normalize_payload(feature, self.name, payload)

    @abstractmethod
    def _run(self, feature: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send the request for ``feature`` with ``params`` and return the raw payload.

        ``params`` is the canonical request body from
        :func:`~webiq_playground.core.params.wire_params`.
        """

    def close(self) -> None:  # pragma: no cover - optional override
        """Release any held resources. No-op by default."""

    def __enter__(self) -> "SearchBackend":
        return self

    def __exit__(self, *exc) -> bool:
        self.close()
        return False


def _validate_feature(feature: str) -> None:
    if feature not in FEATURES:
        raise ValueError(f"Unknown feature {feature!r}; choose from {FEATURES}")


def get_backend(name: str | None = None) -> SearchBackend:
    """Return a backend instance.

    ``name`` defaults to the ``WEBIQ_BACKEND`` env var, then ``"sdk"``.
    """
    name = (name or os.environ.get("WEBIQ_BACKEND") or DEFAULT_BACKEND).lower()

    if name == "sdk":
        from webiq_playground.backends.sdk.backend import SdkBackend

        return SdkBackend()
    if name == "mcp":
        from webiq_playground.backends.mcp.backend import McpBackend

        return McpBackend()
    if name == "openapi":
        from webiq_playground.backends.openapi.backend import OpenApiBackend

        return OpenApiBackend()
    raise ValueError(f"Unknown backend {name!r}; choose from {BACKENDS}")
