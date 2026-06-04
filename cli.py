"""WebIQ Playground CLI.

Usage:
  uv run python cli.py web "tax filing deadline" --site sars.gov.za
  uv run python cli.py news "budget speech" --site sars.gov.za --max 10
  uv run python cli.py videos "how to register for efiling"
  uv run python cli.py images "sars logo"
"""

from __future__ import annotations

import argparse
import json
import sys

from client import WebIQClient, WebIQError
from web import search_web
from news import search_news
from videos import search_videos
from images import search_images

FEATURES = {
    "web": search_web,
    "news": search_news,
    "videos": search_videos,
    "images": search_images,
}

# Per-feature key holding the list of results in the JSON response.
RESULT_KEYS = {
    "web": "webResults",
    "news": "newsResults",
    "videos": "videoResults",
    "images": "imageResults",
}


def _print_results(feature: str, data: dict) -> None:
    print(f"[*] traceId: {data.get('traceId')}")
    key = RESULT_KEYS[feature]
    results = data.get(key) or []
    print(f"[*] {len(results)} result(s) in '{key}':")
    for i, r in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"Title: {r.get('title')}")
        print(f"URL:   {r.get('url')}")
        content = (r.get("content") or r.get("snippet") or "").strip().replace("\n", " ")
        if content:
            print(f"Text:  {content[:400]}{'...' if len(content) > 400 else ''}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Microsoft Web IQ playground CLI")
    parser.add_argument("feature", choices=FEATURES.keys(), help="Which Web IQ API to call")
    parser.add_argument("query", help="Search query text")
    parser.add_argument("--site", default=None, help="Restrict results to a domain, e.g. sars.gov.za")
    parser.add_argument("--max", type=int, default=5, dest="max_results", help="Max results (1-50)")
    parser.add_argument("--region", default="ZA", help="2-letter region code (default ZA)")
    parser.add_argument("--language", default="en", help="2-letter language code (default en)")
    parser.add_argument("--save", default="webiq_response.json", help="Where to dump the full JSON")
    args = parser.parse_args(argv)

    try:
        client = WebIQClient()
    except WebIQError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 2

    fn = FEATURES[args.feature]
    query = f"{args.query} site:{args.site}" if args.site else args.query
    print(f"[*] {args.feature} search: {query!r}")

    try:
        data = fn(
            client,
            args.query,
            site=args.site,
            max_results=args.max_results,
            language=args.language,
            region=args.region,
        )
    except WebIQError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1

    _print_results(args.feature, data)

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\n[*] Full response saved to {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
