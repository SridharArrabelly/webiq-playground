"""Query helpers shared by every backend."""

from __future__ import annotations

from typing import Iterable, Sequence


def _normalize_sites(site: str | Sequence[str] | None) -> tuple[list[str], list[str]]:
    """Split a site spec into (includes, excludes) lists of bare domains.

    ``site`` may be a single domain, a comma/space-separated string, or a sequence of
    domains. A domain prefixed with ``-`` is an exclusion. A leading ``site:`` is tolerated.
    """
    if not site:
        return [], []

    tokens: Iterable[str]
    if isinstance(site, str):
        tokens = site.replace(",", " ").split()
    else:
        tokens = [part for item in site for part in str(item).replace(",", " ").split()]

    includes: list[str] = []
    excludes: list[str] = []
    for token in tokens:
        exclude = token.startswith("-")
        domain = token[1:] if exclude else token
        if domain.startswith("site:"):
            domain = domain[len("site:") :]
        # Reduce a full URL/path to its bare host: site: only matches a domain, so
        # "https://www.mtn.com/investors" and "www.mtn.com/investors" both become
        # "www.mtn.com".
        if "://" in domain:
            domain = domain.split("://", 1)[1]
        domain = domain.split("/", 1)[0].strip()
        if not domain:
            continue
        (excludes if exclude else includes).append(domain)
    return includes, excludes


def build_query(query: str, site: str | Sequence[str] | None = None) -> str:
    """Scope ``query`` with ``site:`` / ``-site:`` operators for one or more domains.

    ``site`` accepts a single domain, a comma/space-separated string, or a sequence of
    domains. Prefix a domain with ``-`` to exclude it. Inclusions are OR-ed together (so
    results may come from any of them); each exclusion is appended as ``-site:``.

    Examples::

        build_query("rag", "learn.microsoft.com")
        # -> "rag site:learn.microsoft.com"

        build_query("open source LLM", ["github.com", "huggingface.co"])
        # -> "open source LLM (site:github.com OR site:huggingface.co)"

        build_query("rag", "arxiv.org,-wikipedia.org")
        # -> "rag site:arxiv.org -site:wikipedia.org"
    """
    includes, excludes = _normalize_sites(site)

    parts: list[str] = []
    if len(includes) == 1:
        parts.append(f"site:{includes[0]}")
    elif includes:
        parts.append("(" + " OR ".join(f"site:{d}" for d in includes) + ")")
    parts.extend(f"-site:{d}" for d in excludes)

    if not parts:
        return query
    return f"{query} {' '.join(parts)}"
