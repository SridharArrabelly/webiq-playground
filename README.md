# WebIQ Playground

A small Python playground for the **Microsoft Web IQ** APIs — a suite of AI-native
search APIs that ground applications in fresh, real-world web content.

It is built on the official [`webiq`](https://pypi.org/project/webiq/) SDK, with a thin
wrapper per feature so the project can grow over time, plus an optional **Foundry
grounding agent** (gpt-4o) that answers questions using WebIQ web search as a tool.

| Feature       | Module      | SDK call                | Status |
| ------------- | ----------- | ----------------------- | ------ |
| Web Search    | `web.py`    | `client.web.search`     | GA     |
| News Search   | `news.py`   | `client.news.search`    | Beta   |
| Videos Search | `videos.py` | `client.videos.search`  | GA     |
| Images Search | `images.py` | `client.images.search`  | Beta   |

`client.py` builds the SDK client (`get_client`) and holds the `site:` helper; `cli.py`
is a thin command-line front end. The Foundry agent lives under `agent/`.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Web IQ **API key** (from the [portal](https://dashboard.microsoft.ai/)),
  or **Entra ID** (`DefaultAzureCredential`).

## Setup

```bash
uv sync                 # install runtime deps (webiq SDK)
cp .env.example .env    # then edit .env and paste your key
```

`.env`:

```
WEBIQ_API_KEY=<your-api-key>
```

## Usage

Run any feature via the `webiq` command (installed by `uv sync`):

```bash
# Web search scoped to a single domain
uv run webiq web "tax filing deadline" --site sars.gov.za

# News, videos, images
uv run webiq news "budget speech" --site sars.gov.za --max 10
uv run webiq videos "how to register for efiling"
uv run webiq images "sars logo"
```

Common flags: `--site <domain>`, `--max <n>` (1-50), `--region ZA`, `--language en`,
`--save out.json`. The full JSON response is written to `webiq_response.json` by default.

Or use the package directly in Python:

```python
from webiq_playground import get_client, search_web

with get_client() as client:                  # reads WEBIQ_API_KEY from .env
    response = search_web(client, "tax filing deadline", site="sars.gov.za")
    for r in response.webResults or []:
        print(r.title, r.url)
```

## Grounding agents (Foundry)

Optional agents use **gpt-4o** on Azure AI Foundry with a WebIQ search tool wired in as a
client-side function tool: the model calls e.g. `web_search`, we run the WebIQ SDK, and the
model synthesizes a cited answer.

There is **one agent per feature** (`web`, `news`, `videos`, `images`), all driven by the
same engine — adding a feature is a single entry in `agent/registry.py`.

```bash
uv sync --extra agent
az login                                            # auth uses DefaultAzureCredential

uv run webiq-agent create web                       # create/update one feature agent
uv run webiq-agent create --all                     # create/update every feature agent

uv run webiq-agent ask web "What is the SARS tax filing deadline this year?"
uv run webiq-agent ask news "latest SARS media releases"
```

Each query begins with a `[Current date: YYYY-MM-DD]` tag the agent injects, so the model
resolves "this year" / "latest" against today rather than its training data.

Requires in `.env`:

```
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL_NAME=gpt-4o
```

Agent names default to `webiq-<feature>-agent` and can be overridden per feature with
`FOUNDRY_AGENT_NAME_<FEATURE>` (e.g. `FOUNDRY_AGENT_NAME_WEB`).

## Authentication

WebIQ auth is resolved automatically by `get_client()`:

1. **API key** (default) — set `WEBIQ_API_KEY`.
2. **Entra ID** — leave `WEBIQ_API_KEY` unset and run `uv sync --extra entra`; the SDK
   uses `DefaultAzureCredential`.

## Site scoping

The Web IQ APIs support the `site:` / `-site:` operators inside the `query` field.
The `--site` flag (and the `site=` argument) append `site:<domain>` for you.

## Project layout

```
webiq-playground/
├── src/
│   └── webiq_playground/
│       ├── __init__.py   # re-exports the public API
│       ├── client.py     # get_client() (api key / Entra) + build_query()
│       ├── web.py        # web search   (webiq SDK)
│       ├── news.py       # news search  (beta)
│       ├── videos.py     # videos search
│       ├── images.py     # images search (beta)
│       ├── cli.py        # `webiq` search CLI
│       └── agent/
│           ├── tools.py        # FunctionTool + run_<feature>_search executors
│           ├── registry.py     # AgentSpec per feature (the one place to add agents)
│           ├── engine.py       # generic create_agent() + ask() tool loop
│           ├── cli.py          # `webiq-agent create|ask <feature>`
│           ├── create_agent.py # back-compat shim
│           └── run_agent.py    # back-compat shim
├── tests/
│   ├── test_smoke.py       # offline tests (no network)
│   └── test_agent_tool.py  # tool serialization + registry
├── .env.example
└── pyproject.toml
```

### Adding a new feature agent

1. Add a search wrapper module if it doesn't exist (e.g. `videos.py`).
2. In `agent/tools.py`, add a `*_SEARCH_TOOL = make_search_tool(...)` and a
   `run_<feature>_search` executor (one line via `_search_to_json`).
3. Add one `AgentSpec` entry to `AGENTS` in `agent/registry.py`.

The CLI, create/ask flow, date handling and tool loop work automatically — no new
boilerplate.

## Support

Web IQ technical issues / feedback: WebIQ-Support@microsoft.com
