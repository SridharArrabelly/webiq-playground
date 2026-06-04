# WebIQ Playground

A small Python playground for the **Microsoft Web IQ** APIs — a suite of AI-native
search APIs that ground applications in fresh, real-world web content.

Each Web IQ feature lives in its own module so the project can grow over time:

| Feature       | Module      | Endpoint                       | Status |
| ------------- | ----------- | ------------------------------ | ------ |
| Web Search    | `web.py`    | `POST /v3/search/web`          | GA     |
| News Search   | `news.py`   | `POST /v3/search/news`         | Beta   |
| Videos Search | `videos.py` | `POST /v3/search/videos`       | GA     |
| Images Search | `images.py` | `POST /v3/search/images`       | Beta   |

Shared HTTP + auth lives in `client.py`, and `cli.py` is a thin command-line front end.

Base URL: `https://api.microsoft.ai/v3`

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Web IQ **API key** (from the [portal Profile Management](https://dashboard.microsoft.ai/) page),
  or an **Entra ID** app registration bound to your Web IQ profile.

## Setup

```bash
uv sync                 # install runtime deps
cp .env.example .env    # then edit .env and paste your key
```

`.env`:

```
WEBIQ_API_KEY=<your-api-key>
```

## Usage

Run any feature via the CLI:

```bash
# Web search scoped to a single domain
uv run python cli.py web "tax filing deadline" --site sars.gov.za

# News, videos, images
uv run python cli.py news "budget speech" --site sars.gov.za --max 10
uv run python cli.py videos "how to register for efiling"
uv run python cli.py images "sars logo"
```

Common flags: `--site <domain>`, `--max <n>` (1-50), `--region ZA`, `--language en`,
`--save out.json`. The full JSON response is written to `webiq_response.json` by default.

Or use the modules directly in Python:

```python
from client import WebIQClient
from web import search_web

client = WebIQClient()                       # reads WEBIQ_API_KEY from .env
data = search_web(client, "tax filing deadline", site="sars.gov.za")
for r in data["webResults"]:
    print(r["title"], r["url"])
```

A minimal end-to-end example also lives in `test_webiq.py`.

## Authentication

Two options, resolved automatically by `WebIQClient`:

1. **API key** (default) — set `WEBIQ_API_KEY`; sent as the `x-apikey` header.
2. **Entra ID** — set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`
   and install the extra: `uv sync --extra entra`. The client requests an app-only
   token (scope `https://api.microsoft.ai/.default`) and sends it as a bearer token.

> Your Entra ID app must be bound to your Web IQ profile in the portal before tokens
> are accepted.

## Site scoping

The Web IQ APIs support the `site:` / `-site:` operators inside the `query` field.
The `--site` flag (and the `site=` argument) append `site:<domain>` for you.

## Project layout

```
webiq-playground/
├── client.py   # WebIQClient: shared POST + auth (api key / Entra ID)
├── web.py      # web search
├── news.py     # news search (beta)
├── videos.py   # videos search
├── images.py   # images search (beta)
├── cli.py      # command-line dispatcher
├── test_webiq.py  # minimal example
├── .env.example
└── pyproject.toml
```

## Support

Web IQ technical issues / feedback: WebIQ-Support@microsoft.com
