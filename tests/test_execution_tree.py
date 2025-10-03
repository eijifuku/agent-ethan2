"""Tests for execution tree builder (C3)."""

from __future__ import annotations

import pytest

from agent_ethan2.graph import GraphBuilder
from agent_ethan2.telemetry import EventBus, ExecutionTreeBuilder
from tests.test_runtime_scheduler import _build_runtime, LlmComponent, RouterComponent, ToolComponent


@pytest.mark.asyncio
async def test_execution_tree_builder() -> None:
    builder = ExecutionTreeBuilder()
    bus = EventBus(exporters=[builder])

    scheduler, _, ir, resolved = await _build_runtime(LlmComponent(), RouterComponent(), ToolComponent())
    definition = GraphBuilder().build(ir, resolved)

    result = await scheduler.run(
        definition,
        inputs={"prompt": "tree"},
        event_emitter=bus,
        run_id="tree-run",
    )

    tree = builder.build()
    assert tree["graph"]["run_id"] == result.run_id
    node_ids = {node["node_id"] for node in tree["nodes"]}
    assert "llm-node" in node_ids
    assert any(node["retries"] == [] for node in tree["nodes"])
