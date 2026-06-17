"""The WebIQ request contract, defined once for every backend.

The REST API, the MCP tools and the SDK all accept the *same* request parameters
(see the official docs: the MCP tools "accept the same parameters as the REST API").
:func:`wire_params` builds that canonical camelCase request body so the OpenAPI and MCP
backends share a single definition; the SDK backend translates the same values into the
SDK's snake_case keyword arguments.
"""

from __future__ import annotations

from typing import Any

# Content format used for text features (web, news). The API also supports
# "passage", "html" and "markdown"; "text" returns plain extracted content.
TEXT_CONTENT_FORMAT = "text"

# Default upper bound on returned text length (characters) for text features.
DEFAULT_MAX_LENGTH = 2000

# Default number of results requested.
DEFAULT_MAX_RESULTS = 5


def wire_params(
    query: str,
    *,
    max_results: int = DEFAULT_MAX_RESULTS,
    language: str = "en",
    region: str,
    max_length: int = DEFAULT_MAX_LENGTH,
    text: bool,
) -> dict[str, Any]:
    """Build the canonical WebIQ request body (camelCase, as sent over the wire).

    ``text`` enables the ``contentFormat`` / ``maxLength`` parameters, which only apply
    to text features (web, news); media features (videos, images) omit them.
    """
    params: dict[str, Any] = {
        "query": query,
        "maxResults": max_results,
        "language": language,
        "region": region,
    }
    if text:
        params["contentFormat"] = TEXT_CONTENT_FORMAT
        params["maxLength"] = max_length
    return params
