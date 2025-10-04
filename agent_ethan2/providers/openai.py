"""OpenAI provider factory implementation."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedProvider

from .base import ProviderFactoryBase


class OpenAIProviderFactory(ProviderFactoryBase):
    """Create OpenAI clients from provider definitions."""

    error_code = "ERR_PROVIDER_OPENAI"

    def build(self, provider: NormalizedProvider) -> Mapping[str, Any]:
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on optional dependency
            raise GraphExecutionError(
                self.error_code,
                "OpenAI provider requires the 'openai' package. Install it with 'pip install openai'.",
                pointer=self._pointer(provider),
            ) from exc

        api_key = self.get_config_value(provider, "api_key", env_var="OPENAI_API_KEY")
        base_url = self.get_config_value(provider, "base_url", env_var="OPENAI_BASE_URL")
        organization = self.get_config_value(provider, "organization", env_var="OPENAI_ORGANIZATION")
        model = self.get_config_value(
            provider,
            "model",
            env_var="OPENAI_MODEL",
            default="gpt-4o-mini",
        )
        timeout_value = self.get_config_value(provider, "timeout", env_var="OPENAI_TIMEOUT")
        max_retries_value = self.get_config_value(provider, "max_retries", env_var="OPENAI_MAX_RETRIES")
        temperature_value = self.get_config_value(provider, "temperature", env_var="OPENAI_TEMPERATURE")

        normalized_base_url = base_url if base_url not in (None, "") else None
        normalized_org = organization if organization not in (None, "") else None
        normalized_api_key = api_key if api_key not in (None, "") else None

        if normalized_api_key is None and normalized_base_url is None:
            raise GraphExecutionError(
                self.error_code,
                "OpenAI API key is required. Set providers[].config.api_key or the OPENAI_API_KEY environment variable.",
                pointer=self._pointer(provider),
            )

        timeout = self.coerce_float(provider, timeout_value, field="timeout")
        max_retries = self.coerce_int(provider, max_retries_value, field="max_retries")
        temperature = self.coerce_float(provider, temperature_value, field="temperature")

        client_kwargs: dict[str, Any] = {}
        if normalized_api_key is not None:
            client_kwargs["api_key"] = str(normalized_api_key)
        if normalized_base_url is not None:
            client_kwargs["base_url"] = str(normalized_base_url)
        if normalized_org is not None:
            client_kwargs["organization"] = str(normalized_org)
        if timeout is not None:
            client_kwargs["timeout"] = timeout
        if max_retries is not None:
            client_kwargs["max_retries"] = max_retries

        client = OpenAI(**client_kwargs)

        return {
            "client": client,
            "model": str(model),
            "config": dict(provider.config),
            "base_url": normalized_base_url,
            "organization": normalized_org,
            "timeout": timeout,
            "max_retries": max_retries,
            "temperature": temperature,
        }


def create_openai_provider(provider: NormalizedProvider) -> Mapping[str, Any]:
    """Convenience function that matches the resolver import expectations."""

    return OpenAIProviderFactory()(provider)


__all__ = ["OpenAIProviderFactory", "create_openai_provider"]
