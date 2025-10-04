"""Factories for Example 06."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.ir import NormalizedComponent


def custom_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """
    Create a custom component by importing the function from the config.
    
    Expected component config:
        function: str - Python import path to the async function (e.g., "examples.06_component.components.custom.text_analyzer")
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
