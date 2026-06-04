"""Backward-compatible shim. Prefer `webiq-agent ask <feature> "..."` (see agent.cli).

Kept so existing imports of ``ask`` / ``main`` keep working; the real logic now lives in
``engine.ask`` driven by the ``registry`` spec.
"""

from __future__ import annotations

import argparse

from webiq_playground.agent.engine import ask as _engine_ask
from webiq_playground.agent.registry import get_spec


def ask(question: str, *, feature: str = "web") -> str:
    return _engine_ask(get_spec(feature), question)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the WebIQ web grounding agent")
    parser.add_argument("question", help="Your question")
    parser.add_argument("--feature", default="web", help="Feature agent (default: web)")
    args = parser.parse_args()

    print(f"[*] Asking: {args.question!r}")
    print("\n=== Answer ===")
    print(ask(args.question, feature=args.feature))


if __name__ == "__main__":
    main()

