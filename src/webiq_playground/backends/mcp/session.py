"""Auth + transport helpers for the WebIQ MCP server (Streamable HTTP, JSON-RPC 2.0).

Authentication is shared with the OpenAPI backend; see
:func:`webiq_playground.core.auth.auth_headers`.
"""

from __future__ import annotations

from webiq_playground.core.auth import auth_headers

__all__ = ["auth_headers"]
