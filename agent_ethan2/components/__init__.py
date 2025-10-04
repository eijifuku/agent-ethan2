"""Default component factories bundled with AgentEthan2."""

from __future__ import annotations

from typing import Mapping

DEFAULT_COMPONENT_FACTORIES: Mapping[str, str] = {
    "llm": "agent_ethan2.components.llm.create_openai_chat_component",
    "openai_chat": "agent_ethan2.components.llm.create_openai_chat_component",
    "anthropic_messages": "agent_ethan2.components.llm.create_anthropic_messages_component",
    "tool": "agent_ethan2.components.tool.create_tool_passthrough_component",
}

__all__ = ["DEFAULT_COMPONENT_FACTORIES"]
