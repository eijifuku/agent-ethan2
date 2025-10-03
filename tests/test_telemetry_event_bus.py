"""Tests for telemetry event bus and exporters (C1/C2)."""

from __future__ import annotations

import io
import json

import pytest

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.policy.cost import CostLimiter
from agent_ethan2.policy.masking import MaskingEngine
from agent_ethan2.policy.permissions import PermissionManager
from agent_ethan2.telemetry.event_bus import EventBus
from agent_ethan2.telemetry.exporters.jsonl import JsonlExporter
from agent_ethan2.telemetry.exporters.otlp import OtlpExporter


class FailingExporter:
    def export(self, event: str, payload: dict) -> None:
        raise RuntimeError("boom")


def test_event_bus_masks_and_exports() -> None:
    buffer = io.StringIO()
    jsonl = JsonlExporter(stream=buffer)
    otlp = OtlpExporter()
    masking = MaskingEngine({"fields": ["inputs.secret"], "diff_fields": ["outputs.text"]})
    permissions = PermissionManager({"allow": {"cmp-tool": ["http"]}})
    cost = CostLimiter({"per_run_tokens": 20})

    bus = EventBus(
        exporters=[jsonl, otlp, FailingExporter()],
        masking=masking,
        permissions=permissions,
        cost=cost,
    )

    run_id = "run-1"
    bus.emit(
        "llm.call",
        run_id=run_id,
        node_id="llm-node",
        provider_id="openai",
        model="gpt-4",
        inputs={"prompt": "Hello", "secret": "hide me"},
        outputs={"text": "hi"},
        tokens_in=5,
        tokens_out=3,
    )
    bus.emit(
        "tool.call",
        run_id=run_id,
        node_id="tool-node",
        tool_id="search",
        component_id="cmp-tool",
        inputs={"query": "kittens"},
        outputs={"result": "data"},
        required_permissions=["http"],
    )

    lines = [json.loads(line) for line in buffer.getvalue().splitlines()]
    assert [record["event"] for record in lines] == ["llm.call", "tool.call"]
    assert lines[0]["inputs"]["secret"] == "***"
    assert otlp.records[0]["inputs"]["secret"] == "***"
    assert len(bus.fallback_records) == 2  # failing exporter captured


def test_event_bus_cost_limit_triggers() -> None:
    bus = EventBus(cost=CostLimiter({"per_run_tokens": 2}))
    with pytest.raises(GraphExecutionError):
        bus.emit(
            "llm.call",
            run_id="run-2",
            node_id="llm-node",
            inputs={},
            outputs={},
            tokens_in=2,
            tokens_out=2,
        )
