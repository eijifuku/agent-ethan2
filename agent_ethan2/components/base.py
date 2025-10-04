"""Base utilities for component factory implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping as MappingABC
import asyncio
from typing import Any, Mapping, Optional

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedComponent


class ComponentFactoryBase(ABC):
    """Base class for component factories with shared helpers."""

    error_code = "ERR_COMPONENT_FACTORY"

    def __call__(
        self,
        component: NormalizedComponent,
        provider_instance: Any,
        tool_instance: Any,
    ) -> Any:
        if not isinstance(component, NormalizedComponent):  # pragma: no cover - defensive
            raise GraphExecutionError(
                self.error_code,
                "Component factory received an unexpected payload",
                pointer="/components",
            )
        try:
            result = self.build(component, provider_instance, tool_instance)
        except GraphExecutionError:
            raise
        except Exception as exc:  # pragma: no cover - defensive rescue
            raise GraphExecutionError(
                self.error_code,
                f"Failed to initialise component '{component.type}': {exc}",
                pointer=self._pointer(component),
            ) from exc

        if not callable(result):
            raise GraphExecutionError(
                self.error_code,
                "Component factory must return a callable",
                pointer=self._pointer(component),
            )
        return result

    @abstractmethod
    def build(
        self,
        component: NormalizedComponent,
        provider_instance: Any,
        tool_instance: Any,
    ) -> Any:
        """Create a component callable."""

    # Helper utilities -----------------------------------------------------

    def coerce_float(
        self,
        component: NormalizedComponent,
        value: Any,
        *,
        field: str,
    ) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise GraphExecutionError(
                self.error_code,
                f"Invalid float for '{field}': {value!r}",
                pointer=self._pointer(component),
            ) from exc

    def coerce_int(
        self,
        component: NormalizedComponent,
        value: Any,
        *,
        field: str,
    ) -> Optional[int]:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise GraphExecutionError(
                self.error_code,
                f"Invalid integer for '{field}': {value!r}",
                pointer=self._pointer(component),
            ) from exc

    def require_provider(self, component: NormalizedComponent, provider_instance: Any) -> Mapping[str, Any]:
        if not isinstance(provider_instance, MappingABC):
            raise GraphExecutionError(
                self.error_code,
                "Component requires a provider instance",
                pointer=self._pointer(component),
            )
        return provider_instance

    async def run_in_executor(self, func) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func)

    def _pointer(self, component: NormalizedComponent) -> str:
        return f"/components/{component.id}"


__all__ = ["ComponentFactoryBase"]
