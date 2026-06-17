# WebIQ Playground

A small Python playground for the **Microsoft Web IQ** APIs — a suite of AI-native
search APIs that ground applications in fresh, real-world web content.

The same features (web, news, videos, images) are reachable through **interchangeable
backends**, so you can compare access methods without changing the CLI or the agent:

| Access method | Backend (`--backend`) | Transport                          | Status |
| ------------- | --------------------- | ---------------------------------- | ------ |
| SDK           | `sdk` (default)       | official [`webiq`](https://pypi.org/project/webiq/) SDK | ✅ |
| MCP           | `mcp`                 | WebIQ MCP server (Streamable HTTP) | ✅ |
| OpenAPI       | `openapi`             | WebIQ REST API directly (`httpx`)  | ✅ |

| Feature       | Status |
| ------------- | ------ |
| Web Search    | GA     |
| News Search   | Beta   |
| Videos Search | GA     |
| Images Search | Beta   |

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- A Web IQ **API key** (from the [portal](https://dashboard.microsoft.ai/)),
  or **Entra ID** (`DefaultAzureCredential`).

## Setup

```bash
uv sync                 # install runtime deps (webiq SDK)
uv sync --extra mcp     # add the MCP backend (official `mcp` SDK)
cp .env.example .env    # then edit .env and paste your key
```

`.env`:

```
WEBIQ_API_KEY=<your-api-key>
```

## Usage

Run any feature via the `webiq` command (installed by `uv sync`):

```bash
# Web search scoped to a single domain (SDK backend, the default)
uv run webiq web "what is retrieval augmented generation" --site learn.microsoft.com

# Same query via the MCP or OpenAPI backend
uv run webiq web "what is retrieval augmented generation" --backend mcp
uv run webiq web "what is retrieval augmented generation" --backend openapi

# News, videos, images
uv run webiq news "latest space exploration news" --max 10 --backend mcp
uv run webiq videos "how to make sourdough bread"
uv run webiq images "aurora borealis"
```

Common flags: `--backend {sdk,mcp,openapi}`, `--site <domain>`, `--max <n>` (1-50),
`--region US`, `--language en`, `--save out.json`. The full JSON response is written to
`webiq_response.json` by default. The backend can also be set with the `WEBIQ_BACKEND`
environment variable (default `sdk`).

Or use the package directly in Python — every backend returns the same normalized
`SearchResult`:

```python
from webiq_playground import get_backend

with get_backend("sdk") as backend:          # or "mcp" / "openapi"
    result = backend.search("web", "what is retrieval augmented generation", site="learn.microsoft.com")
    for item in result.items:
        print(item.title, item.url)
```

## Architecture

All three backends share one request/response contract, so the CLI, the agent and your
own code never depend on *how* WebIQ is reached:

- **One request shape.** The REST API, the MCP tools and the SDK all accept the *same*
  parameters. `core/params.py` (`wire_params`) builds that canonical request body once;
  the SDK backend simply translates it into the SDK's snake_case keyword arguments.
- **One response shape.** `core/models.py` (`normalize_payload`) maps every backend's raw
  payload into the same `SearchResult` / `SearchItem`.
- **Template method.** `SearchBackend.search()` in `backends/base.py` validates the
  feature, builds the parameters and normalizes the response. Each backend only implements
  `_run(feature, params)` — the transport-specific call that returns the raw payload.

```
search(feature, query, …)            ← base.py (shared: validate → wire_params → normalize)
        │
        └── _run(feature, params)     ← per backend (SDK call / MCP tool / REST POST)
```

This is why adding a backend or a feature is a tiny, localized change (see below).

## Backends

### SDK (`--backend sdk`)

Uses the official `webiq` SDK directly (`client.<feature>.search`). Installed with the
base `uv sync`.

### MCP (`--backend mcp`)

Talks to the **WebIQ MCP server** (`https://api.microsoft.ai/v3/mcp`, Streamable HTTP,
JSON-RPC 2.0) via the official [`mcp`](https://pypi.org/project/mcp/) SDK. Install with
`uv sync --extra mcp`. The endpoint can be overridden with `WEBIQ_MCP_ENDPOINT`.
Tools accept the same parameters as the REST API (camelCase) and are scoped to your
account's allow-list.

To wire the WebIQ MCP server directly into **Copilot CLI** instead, add it to
`%USERPROFILE%\.copilot\mcp-config.json`:

```json
{
  "mcpServers": {
    "webiq": {
      "type": "http",
      "url": "https://api.microsoft.ai/v3/mcp",
      "authtype": "api-key",
      "headers": { "x-apikey": "<your-api-key>" }
    }
  }
}
```

### OpenAPI (`--backend openapi`)

Calls the WebIQ **REST API** directly (`POST https://api.microsoft.ai/v3/search/{feature}`)
with `httpx` — no SDK or MCP layer. It follows the same OpenAPI-described request/response
contract as the SDK, and maps HTTP errors to the same `webiq.errors` types so failures
(rate limits, auth) surface uniformly. No extra install needed.

## Grounding agents (Foundry)

Optional agents use **gpt-4o** on Azure AI Foundry with a WebIQ search tool wired in as a
client-side function tool: the model calls e.g. `web_search`, we run a WebIQ backend, and
the model synthesizes a cited answer. The agent uses whichever backend `WEBIQ_BACKEND`
selects (default `sdk`).

There is **one agent per feature** (`web`, `news`, `videos`, `images`), all driven by the
same engine — adding a feature is a single entry in `agent/registry.py`.

```bash
uv sync --extra agent
az login                                            # auth uses DefaultAzureCredential

uv run webiq-agent create web                       # create/update one feature agent
uv run webiq-agent create --all                     # create/update every feature agent

uv run webiq-agent ask web "latest developments in AI, tech and robotics"
uv run webiq-agent ask news "latest news on quantum computing"
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

WebIQ auth is resolved automatically:

1. **API key** (default) — set `WEBIQ_API_KEY`.
2. **Entra ID** — leave `WEBIQ_API_KEY` unset and run `uv sync --extra entra`; all three
   backends fall back to `DefaultAzureCredential`
   (scope `https://api.microsoft.ai/.default`).

## Site scoping

The Web IQ APIs support the `site:` / `-site:` operators inside the `query` field.
The `--site` flag (and the `site=` argument) append `site:<domain>` for you.

## Project layout

```
webiq-playground/
├── src/
│   └── webiq_playground/
│       ├── __init__.py        # public API: get_backend, SearchResult, build_query, ...
│       ├── cli.py             # `webiq --backend sdk|mcp|openapi <feature> ...`
│       ├── core/
│       │   ├── config.py      # endpoints, region, scope, env access
│       │   ├── auth.py        # auth_headers() (x-apikey / Entra) for HTTP backends
│       │   ├── query.py       # build_query() (site: helper)
│       │   ├── params.py      # wire_params() — the shared request contract
│       │   └── models.py      # SearchItem / SearchResult / normalize_payload
│       ├── backends/
│       │   ├── base.py        # SearchBackend ABC (template-method search + _run), factory
│       │   ├── sdk/           # client.py (get_client) + backend.py (SdkBackend)
│       │   ├── mcp/           # session.py (auth) + backend.py (McpBackend)
│       │   └── openapi/       # backend.py (OpenApiBackend, REST over httpx)
│       └── agent/
│           ├── tools.py       # FunctionTool + run_<feature>_search (uses get_backend)
│           ├── registry.py    # AgentSpec per feature (the one place to add agents)
│           ├── engine.py      # generic create_agent() + ask() tool loop
│           └── cli.py         # `webiq-agent create|ask <feature>`
├── tests/
│   ├── test_core.py           # build_query, models, normalize_payload
│   ├── test_params.py         # wire_params (the shared request contract)
│   ├── test_backends.py       # get_backend() factory (backend selection)
│   ├── test_sdk.py            # SDK backend (offline, faked SDK client)
│   ├── test_mcp.py            # MCP backend result parsing / search wiring (offline)
│   ├── test_openapi.py        # OpenAPI backend search/normalize/error mapping (offline)
│   └── test_agent.py          # tools, registry, engine tool loop
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
├── LICENSE
└── README.md
```

### Adding a new backend

1. Create `backends/<name>/backend.py` with a `SearchBackend` subclass that implements
   `_run(feature, params)` — make the transport call and return the raw WebIQ payload.
   (`params` is the camelCase body from `wire_params`; validation and normalization are
   handled by the base `search()`.)
2. Register it in `get_backend()` (and add the name to `BACKENDS`) in `backends/base.py`.

### Adding a new feature agent

1. In `agent/tools.py`, add a `*_SEARCH_TOOL = make_search_tool(...)` and a
   `run_<feature>_search` executor (one line via `_search_to_json`).
2. Add one `AgentSpec` entry to `AGENTS` in `agent/registry.py`.

The CLI, create/ask flow, date handling and tool loop work automatically — no new
boilerplate.

## Support

Web IQ technical issues / feedback: WebIQ-Support@microsoft.com

## Reference documentation

- [Web IQ portal](https://aka.ms/webiq-portal) — overview, onboarding and access requests
- [Web IQ documentation](https://webiq.microsoft.ai/documentation) — full developer docs
  - [Authentication](https://webiq.microsoft.ai/documentation/authentication) — API key & Entra ID setup
  - [REST API reference](https://webiq.microsoft.ai/documentation/api-reference/web) — endpoints, parameters, responses, error codes (used by the OpenAPI backend)
  - [MCP server](https://webiq.microsoft.ai/documentation/mcp) — MCP endpoint, tools and configuration (used by the MCP backend)
- [`webiq` Python SDK](https://pypi.org/project/webiq/) — the official SDK (used by the SDK backend)
- [`mcp` Python SDK](https://pypi.org/project/mcp/) — the official Model Context Protocol SDK
- [Model Context Protocol](https://modelcontextprotocol.io/) — the open MCP standard
- [Azure AI Foundry Agents](https://learn.microsoft.com/azure/ai-foundry/agents/) — the grounding-agent runtime
- [`azure-identity` (`DefaultAzureCredential`)](https://learn.microsoft.com/python/api/overview/azure/identity-readme) — Entra ID authentication
- [uv](https://docs.astral.sh/uv/) — the Python package & project manager used here
- Request access: [Web IQ waitlist](https://aka.ms/webiq-waitlist)

## License

Released under the [MIT License](LICENSE).

This is an unofficial sample/playground for exploring the Microsoft Web IQ APIs and is not
an official Microsoft product. "Microsoft", "Web IQ", "Azure" and related names are
trademarks of Microsoft Corporation. Your use of the Web IQ service is governed by the
terms you accepted with Microsoft, not by this repository's license.

