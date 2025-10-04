"""Default provider factories bundled with AgentEthan2."""

from __future__ import annotations

from typing import Mapping

DEFAULT_PROVIDER_FACTORIES: Mapping[str, str] = {
    "openai": "agent_ethan2.providers.openai.create_openai_provider",
    "anthropic": "agent_ethan2.providers.anthropic.create_anthropic_provider",
}

__all__ = ["DEFAULT_PROVIDER_FACTORIES"]
