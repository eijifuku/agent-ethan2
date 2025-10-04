"""Anthropic provider factory implementation."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedProvider

from .base import ProviderFactoryBase


class AnthropicProviderFactory(ProviderFactoryBase):
    """Create Anthropic clients from provider definitions."""

    error_code = "ERR_PROVIDER_ANTHROPIC"

    def build(self, provider: NormalizedProvider) -> Mapping[str, Any]:
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover - depends on optional dependency
            raise GraphExecutionError(
                self.error_code,
                "Anthropic provider requires the 'anthropic' package. Install it with 'pip install anthropic'.",
                pointer=self._pointer(provider),
            ) from exc

        api_key = self.require_config_value(
            provider,
            "api_key",
            env_var="ANTHROPIC_API_KEY",
            message="Anthropic API key is required. Set providers[].config.api_key or the ANTHROPIC_API_KEY environment variable.",
        )
        model = self.get_config_value(
            provider,
            "model",
            env_var="ANTHROPIC_MODEL",
            default="claude-3-5-sonnet-latest",
        )
        max_tokens_value = self.get_config_value(provider, "max_tokens", env_var="ANTHROPIC_MAX_TOKENS")
        temperature_value = self.get_config_value(provider, "temperature", env_var="ANTHROPIC_TEMPERATURE")

        max_tokens = self.coerce_int(provider, max_tokens_value, field="max_tokens")
        temperature = self.coerce_float(provider, temperature_value, field="temperature")

        client_kwargs: dict[str, Any] = {"api_key": str(api_key)}
        client = Anthropic(**client_kwargs)

        return {
            "client": client,
            "model": str(model),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "config": dict(provider.config),
        }


def create_anthropic_provider(provider: NormalizedProvider) -> Mapping[str, Any]:
    """Convenience function that matches the resolver import expectations."""

    return AnthropicProviderFactory()(provider)


__all__ = ["AnthropicProviderFactory", "create_anthropic_provider"]
