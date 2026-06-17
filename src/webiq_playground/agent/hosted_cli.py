"""CLI for the hosted (server-side) WebIQ MCP agent: ``webiq-mcp-agent``.

    webiq-mcp-agent create             # create/update the hosted MCP agent
    webiq-mcp-agent ask "question..."  # ask it (Foundry runs the WebIQ MCP tools)

This is the single-call, server-side counterpart to ``webiq-agent`` (which runs WebIQ
client-side via a function-calling loop).
"""

from __future__ import annotations

import argparse

from webiq_playground.agent import hosted_mcp


def _cmd_create(args: argparse.Namespace) -> None:
    hosted_mcp.create_agent()


def _cmd_ask(args: argparse.Namespace) -> None:
    print(f"[*] Asking {hosted_mcp.HOSTED_AGENT_NAME}: {args.question!r}")
    answer = hosted_mcp.ask(args.question)
    print("\n=== Answer ===")
    print(answer)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="webiq-mcp-agent",
        description="Hosted (server-side) WebIQ MCP Foundry agent",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create or update the hosted MCP agent")
    create.set_defaults(func=_cmd_create)

    ask = sub.add_parser("ask", help="Ask the hosted MCP agent a question")
    ask.add_argument("question", help="Your question")
    ask.set_defaults(func=_cmd_ask)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
