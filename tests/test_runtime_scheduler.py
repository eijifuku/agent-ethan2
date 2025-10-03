"""Tests for the async runtime scheduler (B1/B2)."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Mapping, Optional

import pytest

from agent_ethan2.graph import GraphBuilder, GraphExecutionError
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
from agent_ethan2.runtime.events import InMemoryEventEmitter
from agent_ethan2.runtime.scheduler import Scheduler


class LlmComponent:
    async def __call__(self, state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        await asyncio.sleep(0)
        prompt = inputs.get("prompt", "")
        return {"text": prompt.upper()}


class RouterComponent:
    def __call__(self, state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        text = inputs.get("decision", "")
        if "ERROR" in text:
            return {"route": "fallback"}
        return {"route": "success"}


class ToolComponent:
    def __call__(self, state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        query = inputs.get("query", "")
        return {"data": f"tool:{query}"}


class MapComponent:
    def __call__(self, state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        value = inputs.get("value")
        if value == "boom":
            raise ValueError("map failure")
        return {"value": value, "doubled": value * 2 if isinstance(value, (int, float)) else value}


class ClosingTool:
    def __init__(self, value: str = "done") -> None:
        self.closed = False
        self.ctx: Optional[Mapping[str, Any]] = None
        self.value = value

    def __call__(self, state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        self.ctx = ctx
        return {"data": self.value}

    def close(self) -> None:
        self.closed = True


class AsyncClosingTool(ClosingTool):
    async def close(self) -> None:  # type: ignore[override]
        self.closed = True


class ErrorTool:
    def __init__(self) -> None:
        self.ctx: Optional[Mapping[str, Any]] = None

    def __call__(self, state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        self.ctx = ctx
        raise ValueError("boom")


class TemporaryError(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(f"temporary status {status}")
        self.status = status


class FlakyTool(ToolComponent):
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        self.calls += 1
        if self.calls == 1:
            raise TemporaryError(500)
        return super().__call__(state, inputs, ctx)


async def _build_runtime(
    llm: Any,
    router: Any,
    tool: Any,
    *,
    retry_config: Optional[Mapping[str, Any]] = None,
    rate_limit_config: Optional[Mapping[str, Any]] = None,
    permissions_config: Optional[Mapping[str, Any]] = None,
) -> tuple[Scheduler, InMemoryEventEmitter, NormalizedIR, dict[str, dict[str, Any]]]:
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
            inputs={"decision": "node.llm-node.text"},
            outputs={"route": "$.route"},
            config={},
        ),
        "cmp-tool": NormalizedComponent(
            id="cmp-tool",
            type="tool",
            provider_id="openai",
            tool_id="tool-instance",
            inputs={"query": "node.llm-node.text"},
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
    policies: Dict[str, Any] = {}
    if retry_config is not None:
        policies["retry"] = retry_config
    if rate_limit_config is not None:
        policies["rate_limit"] = rate_limit_config
    if permissions_config is not None:
        policies["permissions"] = permissions_config

    ir = NormalizedIR(
        meta={"version": 2},
        runtime=runtime,
        providers=providers,
        tools=tools,
        components=components,
        graph=graph,
        policies=policies,
        histories={},
    )
    resolved = {
        "providers": {"openai": object()},
        "tools": {"tool-instance": object()},
        "components": {
            "cmp-llm": llm,
            "cmp-router": router,
            "cmp-tool": tool,
        },
    }
    scheduler = Scheduler()
    emitter = InMemoryEventEmitter()
    return scheduler, emitter, ir, resolved


async def _build_map_runtime(
    component: Any,
    *,
    failure_mode: str = "fail_fast",
    retry_config: Optional[Mapping[str, Any]] = None,
    rate_limit_config: Optional[Mapping[str, Any]] = None,
    permissions_config: Optional[Mapping[str, Any]] = None,
) -> tuple[Scheduler, InMemoryEventEmitter, NormalizedIR, dict[str, dict[str, Any]]]:
    components = {
        "cmp-map": NormalizedComponent(
            id="cmp-map",
            type="map",
            provider_id=None,
            tool_id=None,
            inputs={"value": "map.item"},
            outputs={"value": "$.value", "doubled": "$.doubled"},
            config={},
        )
    }
    graph = NormalizedGraph(
        entry_id="map-node",
        nodes={
            "map-node": NormalizedGraphNode(
                id="map-node",
                type="map",
                component_id="cmp-map",
                next_nodes=(),
                routes={},
                inputs={},
                outputs={},
                config={
                    "collection": "graph.inputs.items",
                    "failure_mode": failure_mode,
                    "ordered": True,
                    "result_key": "results",
                },
                pointer="/graph/nodes/0",
            )
        },
        outputs=(
            NormalizedGraphOutput(key="results", node_id="map-node", output="results"),
            NormalizedGraphOutput(key="errors", node_id="map-node", output="errors"),
        ),
        history=None,
    )
    runtime = NormalizedRuntime(
        engine="lc.lcel",
        graph_name="map-demo",
        defaults={},
        default_provider_id=None,
    )
    policies: Dict[str, Any] = {}
    if retry_config is not None:
        policies["retry"] = retry_config
    if rate_limit_config is not None:
        policies["rate_limit"] = rate_limit_config
    if permissions_config is not None:
        policies["permissions"] = permissions_config

    ir = NormalizedIR(
        meta={"version": 2},
        runtime=runtime,
        providers={},
        tools={},
        components=components,
        graph=graph,
        policies=policies,
        histories={},
    )
    resolved = {
        "providers": {},
        "tools": {},
        "components": {"cmp-map": component},
    }
    scheduler = Scheduler()
    emitter = InMemoryEventEmitter()
    return scheduler, emitter, ir, resolved


async def _build_parallel_runtime(
    branches: Mapping[str, Any],
    *,
    merge_policy: str = "namespace",
    mode: str = "all",
    retry_config: Optional[Mapping[str, Any]] = None,
    rate_limit_config: Optional[Mapping[str, Any]] = None,
    permissions_config: Optional[Mapping[str, Any]] = None,
) -> tuple[Scheduler, InMemoryEventEmitter, NormalizedIR, dict[str, dict[str, Any]]]:
    components: Dict[str, NormalizedComponent] = {}
    node_defs: Dict[str, NormalizedGraphNode] = {}
    resolved_components: Dict[str, Any] = {}
    for idx, (branch_id, component) in enumerate(branches.items()):
        component_id = f"cmp-{branch_id}"
        components[component_id] = NormalizedComponent(
            id=component_id,
            type="component",
            provider_id=None,
            tool_id=None,
            inputs={"value": "graph.inputs.value"},
            outputs={"output": "$.value"},
            config={},
        )
        node_defs[branch_id] = NormalizedGraphNode(
            id=branch_id,
            type="component",
            component_id=component_id,
            next_nodes=(),
            routes={},
            inputs={},
            outputs={},
            config={},
            pointer=f"/graph/nodes/{idx+1}",
        )
        resolved_components[component_id] = component

    parallel_node = NormalizedGraphNode(
        id="parallel-node",
        type="parallel",
        component_id=None,
        next_nodes=(),
        routes={},
        inputs={},
        outputs={},
        config={
            "branches": list(branches.keys()),
            "merge_policy": merge_policy,
            "mode": mode,
        },
        pointer="/graph/nodes/0",
    )
    node_defs = {"parallel-node": parallel_node, **node_defs}

    graph = NormalizedGraph(
        entry_id="parallel-node",
        nodes=node_defs,
        outputs=(
            NormalizedGraphOutput(key="results", node_id="parallel-node", output="results"),
        ),
        history=None,
    )
    runtime = NormalizedRuntime(
        engine="lc.lcel",
        graph_name="parallel-demo",
        defaults={},
        default_provider_id=None,
    )
    policies: Dict[str, Any] = {}
    if retry_config is not None:
        policies["retry"] = retry_config
    if rate_limit_config is not None:
        policies["rate_limit"] = rate_limit_config
    if permissions_config is not None:
        policies["permissions"] = permissions_config

    ir = NormalizedIR(
        meta={"version": 2},
        runtime=runtime,
        providers={},
        tools={},
        components=components,
        graph=graph,
        policies=policies,
        histories={},
    )
    resolved = {
        "providers": {},
        "tools": {},
        "components": resolved_components,
    }
    scheduler = Scheduler()
    emitter = InMemoryEventEmitter()
    return scheduler, emitter, ir, resolved


@pytest.mark.asyncio
async def test_scheduler_runs_graph_and_emits_events() -> None:
    scheduler, emitter, ir, resolved = await _build_runtime(LlmComponent(), RouterComponent(), ToolComponent())
    definition = GraphBuilder().build(ir, resolved)

    result = await scheduler.run(definition, inputs={"prompt": "hello"}, event_emitter=emitter)

    assert result.outputs["final"] == "tool:HELLO"
    events = [record["event"] for record in emitter.events]
    assert events[0] == "graph.start"
    assert "llm.call" in events
    assert "tool.call" in events
    assert events[-1] == "graph.finish"


@pytest.mark.asyncio
async def test_scheduler_timeout_emits_event() -> None:
    class SlowLlm(LlmComponent):
        async def __call__(self, state, inputs, ctx):
            await asyncio.sleep(0.2)
            return await super().__call__(state, inputs, ctx)

    scheduler, emitter, ir, resolved = await _build_runtime(SlowLlm(), RouterComponent(), ToolComponent())
    definition = GraphBuilder().build(ir, resolved)

    with pytest.raises(TimeoutError):
        await scheduler.run(definition, inputs={"prompt": "hello"}, event_emitter=emitter, timeout=0.05)

    assert any(event["event"] == "timeout" for event in emitter.events)


@pytest.mark.asyncio
async def test_scheduler_cancellation_emits_event() -> None:
    class BlockingTool(ToolComponent):
        async def __call__(self, state, inputs, ctx):
            await asyncio.sleep(0.2)
            return ToolComponent.__call__(self, state, inputs, ctx)

    scheduler, emitter, ir, resolved = await _build_runtime(LlmComponent(), RouterComponent(), BlockingTool())
    definition = GraphBuilder().build(ir, resolved)

    task = asyncio.create_task(scheduler.run(definition, inputs={"prompt": "cancel"}, event_emitter=emitter))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert any(event["event"] == "cancelled" for event in emitter.events)


@pytest.mark.asyncio
async def test_router_no_match_raises_error() -> None:
    class BadRouter(RouterComponent):
        def __call__(self, state, inputs, ctx):
            return {"route": "missing"}

    scheduler, emitter, ir, resolved = await _build_runtime(LlmComponent(), BadRouter(), ToolComponent())
    definition = GraphBuilder().build(ir, resolved)

    with pytest.raises(GraphExecutionError) as excinfo:
        await scheduler.run(definition, inputs={"prompt": "hello"}, event_emitter=emitter)

    assert excinfo.value.code == "ERR_ROUTER_NO_MATCH"


@pytest.mark.asyncio
async def test_map_node_collects_results() -> None:
    scheduler, emitter, ir, resolved = await _build_map_runtime(MapComponent(), failure_mode="collect_errors")
    definition = GraphBuilder().build(ir, resolved)

    result = await scheduler.run(
        definition,
        inputs={"items": [1, 2, "boom", 3]},
        event_emitter=emitter,
    )

    results = result.outputs["results"]
    assert [entry["doubled"] for entry in results if entry] == [2, 4, 6]
    errors = result.outputs["errors"]
    assert any(err["index"] == 2 for err in errors)


@pytest.mark.asyncio
async def test_map_node_non_array_raises() -> None:
    scheduler, emitter, ir, resolved = await _build_map_runtime(MapComponent())
    definition = GraphBuilder().build(ir, resolved)

    with pytest.raises(GraphExecutionError) as excinfo:
        await scheduler.run(definition, inputs={"items": "not-array"}, event_emitter=emitter)

    assert excinfo.value.code == "ERR_MAP_OVER_NOT_ARRAY"


@pytest.mark.asyncio
async def test_parallel_namespace_merge() -> None:
    branches = {
        "left": lambda state, inputs, ctx: {"value": inputs["value"] + "-L"},
        "right": lambda state, inputs, ctx: {"value": inputs["value"] + "-R"},
    }

    scheduler, emitter, ir, resolved = await _build_parallel_runtime(branches, merge_policy="namespace")
    definition = GraphBuilder().build(ir, resolved)

    result = await scheduler.run(definition, inputs={"value": "base"}, event_emitter=emitter)

    assert result.outputs["results"]["left"]["output"] == "base-L"
    assert result.outputs["results"]["right"]["output"] == "base-R"


@pytest.mark.asyncio
async def test_parallel_merge_conflict_raises() -> None:
    branches = {
        "first": lambda state, inputs, ctx: {"value": "dup"},
        "second": lambda state, inputs, ctx: {"value": "other"},
    }

    scheduler, emitter, ir, resolved = await _build_parallel_runtime(branches, merge_policy="error")
    definition = GraphBuilder().build(ir, resolved)

    with pytest.raises(GraphExecutionError) as excinfo:
        await scheduler.run(definition, inputs={"value": "base"}, event_emitter=emitter)

    assert excinfo.value.code == "ERR_NODE_RUNTIME"


@pytest.mark.asyncio
async def test_parallel_first_success_mode() -> None:
    async def slow_branch(state, inputs, ctx):
        await asyncio.sleep(0.1)
        return {"value": "slow"}

    branches = {
        "slow": slow_branch,
        "fast": lambda state, inputs, ctx: {"value": "fast"},
    }

    scheduler, emitter, ir, resolved = await _build_parallel_runtime(branches, merge_policy="namespace", mode="first_success")
    definition = GraphBuilder().build(ir, resolved)

    result = await scheduler.run(definition, inputs={"value": "base"}, event_emitter=emitter)

    assert set(result.outputs["results"].keys()) == {"fast"}


@pytest.mark.asyncio
async def test_retry_policy_recovers_from_failure() -> None:
    flaky_tool = FlakyTool()
    retry_config = {
        "default": {"strategy": "fixed", "max_attempts": 2, "interval": 0.0},
        "overrides": [
            {"target": "tool-node", "strategy": "fixed", "max_attempts": 3, "interval": 0.0}
        ],
    }

    scheduler, emitter, ir, resolved = await _build_runtime(
        LlmComponent(),
        RouterComponent(),
        flaky_tool,
        retry_config=retry_config,
    )
    definition = GraphBuilder().build(ir, resolved)

    result = await scheduler.run(definition, inputs={"prompt": "hello"}, event_emitter=emitter)

    assert result.outputs["final"] == "tool:HELLO"
    assert flaky_tool.calls == 2
    assert any(event["event"] == "retry.attempt" for event in emitter.events)


@pytest.mark.asyncio
async def test_invalid_retry_config_raises() -> None:
    retry_config = {"default": {"strategy": "unknown"}}
    scheduler, emitter, ir, resolved = await _build_runtime(
        LlmComponent(),
        RouterComponent(),
        ToolComponent(),
        retry_config=retry_config,
    )
    definition = GraphBuilder().build(ir, resolved)

    with pytest.raises(GraphExecutionError) as excinfo:
        await scheduler.run(definition, inputs={"prompt": "hello"}, event_emitter=emitter)

    assert excinfo.value.code == "ERR_RETRY_PREDICATE"


@pytest.mark.asyncio
async def test_rate_limit_wait_emitted() -> None:
    rate_config = {
        "shared_providers": {"openai": "llm"},
        "providers": [
            {"target": "llm", "type": "token_bucket", "capacity": 1, "refill_rate": 1000.0}
        ],
        "nodes": [
            {"target": "map-node", "type": "token_bucket", "capacity": 1, "refill_rate": 1000.0}
        ],
    }

    scheduler, emitter, ir, resolved = await _build_map_runtime(
        MapComponent(),
        failure_mode="collect_errors",
        rate_limit_config=rate_config,
    )
    definition = GraphBuilder().build(ir, resolved)

    await scheduler.run(definition, inputs={"items": [1, 2]}, event_emitter=emitter)

    waits = [e for e in emitter.events if e["event"] == "rate.limit.wait"]
    assert waits
    assert any(e.get("scope") == "node" for e in waits)

    # provider-level shared bucket (reuse emitter for inspection)
    scheduler2, emitter2, ir2, resolved2 = await _build_runtime(
        LlmComponent(),
        RouterComponent(),
        ToolComponent(),
        rate_limit_config={"shared_providers": {"openai": "llm"}, "providers": rate_config["providers"]},
    )
    definition2 = GraphBuilder().build(ir2, resolved2)
    await scheduler2.run(definition2, inputs={"prompt": "a"}, event_emitter=emitter2)
    await scheduler2.run(definition2, inputs={"prompt": "b"}, event_emitter=emitter2)

    waits2 = [e for e in emitter2.events if e["event"] == "rate.limit.wait"]
    assert any(e.get("scope") == "provider" for e in waits2)


@pytest.mark.asyncio
async def test_invalid_rate_limit_config_raises() -> None:
    rate_config = {"nodes": [{"type": "token_bucket", "capacity": 1}], "shared_providers": {1: 2}}
    scheduler, emitter, ir, resolved = await _build_map_runtime(
        MapComponent(),
        rate_limit_config=rate_config,
    )
    definition = GraphBuilder().build(ir, resolved)

    with pytest.raises(GraphExecutionError) as excinfo:
        await scheduler.run(definition, inputs={"items": [1]}, event_emitter=emitter)

    assert excinfo.value.code == "ERR_RL_POLICY_PARAM"


@pytest.mark.asyncio
async def test_tool_permission_denied() -> None:
    scheduler, emitter, ir, resolved = await _build_runtime(
        LlmComponent(),
        RouterComponent(),
        ToolComponent(),
        permissions_config={"allow": {"cmp-tool": []}},
    )
    component = ir.components["cmp-tool"]
    ir.components["cmp-tool"] = NormalizedComponent(
        id=component.id,
        type=component.type,
        provider_id=component.provider_id,
        tool_id=component.tool_id,
        inputs=component.inputs,
        outputs=component.outputs,
        config={**component.config, "requires_permissions": ["http"]},
    )
    definition = GraphBuilder().build(ir, resolved)

    with pytest.raises(GraphExecutionError) as excinfo:
        await scheduler.run(definition, inputs={"prompt": "hi"}, event_emitter=emitter)

    assert excinfo.value.code == "ERR_TOOL_PERMISSION_DENIED"


@pytest.mark.asyncio
async def test_tool_permission_allowed() -> None:
    scheduler, emitter, ir, resolved = await _build_runtime(
        LlmComponent(),
        RouterComponent(),
        ToolComponent(),
        permissions_config={"allow": {"cmp-tool": ["http"]}},
    )
    component = ir.components["cmp-tool"]
    ir.components["cmp-tool"] = NormalizedComponent(
        id=component.id,
        type=component.type,
        provider_id=component.provider_id,
        tool_id=component.tool_id,
        inputs=component.inputs,
        outputs=component.outputs,
        config={**component.config, "requires_permissions": ["http"]},
    )
    definition = GraphBuilder().build(ir, resolved)

    result = await scheduler.run(definition, inputs={"prompt": "ok"}, event_emitter=emitter)

    assert result.outputs["final"] == "tool:OK"


@pytest.mark.asyncio
async def test_component_close_called() -> None:
    closing_tool = ClosingTool()
    scheduler, emitter, ir, resolved = await _build_runtime(LlmComponent(), RouterComponent(), ToolComponent())
    resolved["components"]["cmp-tool"] = closing_tool
    definition = GraphBuilder().build(ir, resolved)

    await scheduler.run(definition, inputs={"prompt": "close"}, event_emitter=emitter)

    assert closing_tool.closed is True


@pytest.mark.asyncio
async def test_component_async_close_called() -> None:
    closing_tool = AsyncClosingTool()
    scheduler, emitter, ir, resolved = await _build_runtime(LlmComponent(), RouterComponent(), ToolComponent())
    resolved["components"]["cmp-tool"] = closing_tool
    definition = GraphBuilder().build(ir, resolved)

    await scheduler.run(definition, inputs={"prompt": "close"}, event_emitter=emitter)

    assert closing_tool.closed is True


@pytest.mark.asyncio
async def test_component_context_provides_fields() -> None:
    closing_tool = ClosingTool(value="context")
    scheduler, emitter, ir, resolved = await _build_runtime(LlmComponent(), RouterComponent(), ToolComponent())
    resolved["components"]["cmp-tool"] = closing_tool
    definition = GraphBuilder().build(ir, resolved)

    result = await scheduler.run(
        definition,
        inputs={"prompt": "ctx"},
        event_emitter=emitter,
        deadline=123.0,
        registries={"tools": {"search": "fake"}},
    )

    ctx = closing_tool.ctx
    assert ctx is not None
    assert ctx["node_id"] == "tool-node"
    assert ctx.cancel_token.cancelled is False
    assert ctx.deadline == 123.0
    assert ctx.registries["tools"]["search"] == "fake"
    assert ctx.logger.name.endswith("tool-node")
    assert result.outputs["final"] == "context"


@pytest.mark.asyncio
async def test_cancel_token_cancelled_on_error() -> None:
    error_tool = ErrorTool()
    scheduler, emitter, ir, resolved = await _build_runtime(LlmComponent(), RouterComponent(), ToolComponent())
    resolved["components"]["cmp-tool"] = error_tool
    definition = GraphBuilder().build(ir, resolved)

    with pytest.raises(GraphExecutionError):
        await scheduler.run(definition, inputs={"prompt": "oops"}, event_emitter=emitter)

    assert error_tool.ctx is not None
    token = error_tool.ctx["cancel_token"]
    assert token.cancelled is True


@pytest.mark.asyncio
async def test_jsonpath_array_index_resolution() -> None:
    """Test that component outputs with JSONPath array indices (e.g. $.choices[0].text) are correctly resolved."""

    class ArrayOutputComponent:
        async def __call__(self, state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
            return {
                "choices": [
                    {"text": "first", "score": 0.9},
                    {"text": "second", "score": 0.1},
                ],
                "metadata": {"total": 2},
            }

    ir = NormalizedIR(
        meta={"version": 2},
        runtime=NormalizedRuntime(engine="lc.lcel", graph_name="test", defaults={}, default_provider_id="prov"),
        providers={"prov": NormalizedProvider(id="prov", type="test", config={})},
        tools={},
        components={
            "cmp": NormalizedComponent(
                id="cmp",
                type="llm",
                provider_id="prov",
                tool_id=None,
                inputs={},
                outputs={
                    "first_text": "$.choices[0].text",
                    "second_text": "$.choices[1].text",
                    "first_score": "$.choices[0].score",
                    "total": "$.metadata.total",
                },
                config={},
            )
        },
        graph=NormalizedGraph(
            entry_id="node1",
            nodes={
                "node1": NormalizedGraphNode(
                    id="node1",
                    type="llm",
                    component_id="cmp",
                    next_nodes=(),
                    routes={},
                    inputs={},
                    outputs={},
                    config={},
                    pointer="/graph/nodes/0",
                )
            },
            outputs=(
                NormalizedGraphOutput(key="result1", node_id="node1", output="first_text"),
                NormalizedGraphOutput(key="result2", node_id="node1", output="second_text"),
                NormalizedGraphOutput(key="score", node_id="node1", output="first_score"),
                NormalizedGraphOutput(key="count", node_id="node1", output="total"),
            ),
            history=None,
            ),
            policies={},
            histories={},
        )

    resolved = {
        "providers": {"prov": {}},
        "tools": {},
        "components": {"cmp": ArrayOutputComponent()},
    }

    definition = GraphBuilder().build(ir, resolved)
    scheduler = Scheduler()
    emitter = InMemoryEventEmitter()

    result = await scheduler.run(definition, inputs={}, event_emitter=emitter)

    assert result.outputs["result1"] == "first"
    assert result.outputs["result2"] == "second"
    assert result.outputs["score"] == 0.9
    assert result.outputs["count"] == 2
