"""Dummy factories for registry tests."""

from __future__ import annotations

from typing import Any

from agent_ethan2.ir import NormalizedComponent, NormalizedProvider, NormalizedTool


def provider_factory(provider: NormalizedProvider) -> dict[str, Any]:
    return {"id": provider.id, "type": provider.type, **provider.config}


class _DummyTool:
    def __init__(self, tool: NormalizedTool, provider_instance: Any, permissions: Any) -> None:
        self.id = tool.id
        self.type = tool.type
        self.provider = provider_instance
        self.permissions = permissions


def tool_factory(tool: NormalizedTool, provider_instance: Any) -> _DummyTool:
    return _DummyTool(tool, provider_instance, permissions=["read"])


def bad_permission_factory(tool: NormalizedTool, provider_instance: Any) -> _DummyTool:
    return _DummyTool(tool, provider_instance, permissions="not-iterable")


def component_factory(component: NormalizedComponent, provider_instance: Any, tool_instance: Any):
    def impl(state: dict[str, Any], inputs: dict[str, Any], ctx: Any) -> dict[str, Any]:
        return {
            "state": state,
            "inputs": inputs,
            "ctx": ctx,
            "provider": provider_instance,
            "tool": tool_instance,
            "config": component.config,
        }

    return impl


def bad_component_factory(component: NormalizedComponent, provider_instance: Any, tool_instance: Any):
    def impl(state: dict[str, Any]) -> dict[str, Any]:
        return state

    return impl


def non_callable_component_factory(component: NormalizedComponent, provider_instance: Any, tool_instance: Any):
    return "not callable"
