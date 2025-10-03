"""Tests for v1 to v2 converter (E1)."""

from __future__ import annotations

from agent_ethan2.converters.v1_to_v2 import ConversionWarning, convert_v1_to_v2


def test_converter_basic_transforms() -> None:
    doc = {
        "meta": {"version": 1},
        "runtime": {},
        "graph": {
            "start": "start_node",
            "nodes": [
                {"name": "Start Node", "task": "cmp", "input": {"a": 1}, "output": {"b": 2}}
            ],
        },
        "error_policy": {"mode": "fail"},
    }

    result = convert_v1_to_v2(doc)

    assert result.document["meta"]["version"] == 2
    assert result.document["runtime"]["engine"] == "lc.lcel"
    graph = result.document["graph"]
    assert graph["entry"] == "start_node"
    node = graph["nodes"][0]
    assert node["id"] == "start_node"
    assert "task" not in node and node["component"] == "cmp"
    assert "input" not in node and "inputs" in node
    assert "output" not in node and "outputs" in node
    assert "error_policy" not in result.document
    assert "error" in result.document["policies"]
    assert len(result.warnings) >= 4


def test_converter_handles_missing_graph() -> None:
    doc = {"meta": {"version": 1}}
    result = convert_v1_to_v2(doc)
    assert result.document["meta"]["version"] == 2
    assert isinstance(result.warnings[0], ConversionWarning)
