"""Query helpers shared by every backend."""

from __future__ import annotations


def build_query(query: str, site: str | None = None) -> str:
    """Append a `site:` operator to scope results to a single domain."""
    if site:
        return f"{query} site:{site}"
    return query
