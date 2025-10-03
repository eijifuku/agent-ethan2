"""Tests for provider/tool/component registry resolution (A3)."""

from __future__ import annotations

import pytest

from agent_ethan2.ir import (
    NormalizedComponent,
    NormalizedGraph,
    NormalizedGraphNode,
    NormalizedIR,
    NormalizedProvider,
    NormalizedRuntime,
    NormalizedTool,
)
from agent_ethan2.registry import (
    ComponentResolver,
    ProviderResolver,
    Registry,
    RegistryResolutionError,
    ToolResolver,
)


@pytest.fixture()
def normalized_ir() -> NormalizedIR:
    provider = NormalizedProvider(id="openai", type="dummy", config={})
    tool = NormalizedTool(id="tool", type="dummy", provider_id="openai", config={})
    component = NormalizedComponent(
        id="component",
        type="dummy",
        provider_id="openai",
        tool_id="tool",
        inputs={},
        outputs={},
        config={"temperature": 0.1},
    )
    graph = NormalizedGraph(
        entry_id="start",
        nodes={
            "start": NormalizedGraphNode(
                id="start",
                type="component",
                component_id="component",
                next_nodes=(),
                routes={},
                inputs={},
                outputs={},
                config={},
                pointer="/graph/nodes/0",
            )
        },
        outputs=(),
        history=None,
    )
    runtime = NormalizedRuntime(
        engine="lc.lcel",
        graph_name=None,
        defaults={},
        default_provider_id="openai",
    )
    return NormalizedIR(
        meta={"version": 2},
        runtime=runtime,
        providers={provider.id: provider},
        tools={tool.id: tool},
        components={component.id: component},
        graph=graph,
        policies={},
        histories={},
    )


@pytest.fixture()
def registry() -> Registry:
    provider_resolver = ProviderResolver(
        factories={"dummy": "tests.dummies.provider_factory"},
        cache={},
    )
    tool_resolver = ToolResolver(
        factories={
            "dummy": "tests.dummies.tool_factory",
            "bad": "tests.dummies.bad_permission_factory",
        },
        cache={},
    )
    component_resolver = ComponentResolver(
        factories={
            "dummy": "tests.dummies.component_factory",
            "invalid": "tests.dummies.bad_component_factory",
            "noncallable": "tests.dummies.non_callable_component_factory",
        },
        cache={},
    )
    return Registry(
        provider_resolver=provider_resolver,
        tool_resolver=tool_resolver,
        component_resolver=component_resolver,
    )


def test_registry_materialize_success(normalized_ir: NormalizedIR, registry: Registry) -> None:
    materialized = registry.materialize(normalized_ir)

    provider_instance = materialized["providers"]["openai"]
    tool_instance = materialized["tools"]["tool"]
    component_callable = materialized["components"]["component"]

    assert provider_instance["id"] == "openai"
    assert tool_instance.provider is provider_instance
    assert callable(component_callable)

    # cache hits on subsequent resolution
    provider_again = registry.provider_resolver.resolve(normalized_ir.providers["openai"])
    tool_again = registry.tool_resolver.resolve(normalized_ir.tools["tool"], provider_instance)
    component_again = registry.component_resolver.resolve(
        normalized_ir.components["component"],
        provider_instance,
        tool_instance,
    )

    assert provider_again is provider_instance
    assert tool_again is tool_instance
    assert component_again is component_callable


def test_tool_factory_missing_raises(registry: Registry, normalized_ir: NormalizedIR) -> None:
    unknown_tool = NormalizedTool(id="missing", type="unknown", provider_id=None, config={})
    with pytest.raises(RegistryResolutionError) as excinfo:
        registry.tool_resolver.resolve(unknown_tool, provider_instance=None)
    assert excinfo.value.code == "ERR_TOOL_IMPORT"
    assert excinfo.value.pointer == "/tools/missing"


def test_tool_permissions_type_invalid(registry: Registry, normalized_ir: NormalizedIR) -> None:
    tool = NormalizedTool(id="bad-tool", type="bad", provider_id=None, config={})
    with pytest.raises(RegistryResolutionError) as excinfo:
        registry.tool_resolver.resolve(tool, provider_instance=None)
    assert excinfo.value.code == "ERR_TOOL_PERM_TYPE"
    assert excinfo.value.pointer == "/tools/bad-tool"


def test_component_signature_invalid(registry: Registry, normalized_ir: NormalizedIR) -> None:
    component = NormalizedComponent(
        id="broken",
        type="invalid",
        provider_id=None,
        tool_id=None,
        inputs={},
        outputs={},
        config={},
    )
    with pytest.raises(RegistryResolutionError) as excinfo:
        registry.component_resolver.resolve(component, provider_instance=None, tool_instance=None)
    assert excinfo.value.code == "ERR_COMPONENT_SIGNATURE"
    assert excinfo.value.pointer == "/components/broken"


def test_component_factory_returns_non_callable(registry: Registry) -> None:
    component = NormalizedComponent(
        id="bad",
        type="noncallable",
        provider_id=None,
        tool_id=None,
        inputs={},
        outputs={},
        config={},
    )
    with pytest.raises(RegistryResolutionError) as excinfo:
        registry.component_resolver.resolve(component, provider_instance=None, tool_instance=None)
    assert excinfo.value.code == "ERR_COMPONENT_SIGNATURE"
    assert excinfo.value.pointer == "/components/bad"
