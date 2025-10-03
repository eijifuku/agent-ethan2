"""Utilities to convert AgentEthan v1 YAML documents into v2."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, MutableMapping


@dataclass
class ConversionWarning:
    message: str
    pointer: str


@dataclass
class ConversionResult:
    document: Dict[str, Any]
    warnings: List[ConversionWarning]


def convert_v1_to_v2(document: Mapping[str, Any]) -> ConversionResult:
    """Convert a v1-style document into a v2-compatible dict."""

    warnings: List[ConversionWarning] = []
    output: Dict[str, Any] = _deep_copy(document)

    meta = output.setdefault("meta", {})
    if meta.get("version") != 2:
        warnings.append(ConversionWarning("meta.version coerced to 2", "/meta/version"))
    meta["version"] = 2

    runtime = output.setdefault("runtime", {})
    if "engine" not in runtime:
        runtime["engine"] = "lc.lcel"
        warnings.append(ConversionWarning("runtime.engine defaulted to lc.lcel", "/runtime/engine"))

    _convert_graph(output.get("graph"), warnings)

    policies = output.setdefault("policies", {})
    if "error_policy" in output:
        warnings.append(ConversionWarning("error_policy moved under policies.error", "/error_policy"))
        policies.setdefault("error", output.pop("error_policy"))

    return ConversionResult(document=output, warnings=warnings)


def _convert_graph(graph: Any, warnings: List[ConversionWarning]) -> None:
    if not isinstance(graph, MutableMapping):
        return
    if "start" in graph and "entry" not in graph:
        graph["entry"] = graph.pop("start")
        warnings.append(ConversionWarning("graph.start renamed to graph.entry", "/graph/entry"))

    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        return
    name_seen = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, MutableMapping):
            continue
        pointer = f"/graph/nodes/{index}"
        if "name" in node and "id" not in node:
            new_id = _slugify(str(node.pop("name")))
            if new_id in name_seen:
                suffix = 1
                candidate = f"{new_id}_{suffix}"
                while candidate in name_seen:
                    suffix += 1
                    candidate = f"{new_id}_{suffix}"
                new_id = candidate
            node["id"] = new_id
            name_seen.add(new_id)
            warnings.append(ConversionWarning("node.name converted to node.id", f"{pointer}/id"))
        if "input" in node and "inputs" not in node:
            node["inputs"] = node.pop("input")
            warnings.append(ConversionWarning("node.input renamed to node.inputs", f"{pointer}/inputs"))
        if "output" in node and "outputs" not in node:
            node["outputs"] = node.pop("output")
            warnings.append(ConversionWarning("node.output renamed to node.outputs", f"{pointer}/outputs"))
        if "component" not in node and "task" in node:
            node["component"] = node.pop("task")
            warnings.append(ConversionWarning("node.task renamed to node.component", f"{pointer}/component"))


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "node"


def _deep_copy(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: _deep_copy(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [_deep_copy(item) for item in obj]
    return obj
