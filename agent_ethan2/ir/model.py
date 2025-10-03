"""IR data structures and normalization utilities."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple
import copy
import re


Pointer = str


@dataclass(frozen=True)
class NormalizationWarning:
    """Represents a non-blocking compatibility warning emitted during normalization."""

    code: str
    message: str
    pointer: Pointer


class IRNormalizationError(ValueError):
    """Raised when the YAML document cannot be normalized into the target IR."""

    def __init__(self, code: str, message: str, pointer: Pointer) -> None:
        self.code = code
        self.pointer = pointer
        super().__init__(f"[{code}] {message} at {pointer}")


@dataclass(frozen=True)
class NormalizedProvider:
    id: str
    type: str
    config: Mapping[str, Any]


@dataclass(frozen=True)
class NormalizedTool:
    id: str
    type: str
    provider_id: Optional[str]
    config: Mapping[str, Any]


@dataclass(frozen=True)
class NormalizedComponent:
    id: str
    type: str
    provider_id: Optional[str]
    tool_id: Optional[str]
    inputs: Mapping[str, str]
    outputs: Mapping[str, str]
    config: Mapping[str, Any]


@dataclass(frozen=True)
class NormalizedGraphNode:
    id: str
    type: str
    component_id: Optional[str]
    next_nodes: Tuple[str, ...]
    routes: Mapping[str, str]
    inputs: Mapping[str, str]
    outputs: Mapping[str, str]
    config: Mapping[str, Any]
    pointer: str


@dataclass(frozen=True)
class NormalizedGraphOutput:
    key: str
    node_id: str
    output: str


@dataclass(frozen=True)
class NormalizedHistory:
    """Configuration for a conversation history instance."""
    id: str
    backend: Mapping[str, Any]
    system_message: Optional[str]


@dataclass(frozen=True)
class NormalizedGraphHistory:
    """Configuration for conversation history management (deprecated)."""
    enabled: bool
    input_key: str
    output_key: str
    max_turns: Optional[int]
    system_message: Optional[str]


@dataclass(frozen=True)
class NormalizedGraph:
    entry_id: str
    nodes: Mapping[str, NormalizedGraphNode]
    outputs: Tuple[NormalizedGraphOutput, ...]
    history: Optional[NormalizedGraphHistory]


@dataclass(frozen=True)
class NormalizedRuntime:
    engine: str
    graph_name: Optional[str]
    defaults: Mapping[str, Any]
    default_provider_id: Optional[str]


@dataclass(frozen=True)
class NormalizedIR:
    meta: Mapping[str, Any]
    runtime: NormalizedRuntime
    providers: Mapping[str, NormalizedProvider]
    tools: Mapping[str, NormalizedTool]
    components: Mapping[str, NormalizedComponent]
    graph: NormalizedGraph
    policies: Mapping[str, Any]
    histories: Mapping[str, NormalizedHistory]


@dataclass(frozen=True)
class NormalizationResult:
    ir: NormalizedIR
    warnings: Tuple[NormalizationWarning, ...]


_VALID_NODE_NAME = re.compile(r"^[a-z0-9_]+$")


def normalize_document(document: Mapping[str, Any]) -> NormalizationResult:
    """Normalize a validated YAML document into the runtime IR.

    Parameters
    ----------
    document:
        Mapping that passed the schema validation in stage A1.

    Returns
    -------
    NormalizationResult
        The structured IR along with any compatibility warnings.
    """

    if not isinstance(document, MutableMapping):
        raise IRNormalizationError("ERR_IR_INPUT_TYPE", "Document must be a mapping", "/")

    content = copy.deepcopy(document)
    warnings: List[NormalizationWarning] = []

    meta = _normalize_meta(content.get("meta", {}))

    providers = _normalize_providers(content.get("providers", []))

    runtime, default_provider_id = _normalize_runtime(content.get("runtime", {}), providers, warnings)

    tools = _normalize_tools(content.get("tools", []), providers, warnings)

    components = _normalize_components(
        content.get("components", []),
        providers,
        tools,
        default_provider_id,
        warnings,
    )

    graph = _normalize_graph(content.get("graph", {}), components, warnings)

    policies = _normalize_policies(content.get("policies", {}), warnings)
    
    histories = _normalize_histories(content.get("histories", []), warnings)

    ir = NormalizedIR(
        meta=meta,
        runtime=runtime,
        providers=providers,
        tools=tools,
        components=components,
        graph=graph,
        policies=policies,
        histories=histories,
    )

    return NormalizationResult(ir=ir, warnings=tuple(warnings))


def _normalize_meta(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(meta, MutableMapping):
        raise IRNormalizationError("ERR_META_TYPE", "meta must be a mapping", "/meta")
    return dict(meta)


def _normalize_providers(providers: Any) -> Dict[str, NormalizedProvider]:
    if not isinstance(providers, Sequence):
        raise IRNormalizationError("ERR_PROVIDERS_TYPE", "providers must be a list", "/providers")
    normalized: Dict[str, NormalizedProvider] = {}
    for idx, raw in enumerate(providers):
        if not isinstance(raw, MutableMapping):
            raise IRNormalizationError("ERR_PROVIDER_TYPE", "provider entry must be a mapping", f"/providers/{idx}")
        pid = raw.get("id")
        if not isinstance(pid, str):
            raise IRNormalizationError("ERR_PROVIDER_ID", "provider id must be a string", f"/providers/{idx}/id")
        ptype = raw.get("type")
        if not isinstance(ptype, str):
            raise IRNormalizationError("ERR_PROVIDER_TYPE_FIELD", "provider type must be a string", f"/providers/{idx}/type")
        config = raw.get("config") if isinstance(raw.get("config"), MutableMapping) else {}
        normalized[pid] = NormalizedProvider(id=pid, type=ptype, config=dict(config))
    return normalized


def _normalize_runtime(
    runtime: Any,
    providers: Mapping[str, NormalizedProvider],
    warnings: List[NormalizationWarning],
) -> Tuple[NormalizedRuntime, Optional[str]]:
    if not isinstance(runtime, MutableMapping):
        raise IRNormalizationError("ERR_RUNTIME_TYPE", "runtime must be a mapping", "/runtime")
    engine = runtime.get("engine")
    if not isinstance(engine, str):
        raise IRNormalizationError("ERR_RUNTIME_ENGINE", "runtime.engine must be a string", "/runtime/engine")
    graph_name = runtime.get("graph_name") if isinstance(runtime.get("graph_name"), str) else None
    defaults = runtime.get("defaults") if isinstance(runtime.get("defaults"), MutableMapping) else {}
    default_provider_id = defaults.get("provider") if isinstance(defaults.get("provider"), str) else None
    if default_provider_id and default_provider_id not in providers:
        raise IRNormalizationError(
            "ERR_RUNTIME_DEFAULT_PROVIDER",
            f"Default provider '{default_provider_id}' is not defined",
            "/runtime/defaults/provider",
        )
    normalized_runtime = NormalizedRuntime(
        engine=engine,
        graph_name=graph_name,
        defaults=dict(defaults),
        default_provider_id=default_provider_id,
    )
    return normalized_runtime, default_provider_id


def _normalize_tools(
    tools: Any,
    providers: Mapping[str, NormalizedProvider],
    warnings: List[NormalizationWarning],
) -> Dict[str, NormalizedTool]:
    if tools is None:
        return {}
    if not isinstance(tools, Sequence):
        raise IRNormalizationError("ERR_TOOLS_TYPE", "tools must be a list", "/tools")
    normalized: Dict[str, NormalizedTool] = {}
    for idx, raw in enumerate(tools):
        if not isinstance(raw, MutableMapping):
            raise IRNormalizationError("ERR_TOOL_TYPE", "tool entry must be a mapping", f"/tools/{idx}")
        tid = raw.get("id")
        if not isinstance(tid, str):
            raise IRNormalizationError("ERR_TOOL_ID", "tool id must be a string", f"/tools/{idx}/id")
        ttype = raw.get("type")
        if not isinstance(ttype, str):
            raise IRNormalizationError("ERR_TOOL_TYPE_FIELD", "tool type must be a string", f"/tools/{idx}/type")
        provider_id = raw.get("provider") if isinstance(raw.get("provider"), str) else None
        if provider_id and provider_id not in providers:
            raise IRNormalizationError(
                "ERR_TOOL_PROVIDER_NOT_FOUND",
                f"Tool references undefined provider '{provider_id}'",
                f"/tools/{idx}/provider",
            )
        config = raw.get("config") if isinstance(raw.get("config"), MutableMapping) else {}
        normalized[tid] = NormalizedTool(
            id=tid,
            type=ttype,
            provider_id=provider_id,
            config=dict(config),
        )
    return normalized


def _normalize_components(
    components: Any,
    providers: Mapping[str, NormalizedProvider],
    tools: Mapping[str, NormalizedTool],
    default_provider_id: Optional[str],
    warnings: List[NormalizationWarning],
) -> Dict[str, NormalizedComponent]:
    if components is None:
        return {}
    if not isinstance(components, Sequence):
        raise IRNormalizationError("ERR_COMPONENTS_TYPE", "components must be a list", "/components")
    normalized: Dict[str, NormalizedComponent] = {}
    for idx, raw in enumerate(components):
        if not isinstance(raw, MutableMapping):
            raise IRNormalizationError("ERR_COMPONENT_TYPE", "component entry must be a mapping", f"/components/{idx}")
        cid = raw.get("id")
        if not isinstance(cid, str):
            raise IRNormalizationError("ERR_COMPONENT_ID", "component id must be a string", f"/components/{idx}/id")
        ctype = raw.get("type")
        if not isinstance(ctype, str):
            raise IRNormalizationError("ERR_COMPONENT_TYPE_FIELD", "component type must be a string", f"/components/{idx}/type")
        provider_id = raw.get("provider") if isinstance(raw.get("provider"), str) else default_provider_id
        if provider_id and provider_id not in providers:
            raise IRNormalizationError(
                "ERR_COMPONENT_PROVIDER_NOT_FOUND",
                f"Component references undefined provider '{provider_id}'",
                f"/components/{idx}/provider",
            )
        if provider_id is None:
            warnings.append(
                NormalizationWarning(
                    code="WARN_COMPONENT_PROVIDER_INFER",
                    message="Component missing provider; leaving provider unset",
                    pointer=f"/components/{idx}",
                )
            )
        tool_id = raw.get("tool") if isinstance(raw.get("tool"), str) else None
        if tool_id and tool_id not in tools:
            raise IRNormalizationError(
                "ERR_COMPONENT_TOOL_NOT_FOUND",
                f"Component references undefined tool '{tool_id}'",
                f"/components/{idx}/tool",
            )
        inputs = raw.get("inputs") if isinstance(raw.get("inputs"), MutableMapping) else None
        outputs = raw.get("outputs") if isinstance(raw.get("outputs"), MutableMapping) else None
        if inputs is None:
            warnings.append(
                NormalizationWarning(
                    code="WARN_V1_COMPONENT_INPUTS_OPTIONAL",
                    message="Component inputs missing; defaulting to empty mapping",
                    pointer=f"/components/{idx}",
                )
            )
            inputs = {}
        if outputs is None:
            warnings.append(
                NormalizationWarning(
                    code="WARN_V1_COMPONENT_OUTPUTS_OPTIONAL",
                    message="Component outputs missing; defaulting to empty mapping",
                    pointer=f"/components/{idx}",
                )
            )
            outputs = {}
        config = raw.get("config") if isinstance(raw.get("config"), MutableMapping) else {}
        normalized[cid] = NormalizedComponent(
            id=cid,
            type=ctype,
            provider_id=provider_id,
            tool_id=tool_id,
            inputs=dict(inputs),
            outputs=dict(outputs),
            config=dict(config),
        )
    return normalized


def _normalize_graph(
    graph: Any,
    components: Mapping[str, NormalizedComponent],
    warnings: List[NormalizationWarning],
) -> NormalizedGraph:
    if not isinstance(graph, MutableMapping):
        raise IRNormalizationError("ERR_GRAPH_TYPE", "graph must be a mapping", "/graph")
    entry_id = graph.get("entry")
    if not isinstance(entry_id, str):
        raise IRNormalizationError("ERR_GRAPH_ENTRY_NOT_FOUND", "Graph entry must reference a node id", "/graph/entry")

    raw_nodes = graph.get("nodes")
    if not isinstance(raw_nodes, Sequence) or not raw_nodes:
        raise IRNormalizationError("ERR_GRAPH_NODES", "graph.nodes must be a non-empty list", "/graph/nodes")

    nodes: Dict[str, NormalizedGraphNode] = {}
    node_pointer: Dict[str, str] = {}
    connectivity: Dict[str, Tuple[str, ...]] = {}
    for idx, raw in enumerate(raw_nodes):
        if not isinstance(raw, MutableMapping):
            raise IRNormalizationError("ERR_GRAPH_NODE_TYPE", "graph node must be a mapping", f"/graph/nodes/{idx}")
        node_id = raw.get("id")
        if not isinstance(node_id, str):
            raise IRNormalizationError("ERR_NODE_ID", "graph node id must be a string", f"/graph/nodes/{idx}/id")
        pointer = f"/graph/nodes/{idx}"
        node_pointer[node_id] = pointer
        node_type = raw.get("type") if isinstance(raw.get("type"), str) else "node"
        component_id = raw.get("component") if isinstance(raw.get("component"), str) else None
        if component_id and component_id not in components:
            raise IRNormalizationError(
                "ERR_NODE_COMPONENT_NOT_FOUND",
                f"Node references undefined component '{component_id}'",
                f"/graph/nodes/{idx}/component",
            )
        inputs = raw.get("inputs") if isinstance(raw.get("inputs"), MutableMapping) else {}
        outputs = raw.get("outputs") if isinstance(raw.get("outputs"), MutableMapping) else {}
        config = raw.get("config") if isinstance(raw.get("config"), MutableMapping) else {}

        next_raw = raw.get("next")
        next_nodes = tuple(_extract_targets(next_raw))
        routes: Dict[str, str] = {}
        if isinstance(next_raw, MutableMapping):
            for key, value in next_raw.items():
                if isinstance(value, str):
                    routes[str(key)] = value
        connectivity[node_id] = next_nodes
        nodes[node_id] = NormalizedGraphNode(
            id=node_id,
            type=node_type,
            component_id=component_id,
            next_nodes=next_nodes,
            routes=dict(routes),
            inputs=dict(inputs),
            outputs=dict(outputs),
            config=dict(config),
            pointer=pointer,
        )
        if not _VALID_NODE_NAME.match(node_id):
            warnings.append(
                NormalizationWarning(
                    code="WARN_V1_NODE_NAMING",
                    message="Node id contains characters outside snake_case; consider renaming",
                    pointer=f"/graph/nodes/{idx}/id",
                )
            )

    if entry_id not in nodes:
        raise IRNormalizationError(
            "ERR_GRAPH_ENTRY_NOT_FOUND",
            f"Graph entry '{entry_id}' does not match any defined node",
            "/graph/entry",
        )

    for node_id, targets in connectivity.items():
        for target in targets:
            if target not in nodes:
                raise IRNormalizationError(
                    "ERR_EDGE_ENDPOINT_INVALID",
                    f"Node '{node_id}' references undefined target '{target}'",
                    f"{node_pointer[node_id]}/next",
                )

    outputs_raw = graph.get("outputs")
    graph_outputs: List[NormalizedGraphOutput] = []
    if outputs_raw is not None:
        if not isinstance(outputs_raw, Sequence):
            raise IRNormalizationError("ERR_GRAPH_OUTPUTS_TYPE", "graph.outputs must be a list", "/graph/outputs")
        for idx, raw in enumerate(outputs_raw):
            if not isinstance(raw, MutableMapping):
                raise IRNormalizationError("ERR_GRAPH_OUTPUT_TYPE", "graph output must be a mapping", f"/graph/outputs/{idx}")
            key = raw.get("key")
            node_id = raw.get("node")
            output = raw.get("output")
            if not isinstance(key, str):
                raise IRNormalizationError("ERR_GRAPH_OUTPUT_KEY", "graph output key must be a string", f"/graph/outputs/{idx}/key")
            if not isinstance(node_id, str):
                raise IRNormalizationError("ERR_GRAPH_OUTPUT_NODE", "graph output node must be a string", f"/graph/outputs/{idx}/node")
            if node_id not in nodes:
                raise IRNormalizationError(
                    "ERR_EDGE_ENDPOINT_INVALID",
                    f"Graph output references undefined node '{node_id}'",
                    f"/graph/outputs/{idx}/node",
                )
            if not isinstance(output, str):
                raise IRNormalizationError("ERR_GRAPH_OUTPUT_NAME", "graph output name must be a string", f"/graph/outputs/{idx}/output")
            graph_outputs.append(
                NormalizedGraphOutput(
                    key=key,
                    node_id=node_id,
                    output=output,
                )
            )

    reachable = _collect_reachable(entry_id, connectivity)
    for node_id, pointer in node_pointer.items():
        if node_id not in reachable:
            warnings.append(
                NormalizationWarning(
                    code="WARN_GRAPH_NODE_UNREACHABLE",
                    message=f"Node '{node_id}' is not reachable from entry '{entry_id}'",
                    pointer=pointer,
                )
            )

    # Normalize conversation history configuration
    history_config: Optional[NormalizedGraphHistory] = None
    history_raw = graph.get("history")
    if history_raw is not None and isinstance(history_raw, MutableMapping):
        enabled = bool(history_raw.get("enabled", False))
        input_key = str(history_raw.get("input_key", "chat_history"))
        output_key = str(history_raw.get("output_key", "chat_history"))
        max_turns = history_raw.get("max_turns")
        if max_turns is not None and not isinstance(max_turns, int):
            max_turns = None
        system_message = history_raw.get("system_message")
        if system_message is not None and not isinstance(system_message, str):
            system_message = None
        
        history_config = NormalizedGraphHistory(
            enabled=enabled,
            input_key=input_key,
            output_key=output_key,
            max_turns=max_turns,
            system_message=system_message,
        )

    return NormalizedGraph(
        entry_id=entry_id,
        nodes=nodes,
        outputs=tuple(graph_outputs),
        history=history_config,
    )


def _normalize_policies(policies: Any, warnings: List[NormalizationWarning]) -> Mapping[str, Any]:
    if policies is None:
        return {}
    if not isinstance(policies, MutableMapping):
        raise IRNormalizationError("ERR_POLICIES_TYPE", "policies must be a mapping", "/policies")
    if "error_policy" in policies:  # legacy surface
        warnings.append(
            NormalizationWarning(
                code="WARN_V1_ERROR_POLICY",
                message="Found legacy error_policy; migrate to policies.error",
                pointer="/policies/error_policy",
            )
        )
    return dict(policies)


def _normalize_histories(
    histories_raw: Any,
    warnings: List[NormalizationWarning],
) -> Mapping[str, NormalizedHistory]:
    """Normalize conversation history configurations."""
    if not isinstance(histories_raw, Sequence):
        return {}
    
    histories: Dict[str, NormalizedHistory] = {}
    
    for idx, raw in enumerate(histories_raw):
        if not isinstance(raw, MutableMapping):
            raise IRNormalizationError(
                "ERR_HISTORY_TYPE",
                "History must be a mapping",
                f"/histories/{idx}"
            )
        
        history_id = raw.get("id")
        if not isinstance(history_id, str):
            raise IRNormalizationError(
                "ERR_HISTORY_ID",
                "History id must be a string",
                f"/histories/{idx}/id"
            )
        
        if history_id in histories:
            raise IRNormalizationError(
                "ERR_HISTORY_DUPLICATE",
                f"Duplicate history id '{history_id}'",
                f"/histories/{idx}/id"
            )
        
        backend = raw.get("backend")
        if backend is not None and not isinstance(backend, MutableMapping):
            raise IRNormalizationError(
                "ERR_HISTORY_BACKEND_TYPE",
                "History backend must be a mapping",
                f"/histories/{idx}/backend"
            )
        
        # Default backend config
        backend_config = dict(backend) if backend else {"type": "memory"}
        
        system_message = raw.get("system_message")
        if system_message is not None and not isinstance(system_message, str):
            system_message = None
        
        histories[history_id] = NormalizedHistory(
            id=history_id,
            backend=backend_config,
            system_message=system_message,
        )
    
    return histories


def _extract_targets(raw: Any) -> Iterable[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Sequence):
        return [item for item in raw if isinstance(item, str)]
    if isinstance(raw, MutableMapping):
        return [value for value in raw.values() if isinstance(value, str)]
    return []


def _collect_reachable(entry_id: str, connectivity: Mapping[str, Tuple[str, ...]]) -> set[str]:
    reachable: set[str] = set()
    queue: deque[str] = deque([entry_id])
    while queue:
        node_id = queue.popleft()
        if node_id in reachable:
            continue
        reachable.add(node_id)
        for target in connectivity.get(node_id, ()):  # type: ignore[arg-type]
            if target not in reachable:
                queue.append(target)
    return reachable
