"""Backward-compatible shim. Prefer `webiq-agent create <feature>` (see agent.cli).

Kept so existing imports of ``AGENT_NAME`` / ``main`` keep working; the real logic now
lives in ``engine.create_agent`` driven by the ``registry`` spec.
"""

from __future__ import annotations

from webiq_playground.agent.engine import create_agent
from webiq_playground.agent.registry import get_spec

AGENT_NAME = get_spec("web").agent_name


def main() -> None:
    create_agent(get_spec("web"))


if __name__ == "__main__":
    main()

