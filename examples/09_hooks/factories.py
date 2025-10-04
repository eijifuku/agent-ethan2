"""Factories for Example 09."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.ir import NormalizedComponent




def llm_with_hooks_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create LLM component with hooks."""
    import importlib
    
    module = importlib.import_module("examples.09_hooks.components.hooked_llm")
    LoggingLLM = getattr(module, "LoggingLLM")
    
    client = provider_instance["client"]
    model = provider_instance["model"]
    
    return LoggingLLM(client=client, model=model)


def cached_component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
):
    """Create cached component with hooks."""
    import importlib
    
    module = importlib.import_module("examples.09_hooks.components.hooked_llm")
    CachedComponent = getattr(module, "CachedComponent")
    
    return CachedComponent()

