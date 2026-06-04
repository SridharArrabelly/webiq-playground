"""Minimal example: a web search scoped to sars.gov.za.

Run:
  uv run python test_webiq.py
"""

from webiq_playground import WebIQClient, search_web


def main() -> None:
    client = WebIQClient()
    data = search_web(client, "tax filing deadline", site="sars.gov.za", max_results=5)
    print(f"traceId: {data.get('traceId')}")
    for i, r in enumerate(data.get("webResults", []), 1):
        print(f"{i}. {r.get('title')} -> {r.get('url')}")


if __name__ == "__main__":
    main()
