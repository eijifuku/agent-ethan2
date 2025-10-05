"""Google Generative AI provider factory implementation."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedProvider

from .base import ProviderFactoryBase


class GoogleGenerativeAIProviderFactory(ProviderFactoryBase):
    """Create Google Generative AI clients from provider definitions."""

    error_code = "ERR_PROVIDER_GOOGLE"

    def build(self, provider: NormalizedProvider) -> Mapping[str, Any]:
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise GraphExecutionError(
                self.error_code,
                "Google provider requires the 'google-generativeai' package. Install it with 'pip install google-generativeai'.",
                pointer=self._pointer(provider),
            ) from exc

        api_key = self.require_config_value(
            provider,
            "api_key",
            env_var="GOOGLE_API_KEY",
            message=(
                "Google Generative AI API key is required. Set providers[].config.api_key or the GOOGLE_API_KEY environment variable."
            ),
        )
        model = self.get_config_value(
            provider,
            "model",
            env_var="GOOGLE_MODEL",
            default="gemini-pro",
        )

        genai.configure(api_key=str(api_key))

        temperature_value = self.get_config_value(provider, "temperature", env_var="GOOGLE_TEMPERATURE")
        top_p_value = self.get_config_value(provider, "top_p", env_var="GOOGLE_TOP_P")
        top_k_value = self.get_config_value(provider, "top_k", env_var="GOOGLE_TOP_K")
        max_output_tokens_value = self.get_config_value(
            provider,
            "max_output_tokens",
            env_var="GOOGLE_MAX_OUTPUT_TOKENS",
        )
        stop_sequences = provider.config.get("stop_sequences")

        generation_config: dict[str, Any] = {}
        temperature = self.coerce_float(provider, temperature_value, field="temperature")
        if temperature is not None:
            generation_config["temperature"] = temperature
        top_p = self.coerce_float(provider, top_p_value, field="top_p")
        if top_p is not None:
            generation_config["top_p"] = top_p
        top_k = self.coerce_int(provider, top_k_value, field="top_k")
        if top_k is not None:
            generation_config["top_k"] = top_k
        max_output_tokens = self.coerce_int(
            provider,
            max_output_tokens_value,
            field="max_output_tokens",
        )
        if max_output_tokens is not None:
            generation_config["max_output_tokens"] = max_output_tokens
        if isinstance(stop_sequences, (list, tuple)) and stop_sequences:
            generation_config["stop_sequences"] = list(stop_sequences)

        safety_settings = provider.config.get("safety_settings")
        system_instruction = provider.config.get("system_instruction")

        return {
            "client": genai,
            "model": str(model),
            "generation_config": generation_config or None,
            "safety_settings": safety_settings,
            "system_instruction": system_instruction,
            "config": dict(provider.config),
        }


def create_google_provider(provider: NormalizedProvider) -> Mapping[str, Any]:
    """Convenience wrapper aligning with resolver expectations."""

    return GoogleGenerativeAIProviderFactory()(provider)


__all__ = ["GoogleGenerativeAIProviderFactory", "create_google_provider"]
