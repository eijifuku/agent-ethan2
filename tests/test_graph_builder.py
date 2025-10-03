"""Tests for the GraphBuilder (B1)."""

from __future__ import annotations

import pytest

from agent_ethan2.graph import GraphBuilder, GraphBuilderError
from agent_ethan2.ir import (
    NormalizedComponent,
    NormalizedGraph,
    NormalizedGraphNode,
    NormalizedGraphOutput,
    NormalizedIR,
    NormalizedProvider,
    NormalizedRuntime,
    NormalizedTool,
)


def _simple_ir() -> tuple[NormalizedIR, dict[str, dict[str, object]]]:
    providers = {
        "openai": NormalizedProvider(id="openai", type="llm", config={}),
    }
    tools = {
        "tool-instance": NormalizedTool(id="tool-instance", type="http", provider_id="openai", config={}),
    }
    components = {
        "cmp-llm": NormalizedComponent(
            id="cmp-llm",
            type="llm",
            provider_id="openai",
            tool_id=None,
            inputs={"prompt": "graph.inputs.prompt"},
            outputs={"text": "$.text"},
            config={},
        ),
        "cmp-router": NormalizedComponent(
            id="cmp-router",
            type="router",
            provider_id="openai",
            tool_id=None,
            inputs={"decision": "node.cmp-llm.text"},
            outputs={"route": "$.route"},
            config={},
        ),
        "cmp-tool": NormalizedComponent(
            id="cmp-tool",
            type="tool",
            provider_id="openai",
            tool_id="tool-instance",
            inputs={"query": "node.cmp-llm.text"},
            outputs={"result": "$.data"},
            config={},
        ),
    }
    graph = NormalizedGraph(
        entry_id="llm-node",
        nodes={
            "llm-node": NormalizedGraphNode(
                id="llm-node",
                type="llm",
                component_id="cmp-llm",
                next_nodes=("router-node",),
                routes={},
                inputs={},
                outputs={},
                config={},
                pointer="/graph/nodes/0",
            ),
            "router-node": NormalizedGraphNode(
                id="router-node",
                type="router",
                component_id="cmp-router",
                next_nodes=("tool-node", "fallback"),
                routes={"success": "tool-node", "fallback": "fallback"},
                inputs={},
                outputs={},
                config={},
                pointer="/graph/nodes/1",
            ),
            "tool-node": NormalizedGraphNode(
                id="tool-node",
                type="tool",
                component_id="cmp-tool",
                next_nodes=(),
                routes={},
                inputs={},
                outputs={},
                config={},
                pointer="/graph/nodes/2",
            ),
            "fallback": NormalizedGraphNode(
                id="fallback",
                type="component",
                component_id=None,
                next_nodes=(),
                routes={},
                inputs={},
                outputs={},
                config={},
                pointer="/graph/nodes/3",
            ),
        },
        outputs=(
            NormalizedGraphOutput(key="final", node_id="tool-node", output="result"),
        ),
        history=None,
    )
    runtime = NormalizedRuntime(
        engine="lc.lcel",
        graph_name="demo",
        defaults={},
        default_provider_id="openai",
    )
    ir = NormalizedIR(
        meta={"version": 2},
        runtime=runtime,
        providers=providers,
        tools=tools,
        components=components,
        graph=graph,
        policies={},
        histories={},
    )
    resolved = {
        "providers": {"openai": object()},
        "tools": {"tool-instance": object()},
        "components": {
            "cmp-llm": lambda *args, **kwargs: {"text": "ok"},
            "cmp-router": lambda *args, **kwargs: {"route": "success"},
            "cmp-tool": lambda *args, **kwargs: {"data": "done"},
        },
    }
    return ir, resolved


def test_build_graph_definition_success() -> None:
    ir, resolved = _simple_ir()
    builder = GraphBuilder()

    definition = builder.build(ir, resolved)

    assert definition.entrypoint == "llm-node"
    assert definition.name == "demo"
    assert set(definition.nodes) == {"llm-node", "router-node", "tool-node", "fallback"}
    assert definition.policies == ir.policies

    llm_spec = definition.nodes["llm-node"]
    assert llm_spec.kind == "llm"
    assert llm_spec.component_id == "cmp-llm"

    router_spec = definition.nodes["router-node"]
    assert router_spec.kind == "router"
    assert router_spec.routes["success"] == "tool-node"

    tool_spec = definition.nodes["tool-node"]
    assert tool_spec.kind == "tool"
    assert tool_spec.component_meta and tool_spec.component_meta.tool_id == "tool-instance"


def test_llm_without_provider_raises() -> None:
    ir, resolved = _simple_ir()
    component = ir.components["cmp-llm"]
    ir.components["cmp-llm"] = NormalizedComponent(
        id=component.id,
        type=component.type,
        provider_id=None,
        tool_id=component.tool_id,
        inputs=component.inputs,
        outputs=component.outputs,
        config=component.config,
    )

    builder = GraphBuilder()
    with pytest.raises(GraphBuilderError) as excinfo:
        builder.build(ir, resolved)

    assert excinfo.value.code == "ERR_PROVIDER_DEFAULT_MISSING"
    assert excinfo.value.pointer == ir.graph.nodes["llm-node"].pointer


def test_missing_tool_runtime_raises() -> None:
    ir, resolved = _simple_ir()
    resolved["tools"].pop("tool-instance")

    builder = GraphBuilder()
    with pytest.raises(GraphBuilderError) as excinfo:
        builder.build(ir, resolved)

    assert excinfo.value.code == "ERR_TOOL_NOT_FOUND"
    assert excinfo.value.pointer == ir.graph.nodes["tool-node"].pointer


def test_router_without_routes_raises() -> None:
    ir, resolved = _simple_ir()
    node = ir.graph.nodes["router-node"]
    ir.graph.nodes["router-node"] = NormalizedGraphNode(
        id=node.id,
        type=node.type,
        component_id=node.component_id,
        next_nodes=(),
        routes={},
        inputs=node.inputs,
        outputs=node.outputs,
        config=node.config,
        pointer=node.pointer,
    )

    builder = GraphBuilder()
    with pytest.raises(GraphBuilderError) as excinfo:
        builder.build(ir, resolved)

    assert excinfo.value.code == "ERR_ROUTER_NO_MATCH"
    assert excinfo.value.pointer == node.pointer
