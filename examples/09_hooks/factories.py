"""Factories for Example 09."""

from __future__ import annotations

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


def error_provider_factory(provider: NormalizedProvider) -> Mapping[str, Any]:
    """Create OpenAI provider with invalid API key for error testing."""
    # Use invalid API key from config to trigger authentication error
    api_key = provider.config.get("api_key", "invalid-key")
    client = OpenAI(api_key=api_key)
    model = provider.config.get("model", "gpt-4o-mini")
    
    return {"client": client, "model": model, "config": dict(provider.config)}


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

