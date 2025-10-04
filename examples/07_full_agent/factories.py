"""Factories for Example 07."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.ir import NormalizedComponent


def tool_factory(tool: Any, provider_instance: Mapping[str, Any]) -> Any:
    """Create a tool instance by importing the function from the config."""
    import importlib

    tool_type = tool.type

    module = importlib.import_module("examples.07_full_agent.components.tools")
    if tool_type == "search":
        return getattr(module, "web_search_tool")
    if tool_type == "calculator":
        return getattr(module, "calculator_tool")
    if tool_type == "validator":
        return getattr(module, "data_validator")
    raise ValueError(f"Unknown tool type: {tool_type}")


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

    module_path, function_name = function_path.rsplit(".", 1)
    import importlib

    module = importlib.import_module(module_path)
    func = getattr(module, function_name)
    return func
