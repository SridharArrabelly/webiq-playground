"""Registry of WebIQ Foundry agents.

Adding a new feature agent is a single entry here: a name, a tool, an executor and
an instruction blurb. The generic engine (``engine.py``) and CLI (``cli.py``) drive
every entry the same way, so there is no per-feature boilerplate to copy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from azure.ai.projects.models import FunctionTool

from webiq_playground.agent import tools

# Shared preamble: gives the model a clock and grounding rules.
_PREAMBLE = (
    "You are WebIQ, a research assistant. The user's message begins with the current date "
    "in a [Current date: YYYY-MM-DD] tag; treat that as today and resolve relative time "
    "references such as 'this year', 'today', or 'latest' against it (do NOT rely on your "
    "training data for the current year). "
)
_GROUNDING = (
    " Base your answer ONLY on the returned sources, write a concise synthesized answer, "
    "and cite the source URLs you used. If the sources do not answer the question, say so "
    "plainly."
)


def _instructions(tool_name: str, what: str) -> str:
    return (
        f"{_PREAMBLE}When a question needs {what}, call the {tool_name} tool (optionally "
        "scoping it to a site such as wikipedia.org) and put the resolved year in the query."
        f"{_GROUNDING}"
    )


def _agent_name(feature: str) -> str:
    """Foundry agent name, overridable per feature via env (e.g. FOUNDRY_AGENT_NAME_WEB)."""
    return os.environ.get(f"FOUNDRY_AGENT_NAME_{feature.upper()}") or f"webiq-{feature}-agent"


@dataclass(frozen=True)
class AgentSpec:
    feature: str
    agent_name: str
    tool_name: str
    instructions: str
    tool: FunctionTool
    executor: Callable[..., str]


def _spec(feature: str, tool: FunctionTool, executor: Callable[..., str], what: str) -> AgentSpec:
    return AgentSpec(
        feature=feature,
        agent_name=_agent_name(feature),
        tool_name=tool.name,
        instructions=_instructions(tool.name, what),
        tool=tool,
        executor=executor,
    )


AGENTS: dict[str, AgentSpec] = {
    "web": _spec(
        "web",
        tools.WEB_SEARCH_TOOL,
        tools.run_web_search,
        "current, factual, or web-sourced information",
    ),
    "news": _spec(
        "news",
        tools.NEWS_SEARCH_TOOL,
        tools.run_news_search,
        "recent news or coverage of current events",
    ),
    "videos": _spec(
        "videos",
        tools.VIDEO_SEARCH_TOOL,
        tools.run_video_search,
        "videos or visual demonstrations",
    ),
    "images": _spec(
        "images",
        tools.IMAGE_SEARCH_TOOL,
        tools.run_image_search,
        "images or pictures",
    ),
}


def feature_names() -> list[str]:
    return list(AGENTS)


def get_spec(feature: str) -> AgentSpec:
    try:
        return AGENTS[feature]
    except KeyError:
        raise KeyError(f"Unknown feature {feature!r}; choose from {feature_names()}") from None
