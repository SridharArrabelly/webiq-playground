"""Generic engine shared by every WebIQ agent: create a version, and run the tool loop.

This is the *only* copy of the agent lifecycle code. Every feature in the registry is
created and invoked through these two functions, so fixes (auth, the date tag, the
function-calling loop) land in exactly one place.
"""

from __future__ import annotations

import json
import os
from datetime import date

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam

from webiq_playground.agent.registry import AgentSpec

load_dotenv()

MAX_TOOL_ROUNDS = 5


def _project_client() -> tuple[DefaultAzureCredential, AIProjectClient]:
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    credential = DefaultAzureCredential()
    return credential, AIProjectClient(endpoint=endpoint, credential=credential)


def create_agent(spec: AgentSpec) -> str:
    """Create (or add a new version of) the Foundry agent for ``spec``."""
    credential, project_client = _project_client()
    with credential, project_client:
        agent = project_client.agents.create_version(
            agent_name=spec.agent_name,
            definition=PromptAgentDefinition(
                model=os.environ["FOUNDRY_MODEL_NAME"],
                instructions=spec.instructions,
                tools=[spec.tool],
            ),
        )
        print(f"Agent ready: name={agent.name} version={agent.version} id={agent.id}")
        return agent.name


def ask(spec: AgentSpec, question: str) -> str:
    """Ask ``spec``'s agent a question, running the client-side tool loop."""
    agent_ref = {"agent_reference": {"name": spec.agent_name, "type": "agent_reference"}}
    dated_question = f"[Current date: {date.today().isoformat()}] {question}"

    credential, project_client = _project_client()
    with (
        credential,
        project_client,
        project_client.get_openai_client() as openai_client,
    ):
        response = openai_client.responses.create(input=dated_question, extra_body=agent_ref)

        for _ in range(MAX_TOOL_ROUNDS):
            tool_outputs: ResponseInputParam = []
            for item in response.output:
                if getattr(item, "type", None) == "function_call" and item.name == spec.tool_name:
                    args = json.loads(item.arguments)
                    print(
                        f"  -> {spec.tool_name}(query={args.get('query')!r}, "
                        f"site={args.get('site')!r})"
                    )
                    result = spec.executor(**args)
                    tool_outputs.append(
                        FunctionCallOutput(
                            type="function_call_output",
                            call_id=item.call_id,
                            output=result,
                        )
                    )
            if not tool_outputs:
                break
            response = openai_client.responses.create(
                input=tool_outputs,
                previous_response_id=response.id,
                extra_body=agent_ref,
            )

        return response.output_text
