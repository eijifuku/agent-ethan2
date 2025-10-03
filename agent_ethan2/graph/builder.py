"""Graph builder that composes normalized IR into executable node specifications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional, Tuple

from agent_ethan2.graph.errors import GraphBuilderError
from agent_ethan2.ir import (
    NormalizedComponent,
    NormalizedGraphHistory,
    NormalizedGraphNode,
    NormalizedGraphOutput,
    NormalizedIR,
)

NodeCallable = Callable[..., Any]


@dataclass(frozen=True)
class NodeSpec:
    """Executable specification for a single graph node."""

    id: str
    kind: str
    pointer: str
    component_id: Optional[str]
    component: Optional[NodeCallable]
    component_meta: Optional[NormalizedComponent]
    inputs: Mapping[str, str]
    outputs: Mapping[str, str]
    routes: Mapping[str, str]
    next_nodes: Tuple[str, ...]
    config: Mapping[str, Any]


@dataclass(frozen=True)
class GraphDefinition:
    """Executable graph definition derived from the normalized IR."""

    name: Optional[str]
    entrypoint: str
    nodes: Mapping[str, NodeSpec]
    outputs: Tuple[NormalizedGraphOutput, ...]
    policies: Mapping[str, Any]
    history: Optional[NormalizedGraphHistory]
    histories: Mapping[str, Any]  # NormalizedHistory instances


class GraphBuilder:
    """Compose a `GraphDefinition` from normalized IR and resolved factories."""

    SUPPORTED_KINDS = {"component", "llm", "tool", "router", "map", "parallel"}

    def build(self, ir: NormalizedIR, resolved: Mapping[str, Mapping[str, Any]]) -> GraphDefinition:
        components_runtime = resolved.get("components", {})
        providers_runtime = resolved.get("providers", {})
        tools_runtime = resolved.get("tools", {})

        if ir.graph.entry_id not in ir.graph.nodes:
            raise GraphBuilderError(
                "ERR_GRAPH_ENTRY_NOT_FOUND",
                f"Graph entry '{ir.graph.entry_id}' does not exist",
                pointer="/graph/entry",
            )

        nodes: Dict[str, NodeSpec] = {}
        for node_id, node in ir.graph.nodes.items():
            nodes[node_id] = self._build_node(
                node=node,
                ir=ir,
                components_runtime=components_runtime,
                providers_runtime=providers_runtime,
                tools_runtime=tools_runtime,
            )

        return GraphDefinition(
            name=ir.runtime.graph_name,
            entrypoint=ir.graph.entry_id,
            nodes=nodes,
            outputs=ir.graph.outputs,
            policies=ir.policies,
            history=ir.graph.history,
            histories=ir.histories,
        )

    def _build_node(
        self,
        *,
        node: NormalizedGraphNode,
        ir: NormalizedIR,
        components_runtime: Mapping[str, Any],
        providers_runtime: Mapping[str, Any],
        tools_runtime: Mapping[str, Any],
    ) -> NodeSpec:
        component_meta: Optional[NormalizedComponent] = None
        component_callable: Optional[NodeCallable] = None

        if node.component_id is not None:
            component_meta = ir.components.get(node.component_id)
            if component_meta is None:
                raise GraphBuilderError(
                    "ERR_NODE_TYPE",
                    f"Component '{node.component_id}' referenced by node '{node.id}' is undefined",
                    pointer=node.pointer,
                )
            component_callable = components_runtime.get(node.component_id)
            if component_callable is None:
                raise GraphBuilderError(
                    "ERR_COMPONENT_IMPORT",
                    f"Component '{node.component_id}' has not been materialized",
                    pointer=node.pointer,
                )

        kind = self._determine_kind(node, component_meta)
        if kind not in self.SUPPORTED_KINDS:
            raise GraphBuilderError(
                "ERR_NODE_TYPE",
                f"Node '{node.id}' has unsupported kind '{kind}'",
                pointer=node.pointer,
            )

        if kind in {"llm", "tool"}:
            if component_meta is None:
                raise GraphBuilderError(
                    "ERR_NODE_TYPE",
                    f"Node '{node.id}' of kind '{kind}' requires a component",
                    pointer=node.pointer,
                )
            if component_meta.provider_id is None:
                raise GraphBuilderError(
                    "ERR_PROVIDER_DEFAULT_MISSING",
                    f"Node '{node.id}' requires a provider but none was resolved",
                    pointer=node.pointer,
                )
            if component_meta.provider_id not in providers_runtime:
                raise GraphBuilderError(
                    "ERR_PROVIDER_DEFAULT_MISSING",
                    f"Provider '{component_meta.provider_id}' for node '{node.id}' is not available",
                    pointer=node.pointer,
                )

        if kind == "tool" and component_meta is not None:
            if component_meta.tool_id is None:
                raise GraphBuilderError(
                    "ERR_TOOL_NOT_FOUND",
                    f"Node '{node.id}' of kind 'tool' does not reference a tool",
                    pointer=node.pointer,
                )
            if component_meta.tool_id not in tools_runtime:
                raise GraphBuilderError(
                    "ERR_TOOL_NOT_FOUND",
                    f"Tool '{component_meta.tool_id}' required by node '{node.id}' is not available",
                    pointer=node.pointer,
                )

        if kind == "router" and not node.routes:
            raise GraphBuilderError(
                "ERR_ROUTER_NO_MATCH",
                f"Router node '{node.id}' does not define any routes",
                pointer=node.pointer,
            )

        if kind == "map" and component_meta is None:
            raise GraphBuilderError(
                "ERR_MAP_BODY_NOT_FOUND",
                f"Map node '{node.id}' requires a component",
                pointer=node.pointer,
            )

        # For map/parallel nodes, merge component config with node config
        # Component config provides defaults (collection, failure_mode, etc.)
        merged_config = dict(node.config)
        if kind in {"map", "parallel"} and component_meta is not None:
            for key, value in component_meta.config.items():
                if key not in merged_config:
                    merged_config[key] = value

        return NodeSpec(
            id=node.id,
            kind=kind,
            pointer=node.pointer,
            component_id=node.component_id,
            component=component_callable,
            component_meta=component_meta,
            inputs=node.inputs,
            outputs=node.outputs,
            routes=node.routes,
            next_nodes=node.next_nodes,
            config=merged_config,
        )

    @staticmethod
    def _determine_kind(node: NormalizedGraphNode, component_meta: Optional[NormalizedComponent]) -> str:
        node_type = node.type.lower()
        if node_type in {"llm", "tool", "router", "map", "parallel"}:
            return node_type
        if node_type in {"component", "node", "task"} and component_meta is not None:
            component_type = component_meta.type.lower()
            if component_type in {"llm", "tool", "router", "map", "parallel"}:
                return component_type
        return node_type
