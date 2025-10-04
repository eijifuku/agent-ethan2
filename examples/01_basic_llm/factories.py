"""Factory helpers for the basic LLM example."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from openai import OpenAI

from agent_ethan2.ir import NormalizedComponent


def component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create an async callable that invokes OpenAI Responses API."""

    client: OpenAI = provider_instance["client"]
    model: str = provider_instance["model"]
    temperature = component.config.get("temperature", 0.2)
    max_output_tokens = component.config.get("max_output_tokens", 256)

    async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        prompt = inputs.get("prompt", "")
        loop = asyncio.get_running_loop()

        def _invoke() -> Mapping[str, Any]:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=float(temperature),
                max_tokens=int(max_output_tokens),
            )
            usage = response.usage
            usage_dict = usage.model_dump() if hasattr(usage, "model_dump") else {}
            text = response.choices[0].message.content if response.choices else ""
            return {
                "choices": [
                    {"text": text}
                ],
                "usage": usage_dict,
            }

        return await loop.run_in_executor(None, _invoke)

    return call
