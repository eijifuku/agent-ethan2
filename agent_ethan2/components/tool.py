"""Built-in factories for tool-based components."""

from __future__ import annotations

from typing import Any, Mapping

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedComponent

from .base import ComponentFactoryBase


class ToolPassthroughComponentFactory(ComponentFactoryBase):
    """Return the resolved tool instance as the component callable."""

    error_code = "ERR_COMPONENT_TOOL_PASSTHROUGH"

    def build(
        self,
        component: NormalizedComponent,
        provider_instance: Any,
        tool_instance: Any,
    ) -> Any:
        if tool_instance is None:
            raise GraphExecutionError(
                self.error_code,
                "Tool passthrough component requires an attached tool instance",
                pointer=self._pointer(component),
            )
        if not callable(tool_instance):
            raise GraphExecutionError(
                self.error_code,
                "Tool instance must be callable",
                pointer=self._pointer(component),
            )
        return tool_instance


def create_tool_passthrough_component(
    component: NormalizedComponent,
    provider_instance: Any,
    tool_instance: Any,
) -> Any:
    return ToolPassthroughComponentFactory()(component, provider_instance, tool_instance)


__all__ = ["ToolPassthroughComponentFactory", "create_tool_passthrough_component"]
