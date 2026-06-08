"""WebIQ Playground CLI — backend-agnostic (SDK or MCP).

Usage:
  uv run webiq web "tax filing deadline" --site sars.gov.za
  uv run webiq news "budget speech" --max 10 --backend mcp
  uv run webiq videos "how to register for efiling"
  uv run webiq images "sars logo"
"""

from __future__ import annotations

import argparse
import json

from .backends.base import BACKENDS, DEFAULT_BACKEND, FEATURES, get_backend
from .core.config import DEFAULT_REGION

try:  # SDK is a base dependency, but stay defensive for MCP-only installs.
    from webiq.errors import WebIQError
except ImportError:  # pragma: no cover
    WebIQError = Exception


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Microsoft Web IQ playground CLI")
    parser.add_argument("feature", choices=FEATURES)
    parser.add_argument("query")
    parser.add_argument("--site", default=None, help="Restrict to a domain, e.g. sars.gov.za")
    parser.add_argument("--max", type=int, default=5, dest="max_results")
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--language", default="en")
    parser.add_argument(
        "--backend",
        choices=BACKENDS,
        default=None,
        help=f"Access method (default: $WEBIQ_BACKEND or {DEFAULT_BACKEND})",
    )
    parser.add_argument("--save", default="webiq_response.json")
    args = parser.parse_args(argv)

    scope = f" (site:{args.site})" if args.site else ""
    backend = get_backend(args.backend)
    print(f"[*] {args.feature} search via {backend.name}: {args.query!r}{scope}")

    with backend:
        try:
            result = backend.search(
                args.feature,
                args.query,
                site=args.site,
                max_results=args.max_results,
                language=args.language,
                region=args.region,
            )
        except WebIQError as exc:
            print(f"[!] WebIQ request failed: {exc}")
            return 1

    print(f"[*] {len(result.items)} result(s):")
    for i, item in enumerate(result.items, 1):
        print(f"\n--- {i} ---")
        print(f"Title: {item.title}")
        print(f"URL:   {item.url}")
        if item.content:
            text = str(item.content)
            print(f"Text:  {text[:300]}{'...' if len(text) > 300 else ''}")

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        print(f"\n[*] Full response saved to {args.save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
