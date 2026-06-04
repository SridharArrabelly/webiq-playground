"""Foundry grounding agents for WebIQ (web, news, videos, images): gpt-4o + function tools."""

from webiq_playground.agent.registry import AGENTS, AgentSpec, feature_names, get_spec

__all__ = ["AGENTS", "AgentSpec", "feature_names", "get_spec"]
