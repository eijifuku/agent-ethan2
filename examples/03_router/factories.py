"""Factories for Example 03."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping

from openai import OpenAI

from agent_ethan2.ir import NormalizedComponent



def llm_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create an async callable that invokes OpenAI Chat API."""
    
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


def router_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create a router component that classifies input and returns a route."""
    
    async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Classify the user input and return routing decision.
        
        Expected inputs:
            user_input: str - the user's message
        
        Returns:
            route: str - one of "greeting", "question", "calculation", "other"
        """
        user_input = inputs.get("user_input", "").lower()
        
        # Simple keyword-based routing
        if any(word in user_input for word in ["hello", "hi", "hey", "good morning", "good evening"]):
            route = "greeting"
        elif any(word in user_input for word in ["?", "what", "how", "why", "when", "where", "who"]):
            route = "question"
        elif any(word in user_input for word in ["calculate", "compute", "+", "-", "*", "/", "add", "subtract", "multiply", "divide"]):
            route = "calculation"
        else:
            route = "other"
        
        return {
            "route": route,
            "input": user_input,
        }
    
    return call

