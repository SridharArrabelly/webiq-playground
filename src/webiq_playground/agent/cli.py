"""Unified CLI for the WebIQ Foundry agents: `webiq-agent`.

    webiq-agent create web              # create/update one feature agent
    webiq-agent create --all            # create/update every feature agent
    webiq-agent ask web "question..."   # ask a feature agent
"""

from __future__ import annotations

import argparse

from webiq_playground.agent.engine import ask as engine_ask
from webiq_playground.agent.engine import create_agent
from webiq_playground.agent.registry import feature_names, get_spec


def _cmd_create(args: argparse.Namespace) -> None:
    features = feature_names() if args.all else [args.feature]
    for feature in features:
        create_agent(get_spec(feature))


def _cmd_ask(args: argparse.Namespace) -> None:
    spec = get_spec(args.feature)
    print(f"[*] Asking {spec.agent_name}: {args.question!r}")
    answer = engine_ask(spec, args.question)
    print("\n=== Answer ===")
    print(answer)


def main() -> None:
    parser = argparse.ArgumentParser(prog="webiq-agent", description="WebIQ Foundry agents")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create or update a feature agent")
    create.add_argument(
        "feature", nargs="?", choices=feature_names(), help="Feature to create"
    )
    create.add_argument("--all", action="store_true", help="Create every feature agent")
    create.set_defaults(func=_cmd_create)

    ask = sub.add_parser("ask", help="Ask a feature agent a question")
    ask.add_argument("feature", choices=feature_names(), help="Feature agent to ask")
    ask.add_argument("question", help="Your question")
    ask.set_defaults(func=_cmd_ask)

    args = parser.parse_args()
    if args.command == "create" and not args.all and not args.feature:
        parser.error("create requires a feature (or --all)")
    args.func(args)


if __name__ == "__main__":
    main()
