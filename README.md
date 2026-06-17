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

The CLI, the agent and your own code all call one method — `backend.search(...)` — and get
back one shape — `SearchResult` — no matter which backend runs. Each backend differs only
in the one step that actually talks to WebIQ.

```
caller (CLI / agent / your code)
   │   backend.search("web", "your query", site=…, max_results=…)
   ▼
SearchBackend.search()                         ← base.py, shared by every backend
   1. validate the feature (web / news / videos / images)
   2. build_query()    → append the `site:` operator        (core/query.py)
   3. wire_params()    → canonical request body (camelCase)  (core/params.py)
   4. _run(feature, params)  ─── the ONLY per-backend step ───┐
   5. normalize_payload() → SearchResult / SearchItem  (core/models.py)
   │                                                          │
   ▼                                                          ▼
SearchResult (same shape every time)            SDK      → client.<feature>.search(**kwargs)
                                                MCP      → call the MCP tool (JSON-RPC)
                                                OpenAPI  → POST /search/{feature} (httpx)
```

Why it's built this way:

- **One request shape.** The REST API, the MCP tools and the SDK all accept the *same*
  parameters, so `wire_params()` builds the request body once. The SDK backend just renames
  those keys to the SDK's snake_case keyword arguments.
- **One response shape.** `normalize_payload()` folds every backend's raw payload into the
  same `SearchResult` / `SearchItem`, so callers never touch backend-specific JSON.
- **One place to extend.** Because `search()` owns validation, query building and
  normalization, a new backend only implements `_run()` — see
  [Adding a new backend](#adding-a-new-backend).

> The hosted MCP agent (`webiq-mcp-agent`) is the one exception: WebIQ runs inside Foundry,
> so it does not go through `backend.search()` at all.

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

Optional agents run on Azure AI Foundry and answer questions with cited, WebIQ-grounded
results. There are **two flavors** that differ only in *where* WebIQ runs:

|                       | `webiq-agent` (function-tool)        | `webiq-mcp-agent` (hosted MCP)        |
| --------------------- | ------------------------------------ | ------------------------------------- |
| WebIQ tool            | client-side `FunctionTool`           | Foundry-hosted `MCPTool`              |
| Who calls WebIQ       | **us** (a local backend)             | **Foundry** (server-side)             |
| Round trips per ask   | 2× Foundry + 1× WebIQ (loops)        | **1× Foundry** (it runs the tool)     |
| Coverage              | one agent **per feature**            | **one agent**, model picks the tool   |
| WebIQ auth            | the active backend (key / Entra)     | stored in the Foundry MCP connection  |

Both inject a `[Current date: YYYY-MM-DD]` tag so the model resolves "this year" / "latest"
against today rather than its training data. Shared `.env`:

```
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL_NAME=gpt-4o
```

```bash
uv sync
az login                                            # auth uses DefaultAzureCredential
```

### `webiq-agent` — client-side function tool

The model calls e.g. `web_search`, we run a WebIQ backend locally, and the model
synthesizes a cited answer. It uses whichever backend `WEBIQ_BACKEND` selects (default
`sdk`). There is **one agent per feature** (`web`, `news`, `videos`, `images`), all driven
by the same engine — adding a feature is a single entry in `agent/registry.py`.

```bash
uv run webiq-agent create web                       # create/update one feature agent
uv run webiq-agent create --all                     # create/update every feature agent

uv run webiq-agent ask web "latest developments in AI, tech and robotics"
uv run webiq-agent ask news "latest news on quantum computing"
```

Agent names default to `webiq-<feature>-agent` and can be overridden per feature with
`FOUNDRY_AGENT_NAME_<FEATURE>` (e.g. `FOUNDRY_AGENT_NAME_WEB`).

### `webiq-mcp-agent` — hosted MCP tool

A single agent attaches WebIQ as a **Foundry-hosted MCP tool**, so Foundry calls the WebIQ
MCP server itself — one round trip from our side, no client-side loop, and the WebIQ
credential lives in the Foundry connection (not in this repo). First register the WebIQ MCP
server in the portal (**Tools → MCP**): server URL `https://api.microsoft.ai/v3/mcp`,
key-based auth with header name **`x-apikey`**. Then point `.env` at that connection:

```
WEBIQ_MCP_CONNECTION_ID=WebIQ-MCP                    # connection name, or its full resource id
```

```bash
uv run webiq-mcp-agent create                       # create/update the hosted MCP agent
uv run webiq-mcp-agent ask "latest news on quantum computing"
uv run webiq-mcp-agent ask "short videos on sourdough bread"
```

The hosted agent name defaults to `webiq-mcp-agent` (override with `FOUNDRY_MCP_AGENT_NAME`)
and exposes the WebIQ `web`, `news`, `videos`, `images` and `browse` tools.

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
│           ├── cli.py         # `webiq-agent create|ask <feature>`
│           ├── hosted_mcp.py  # hosted MCP agent: build_tool/create_agent/ask (server-side)
│           └── hosted_cli.py  # `webiq-mcp-agent create|ask`
├── tests/
│   ├── test_core.py           # build_query, models, normalize_payload
│   ├── test_params.py         # wire_params (the shared request contract)
│   ├── test_backends.py       # get_backend() factory (backend selection)
│   ├── test_sdk.py            # SDK backend (offline, faked SDK client)
│   ├── test_mcp.py            # MCP backend result parsing / search wiring (offline)
│   ├── test_openapi.py        # OpenAPI backend search/normalize/error mapping (offline)
│   ├── test_agent.py          # tools, registry, engine tool loop
│   └── test_hosted_mcp.py     # hosted MCP agent (tool wiring + ask, offline)
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

