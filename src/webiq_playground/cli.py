"""WebIQ Playground CLI (backed by the official webiq SDK).

Usage:
  uv run webiq web "tax filing deadline" --site sars.gov.za
  uv run webiq news "budget speech" --site sars.gov.za --max 10
  uv run webiq videos "how to register for efiling"
  uv run webiq images "sars logo"
"""

from __future__ import annotations

import argparse
import json

from .client import get_client
from .web import search_web
from .news import search_news
from .videos import search_videos
from .images import search_images

# feature -> (function, response attribute holding the result list)
FEATURES = {
    "web": (search_web, "webResults"),
    "news": (search_news, "newsResults"),
    "videos": (search_videos, "videoResults"),
    "images": (search_images, "imageResults"),
}


def _results(response, key):
    return getattr(response, key, None) or []


def _line(r):
    title = getattr(r, "title", None)
    url = getattr(r, "url", None)
    text = getattr(r, "content", None) or getattr(r, "snippet", None) or ""
    return title, url, str(text)


def _jsonable(response):
    for attr in ("model_dump", "to_dict", "dict"):
        fn = getattr(response, attr, None)
        if callable(fn):
            return fn()
    return response


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Microsoft Web IQ playground CLI")
    parser.add_argument("feature", choices=FEATURES.keys())
    parser.add_argument("query")
    parser.add_argument("--site", default=None, help="Restrict to a domain, e.g. sars.gov.za")
    parser.add_argument("--max", type=int, default=5, dest="max_results")
    parser.add_argument("--region", default="ZA")
    parser.add_argument("--language", default="en")
    parser.add_argument("--save", default="webiq_response.json")
    args = parser.parse_args(argv)

    fn, key = FEATURES[args.feature]
    scope = f" (site:{args.site})" if args.site else ""
    print(f"[*] {args.feature} search: {args.query!r}{scope}")

    with get_client() as client:
        response = fn(
            client,
            args.query,
            site=args.site,
            max_results=args.max_results,
            language=args.language,
            region=args.region,
        )

    results = _results(response, key)
    print(f"[*] {len(results)} result(s):")
    for i, r in enumerate(results, 1):
        title, url, text = _line(r)
        print(f"\n--- {i} ---")
        print(f"Title: {title}")
        print(f"URL:   {url}")
        if text:
            print(f"Text:  {text[:300]}{'...' if len(text) > 300 else ''}")

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(_jsonable(response), f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[*] Full response saved to {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
