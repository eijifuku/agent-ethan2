"""Resolver and registry for providers, tools, and components."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional
import inspect

from agent_ethan2.ir import NormalizedComponent, NormalizedIR, NormalizedProvider, NormalizedTool


class RegistryResolutionError(RuntimeError):
    """Raised when a provider/tool/component cannot be resolved."""

    def __init__(self, code: str, message: str, *, pointer: Optional[str] = None) -> None:
        self.code = code
        self.pointer = pointer or "/"
        super().__init__(f"[{code}] {message} at {self.pointer}")


ProviderFactory = Callable[[NormalizedProvider], Any]
ToolFactory = Callable[[NormalizedTool, Any], Any]
ComponentFactory = Callable[[NormalizedComponent, Any, Any], Any]


@dataclass
class ProviderResolver:
    """Resolves providers using configurable import rules."""

    factories: Mapping[str, str]
    cache: MutableMapping[str, Any]

    def resolve(self, provider: NormalizedProvider) -> Any:
        if provider.id in self.cache:
            return self.cache[provider.id]
        dotted_path = self.factories.get(provider.type)
        if not dotted_path:
            raise RegistryResolutionError(
                "ERR_TOOL_IMPORT",
                f"No factory registered for provider type '{provider.type}'",
                pointer=f"/providers/{provider.id}",
            )
        factory = _load_factory(
            dotted_path,
            expected_callable=True,
            code="ERR_TOOL_IMPORT",
            pointer=f"/providers/{provider.id}",
        )
        instance = factory(provider)
        self.cache[provider.id] = instance
        return instance


@dataclass
class ToolResolver:
    """Resolves tools from normalized definitions."""

    factories: Mapping[str, str]
    cache: MutableMapping[str, Any]

    def resolve(self, tool: NormalizedTool, provider_instance: Any) -> Any:
        cache_key = tool.id
        if cache_key in self.cache:
            return self.cache[cache_key]
        dotted_path = self.factories.get(tool.type)
        if not dotted_path:
            raise RegistryResolutionError(
                "ERR_TOOL_IMPORT",
                f"No factory registered for tool type '{tool.type}'",
                pointer=f"/tools/{tool.id}",
            )
        factory = _load_factory(
            dotted_path,
            expected_callable=True,
            code="ERR_TOOL_IMPORT",
            pointer=f"/tools/{tool.id}",
        )
        instance = factory(tool, provider_instance)
        _validate_tool_permissions(instance, pointer=f"/tools/{tool.id}")
        self.cache[cache_key] = instance
        return instance


@dataclass
class ComponentResolver:
    """Builds component callables and validates their signatures."""

    factories: Mapping[str, str]
    cache: MutableMapping[str, Any]

    def resolve(self, component: NormalizedComponent, provider_instance: Any, tool_instance: Any) -> Any:
        cache_key = component.id
        if cache_key in self.cache:
            return self.cache[cache_key]
        dotted_path = self.factories.get(component.type)
        if not dotted_path:
            raise RegistryResolutionError(
                "ERR_COMPONENT_IMPORT",
                f"No factory registered for component type '{component.type}'",
                pointer=f"/components/{component.id}",
            )
        factory = _load_factory(
            dotted_path,
            expected_callable=True,
            code="ERR_COMPONENT_IMPORT",
            pointer=f"/components/{component.id}",
        )
        instance = factory(component, provider_instance, tool_instance)
        _validate_component_signature(instance, pointer=f"/components/{component.id}")
        self.cache[cache_key] = instance
        return instance


@dataclass
class Registry:
    """High-level registry that resolves all entities for a normalized IR."""

    provider_resolver: ProviderResolver
    tool_resolver: ToolResolver
    component_resolver: ComponentResolver

    def materialize(self, ir: NormalizedIR) -> Dict[str, Any]:
        providers: Dict[str, Any] = {}
        tools: Dict[str, Any] = {}
        components: Dict[str, Any] = {}

        for provider in ir.providers.values():
            providers[provider.id] = self.provider_resolver.resolve(provider)

        for tool in ir.tools.values():
            provider_instance = providers.get(tool.provider_id) if tool.provider_id else None
            tools[tool.id] = self.tool_resolver.resolve(tool, provider_instance)

        for component in ir.components.values():
            provider_instance = providers.get(component.provider_id) if component.provider_id else None
            tool_instance = tools.get(component.tool_id) if component.tool_id else None
            components[component.id] = self.component_resolver.resolve(component, provider_instance, tool_instance)

        return {
            "providers": providers,
            "tools": tools,
            "components": components,
        }


def _load_factory(dotted_path: str, *, expected_callable: bool, code: str, pointer: str) -> Callable[..., Any]:
    try:
        module_name, attr_name = dotted_path.rsplit(".", 1)
    except ValueError as exc:  # pragma: no cover - defensive
        raise RegistryResolutionError(code, f"Invalid import path '{dotted_path}'", pointer=pointer) from exc
    try:
        module = import_module(module_name)
    except ImportError as exc:
        raise RegistryResolutionError(code, f"Failed to import module '{module_name}'", pointer=pointer) from exc
    try:
        factory = getattr(module, attr_name)
    except AttributeError as exc:
        raise RegistryResolutionError(code, f"Factory '{attr_name}' not found in '{module_name}'", pointer=pointer) from exc
    if expected_callable and not callable(factory):
        raise RegistryResolutionError(code, f"Factory '{dotted_path}' is not callable", pointer=pointer)
    return factory


def _validate_tool_permissions(instance: Any, *, pointer: str) -> None:
    permissions = getattr(instance, "permissions", None)
    if permissions is None:
        return
    if isinstance(permissions, (str, bytes)) or not isinstance(permissions, Iterable):
        raise RegistryResolutionError(
            "ERR_TOOL_PERM_TYPE",
            "Tool permissions must be an iterable",
            pointer=pointer,
        )


def _validate_component_signature(component: Any, *, pointer: str) -> None:
    callable_obj = component
    if not callable(callable_obj):
        raise RegistryResolutionError(
            "ERR_COMPONENT_SIGNATURE",
            "Component factory must return a callable",
            pointer=pointer,
        )
    signature = inspect.signature(callable_obj)
    params = list(signature.parameters.values())
    expected = ["state", "inputs", "ctx"]
    if len(params) < 3:
        raise RegistryResolutionError(
            "ERR_COMPONENT_SIGNATURE",
            "Component callable must accept at least (state, inputs, ctx)",
            pointer=pointer,
        )
    for param, name in zip(params[:3], expected):
        if param.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY):
            raise RegistryResolutionError(
                "ERR_COMPONENT_SIGNATURE",
                f"Component parameter '{param.name}' must be positional",
                pointer=pointer,
            )
        if param.name != name:
            raise RegistryResolutionError(
                "ERR_COMPONENT_SIGNATURE",
                f"Component parameter '{param.name}' must be named '{name}'",
                pointer=pointer,
            )
    # optional: allow additional parameters if they have defaults
    for param in params[3:]:
        if param.default is inspect.Signature.empty:
            raise RegistryResolutionError(
                "ERR_COMPONENT_SIGNATURE",
                "Additional component parameters must have defaults",
                pointer=pointer,
            )
