"""Hosted (server-side) WebIQ MCP agent for Foundry.

Unlike the per-feature agents in ``engine.py`` -- which run WebIQ *client-side* via a
function-calling loop -- this agent attaches a single Foundry-hosted MCP tool that points
at the ``WebIQ-MCP`` project connection. Foundry calls the WebIQ MCP server itself, so one
``ask`` is a single round trip from our side: no local executor, no tool loop. The WebIQ
credential lives in the Foundry connection, not in this code.
"""

from __future__ import annotations

import os
from datetime import date

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import MCPTool, PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

from webiq_playground.core.config import MCP_ENDPOINT

load_dotenv()

# Foundry agent name (overridable via env) and the WebIQ tools the hosted server exposes.
HOSTED_AGENT_NAME = os.environ.get("FOUNDRY_MCP_AGENT_NAME", "webiq-mcp-agent")
WEBIQ_MCP_SERVER_LABEL = "WebIQ-MCP"
WEBIQ_MCP_TOOLS = ["web", "news", "videos", "images", "browse"]

INSTRUCTIONS = (
    "You are WebIQ, a research assistant. The user's message begins with the current date "
    "in a [Current date: YYYY-MM-DD] tag; treat that as today and resolve relative time "
    "references such as 'this year', 'today', or 'latest' against it (do NOT rely on your "
    "training data for the current year). When a question needs current, factual, or "
    "media information, call the WebIQ MCP tools (web, news, videos, images, browse) to "
    "ground your answer in live results. Base your answer ONLY on the returned sources, "
    "write a concise synthesized answer, and cite the source URLs you used. If the sources "
    "do not answer the question, say so plainly."
)


def _connection_id() -> str:
    """The project connection that stores the WebIQ MCP server's auth."""
    try:
        return os.environ["WEBIQ_MCP_CONNECTION_ID"]
    except KeyError:
        raise KeyError(
            "WEBIQ_MCP_CONNECTION_ID is not set. Point it at your WebIQ MCP connection in "
            "Foundry (the connection name, e.g. 'WebIQ-MCP', or its full resource id)."
        ) from None


def build_tool() -> MCPTool:
    """Build the hosted MCP tool bound to the WebIQ-MCP Foundry connection.

    ``server_url`` is the WebIQ MCP endpoint Foundry calls; ``project_connection_id`` is the
    Foundry connection that supplies the auth (the ``x-apikey`` header). Foundry requires the
    endpoint to be present on the tool, so both are set.
    """
    return MCPTool(
        type="mcp",
        server_label=WEBIQ_MCP_SERVER_LABEL,
        server_url=MCP_ENDPOINT,
        project_connection_id=_connection_id(),
        require_approval="never",
        allowed_tools=list(WEBIQ_MCP_TOOLS),
    )


def _project_client() -> tuple[DefaultAzureCredential, AIProjectClient]:
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    return credential, AIProjectClient(endpoint=endpoint, credential=credential)


def create_agent() -> str:
    """Create (or add a new version of) the hosted WebIQ MCP agent."""
    credential, project_client = _project_client()
    with credential, project_client:
        agent = project_client.agents.create_version(
            agent_name=HOSTED_AGENT_NAME,
            definition=PromptAgentDefinition(
                model=os.environ["FOUNDRY_MODEL_NAME"],
                instructions=INSTRUCTIONS,
                tools=[build_tool()],
            ),
        )
        print(f"Agent ready: name={agent.name} version={agent.version} id={agent.id}")
        return agent.name


def ask(question: str) -> str:
    """Ask the hosted WebIQ MCP agent; Foundry runs the tool, so there is no client loop."""
    agent_ref = {"agent_reference": {"name": HOSTED_AGENT_NAME, "type": "agent_reference"}}
    dated_question = f"[Current date: {date.today().isoformat()}] {question}"

    credential, project_client = _project_client()
    with (
        credential,
        project_client,
        project_client.get_openai_client() as openai_client,
    ):
        response = openai_client.responses.create(input=dated_question, extra_body=agent_ref)
        return response.output_text
