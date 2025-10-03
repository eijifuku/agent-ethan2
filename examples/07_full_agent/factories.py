"""Factories for Example 07."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Mapping

from openai import OpenAI

from agent_ethan2.ir import NormalizedComponent, NormalizedProvider


def provider_factory(provider: NormalizedProvider) -> Mapping[str, Any]:
    """Create OpenAI provider instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    model = provider.config.get("model", "gpt-4o-mini")
    
    return {"client": client, "model": model, "config": dict(provider.config)}


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


def tool_factory(tool: Any, provider_instance: Mapping[str, Any]) -> Any:
    """Create a tool instance by importing the function from the config."""
    import importlib
    
    tool_type = tool.type
    
    # Map tool types to their factory functions
    if tool_type == "search":
        module = importlib.import_module("examples.07_full_agent.components.tools")
        return getattr(module, "web_search_tool")
    elif tool_type == "calculator":
        module = importlib.import_module("examples.07_full_agent.components.tools")
        return getattr(module, "calculator_tool")
    elif tool_type == "validator":
        module = importlib.import_module("examples.07_full_agent.components.tools")
        return getattr(module, "data_validator")
    else:
        raise ValueError(f"Unknown tool type: {tool_type}")


def tool_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Wrap tool instance as a component."""
    return tool_instance


def custom_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """
    Create a custom component by importing the function from the config.
    
    Expected component config:
        function: str - Python import path to the async function
    """
    function_path = component.config.get("function")
    if not function_path:
        raise ValueError(f"Custom component '{component.id}' missing 'function' in config")
    
    # Import the function dynamically
    module_path, function_name = function_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    func = getattr(module, function_name)
    
    return func


def router_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """
    Create a router component by importing the classifier function from the config.
    
    Expected component config:
        function: str - Python import path to the async function
    """
    function_path = component.config.get("function")
    if not function_path:
        raise ValueError(f"Router component '{component.id}' missing 'function' in config")
    
    # Import the function dynamically
    module_path, function_name = function_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    func = getattr(module, function_name)
    
    return func

