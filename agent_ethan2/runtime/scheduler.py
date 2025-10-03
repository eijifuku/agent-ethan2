"""Async graph scheduler and runtime utilities (B1/B2)."""

from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Sequence

from agent_ethan2.graph import GraphDefinition, GraphExecutionError, NodeSpec
from agent_ethan2.policy import RateLimiterManager, RetryManager
from agent_ethan2.policy.permissions import PermissionManager
from agent_ethan2.runtime.context import CancelToken, ComponentContext, build_component_context
from agent_ethan2.runtime.events import EventEmitter, ensure_emitter


class _RunEventEmitter:
    """Wraps an emitter to ensure run metadata and timestamps are applied."""

    def __init__(self, emitter: EventEmitter, run_id: str) -> None:
        self._emitter = emitter
        self._run_id = run_id

    @property
    def run_id(self) -> str:
        return self._run_id

    def emit(self, event: str, **payload: Any) -> None:
        payload.setdefault("run_id", self._run_id)
        payload.setdefault("ts", time.time())
        self._emitter.emit(event, **payload)


@dataclass(frozen=True)
class NodeRuntimeState:
    """Captured state of a node after execution."""

    outputs: Mapping[str, Any]
    result: Any


@dataclass(frozen=True)
class GraphResult:
    """Result of executing a graph."""

    outputs: Mapping[str, Any]
    node_states: Mapping[str, NodeRuntimeState]
    run_id: str


@dataclass
class _GraphState:
    inputs: Mapping[str, Any]
    node_states: MutableMapping[str, NodeRuntimeState]


class Scheduler:
    """Executes graph definitions with async scheduling semantics."""

    def __init__(self) -> None:
        pass

    async def run(
        self,
        definition: GraphDefinition,
        *,
        inputs: Mapping[str, Any],
        event_emitter: Optional[EventEmitter] = None,
        timeout: Optional[float] = None,
        cancel_on_error: bool = True,
        run_id: Optional[str] = None,
        deadline: Optional[float] = None,
        registries: Optional[Mapping[str, Any]] = None,
    ) -> GraphResult:
        emitter = ensure_emitter(event_emitter)
        state = _GraphState(inputs=inputs, node_states={})

        run_id_value = run_id or uuid.uuid4().hex
        run_emitter = _RunEventEmitter(emitter, run_id_value)
        cancel_token = CancelToken()
        deadline_at = deadline
        registries = dict(registries or {})
        
        # Add histories to registries if available in definition
        if hasattr(definition, 'histories') and definition.histories:
            registries['histories'] = definition.histories

        retry_manager = RetryManager(definition.policies.get("retry", {}), run_emitter)
        rate_manager = RateLimiterManager(definition.policies.get("rate_limit", {}), run_emitter)
        permission_manager = PermissionManager(definition.policies.get("permissions", {}))

        closables = self._collect_closables(definition)

        run_emitter.emit(
            "graph.start",
            graph_name=definition.name,
            entrypoint=definition.entrypoint,
        )

        try:
            execution = self._execute(
                definition,
                state,
                run_emitter,
                retry_manager=retry_manager,
                rate_manager=rate_manager,
                cancel_on_error=cancel_on_error,
                run_id=run_id_value,
                permission_manager=permission_manager,
                cancel_token=cancel_token,
                deadline=deadline_at,
                registries=registries,
            )
            if timeout is not None:
                result = await asyncio.wait_for(execution, timeout=timeout)
            else:
                result = await execution
            run_emitter.emit(
                "graph.finish",
                graph_name=definition.name,
                status="success",
                outputs=result.outputs,
            )
            return GraphResult(outputs=result.outputs, node_states=result.node_states, run_id=run_id_value)
        except asyncio.TimeoutError as exc:
            cancel_token.cancel()
            run_emitter.emit(
                "timeout",
                graph_name=definition.name,
                timeout=timeout,
            )
            run_emitter.emit(
                "graph.finish",
                graph_name=definition.name,
                status="timeout",
            )
            raise TimeoutError(f"Graph execution exceeded {timeout:.2f}s") from exc
        except asyncio.CancelledError:
            cancel_token.cancel()
            run_emitter.emit(
                "cancelled",
                graph_name=definition.name,
            )
            run_emitter.emit(
                "graph.finish",
                graph_name=definition.name,
                status="cancelled",
            )
            raise
        except GraphExecutionError as exc:
            cancel_token.cancel()
            run_emitter.emit(
                "graph.finish",
                graph_name=definition.name,
                status="error",
                error_code=exc.code,
            )
            raise
        except Exception:
            cancel_token.cancel()
            run_emitter.emit(
                "graph.finish",
                graph_name=definition.name,
                status="error",
            )
            raise
        finally:
            await self._close_components(closables, run_emitter)

    async def _execute(
        self,
        definition: GraphDefinition,
        state: _GraphState,
        emitter: EventEmitter,
        *,
        retry_manager: RetryManager,
        rate_manager: RateLimiterManager,
        cancel_on_error: bool,
        run_id: str,
        permission_manager: PermissionManager,
        cancel_token: CancelToken,
        deadline: Optional[float],
        registries: Mapping[str, Any],
    ) -> GraphResult:
        pending = [definition.entrypoint]
        visited = set()

        while pending:
            node_id = pending.pop(0)
            if node_id in visited:
                continue
            spec = definition.nodes.get(node_id)
            if spec is None:
                raise GraphExecutionError(
                    "ERR_EDGE_ENDPOINT_INVALID",
                    f"Node '{node_id}' referenced in graph is not defined",
                    pointer="/graph/nodes",
                )
            next_nodes = await self._run_node(
                definition,
                spec,
                state,
                emitter,
                retry_manager=retry_manager,
                rate_manager=rate_manager,
                graph_name=definition.name,
                cancel_on_error=cancel_on_error,
                permission_manager=permission_manager,
                cancel_token=cancel_token,
                deadline=deadline,
                registries=registries,
            )
            visited.add(node_id)
            for target in next_nodes:
                if target not in definition.nodes:
                    raise GraphExecutionError(
                        "ERR_EDGE_ENDPOINT_INVALID",
                        f"Node '{node_id}' references undefined target '{target}'",
                        pointer=spec.pointer,
                    )
                pending.append(target)

        result_outputs = self._collect_outputs(definition, state)
        return GraphResult(outputs=result_outputs, node_states=dict(state.node_states), run_id=run_id)

    async def _run_node(
        self,
        definition: GraphDefinition,
        spec: NodeSpec,
        state: _GraphState,
        emitter: EventEmitter,
        *,
        retry_manager: RetryManager,
        rate_manager: RateLimiterManager,
        graph_name: Optional[str],
        cancel_on_error: bool,
        permission_manager: PermissionManager,
        cancel_token: CancelToken,
        deadline: Optional[float],
        registries: Mapping[str, Any],
    ) -> tuple[str, ...]:
        start_wall = time.time()
        emitter.emit(
            "node.start",
            node_id=spec.id,
            kind=spec.kind,
            started_at=start_wall,
            graph_name=graph_name,
        )
        start_ts = perf_counter()

        try:
            if spec.kind == "map":
                outputs, result = await self._execute_map(
                    spec,
                    state,
                    emitter,
                    graph_name,
                    retry_manager=retry_manager,
                    rate_manager=rate_manager,
                    permission_manager=permission_manager,
                    cancel_token=cancel_token,
                    deadline=deadline,
                    registries=registries,
                )
            elif spec.kind == "parallel":
                outputs, result = await self._execute_parallel(
                    definition,
                    spec,
                    state,
                    emitter,
                    graph_name,
                    retry_manager=retry_manager,
                    rate_manager=rate_manager,
                    permission_manager=permission_manager,
                    cancel_token=cancel_token,
                    deadline=deadline,
                    registries=registries,
                )
            else:
                node_state = await self._invoke_component_spec(
                    spec,
                    state,
                    emitter,
                    graph_name,
                    retry_manager=retry_manager,
                    rate_manager=rate_manager,
                    permission_manager=permission_manager,
                    cancel_token=cancel_token,
                    deadline=deadline,
                    registries=registries,
                )
                outputs = dict(node_state.outputs)
                result = node_state.result

            state.node_states[spec.id] = NodeRuntimeState(outputs=outputs, result=result)
            duration_ms = (perf_counter() - start_ts) * 1000.0
            emitter.emit(
                "node.finish",
                node_id=spec.id,
                kind=spec.kind,
                status="success",
                duration_ms=duration_ms,
                outputs=outputs,
                started_at=start_wall,
                graph_name=graph_name,
            )
        except GraphExecutionError as exc:
            duration_ms = (perf_counter() - start_ts) * 1000.0
            emitter.emit(
                "error.raised",
                node_id=spec.id,
                kind=spec.kind,
                message=str(exc),
            )
            emitter.emit(
                "node.finish",
                node_id=spec.id,
                kind=spec.kind,
                status="error",
                duration_ms=duration_ms,
                outputs={},
                started_at=start_wall,
                graph_name=graph_name,
            )
            cancel_token.cancel()
            raise
        except Exception as exc:
            duration_ms = (perf_counter() - start_ts) * 1000.0
            emitter.emit(
                "error.raised",
                node_id=spec.id,
                kind=spec.kind,
                message=str(exc),
            )
            emitter.emit(
                "node.finish",
                node_id=spec.id,
                kind=spec.kind,
                status="error",
                duration_ms=duration_ms,
                outputs={},
                started_at=start_wall,
                graph_name=graph_name,
            )
            if cancel_on_error:
                cancel_token.cancel()
                raise GraphExecutionError("ERR_NODE_RUNTIME", str(exc), pointer=spec.pointer) from exc
            state.node_states[spec.id] = NodeRuntimeState(outputs={}, result=None)
            return tuple()

        return self._select_next(spec, state)

    def _prepare_inputs(
        self,
        spec: NodeSpec,
        state: _GraphState,
        *,
        loop_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        component_meta = spec.component_meta
        if component_meta is None:
            return {}
        resolved: Dict[str, Any] = {}
        for name, expression in component_meta.inputs.items():
            resolved[name] = self._resolve_expression(expression, state, loop_context=loop_context)
        return resolved

    def _prepare_outputs(self, spec: NodeSpec, result: Any) -> Dict[str, Any]:
        component_meta = spec.component_meta
        if component_meta is None:
            return {}
        outputs: Dict[str, Any] = {}
        for name, expression in component_meta.outputs.items():
            outputs[name] = self._resolve_result_expression(expression, result)
        return outputs

    def _make_state_view(self, state: _GraphState) -> Dict[str, Any]:
        return {
            "graph": {"inputs": state.inputs},
            "nodes": {node_id: node_state.outputs for node_id, node_state in state.node_states.items()},
        }

    def _select_next(self, spec: NodeSpec, state: _GraphState) -> tuple[str, ...]:
        if spec.kind == "router":
            node_state = state.node_states.get(spec.id)
            if node_state is None:
                raise GraphExecutionError(
                    "ERR_ROUTER_NO_MATCH",
                    f"Router node '{spec.id}' did not produce a state",
                    pointer=spec.pointer,
                )
            route_value = node_state.outputs.get("route")
            if route_value is None:
                raise GraphExecutionError(
                    "ERR_ROUTER_NO_MATCH",
                    f"Router node '{spec.id}' did not produce a route output",
                    pointer=spec.pointer,
                )
            route_key = str(route_value)
            if route_key not in spec.routes:
                default_target = spec.routes.get("default")
                if default_target is None:
                    raise GraphExecutionError(
                        "ERR_ROUTER_NO_MATCH",
                        f"Router node '{spec.id}' produced unknown route '{route_key}'",
                        pointer=spec.pointer,
                    )
                return (default_target,)
            return (spec.routes[route_key],)
        return spec.next_nodes

    async def _execute_map(
        self,
        spec: NodeSpec,
        state: _GraphState,
        emitter: EventEmitter,
        graph_name: Optional[str],
        *,
        retry_manager: RetryManager,
        rate_manager: RateLimiterManager,
        permission_manager: PermissionManager,
        cancel_token: CancelToken,
        deadline: Optional[float],
        registries: Mapping[str, Any],
    ) -> tuple[Dict[str, Any], Any]:
        if spec.component is None or spec.component_meta is None:
            raise GraphExecutionError(
                "ERR_MAP_BODY_NOT_FOUND",
                f"Map node '{spec.id}' is missing a component",
                pointer=spec.pointer,
            )

        collection_expr = spec.config.get("collection")
        items = self._resolve_expression(collection_expr, state)
        if not isinstance(items, (list, tuple)):
            raise GraphExecutionError(
                "ERR_MAP_OVER_NOT_ARRAY",
                f"Map node '{spec.id}' requires array-like input",
                pointer=spec.pointer,
            )

        failure_mode = str(spec.config.get("failure_mode", "fail_fast")).lower()
        ordered = bool(spec.config.get("ordered", True))
        result_key = str(spec.config.get("result_key", "results"))

        results: list[tuple[int, Mapping[str, Any]]] = []
        errors: list[Dict[str, Any]] = []

        for index, item in enumerate(items):
            loop_context = {"map_item": item, "map_index": index}
            try:
                iteration_state = await self._invoke_component_spec(
                    spec,
                    state,
                    emitter,
                    graph_name,
                    loop_context=loop_context,
                    emit_event=False,
                    retry_manager=retry_manager,
                    rate_manager=rate_manager,
                    permission_manager=permission_manager,
                    cancel_token=cancel_token,
                    deadline=deadline,
                    registries=registries,
                )
                results.append((index, iteration_state.outputs))
            except Exception as exc:
                emitter.emit(
                    "error.raised",
                    node_id=spec.id,
                    kind=spec.kind,
                    iteration=index,
                    message=str(exc),
                )
                if failure_mode == "fail_fast":
                    raise GraphExecutionError(
                        "ERR_NODE_RUNTIME",
                        f"Map iteration {index} failed: {exc}",
                        pointer=spec.pointer,
                    ) from exc
                if failure_mode == "collect_errors":
                    errors.append({"index": index, "error": str(exc)})
                    continue
                if failure_mode == "skip_failed":
                    continue
                raise

        if ordered:
            results.sort(key=lambda pair: pair[0])

        mapped_results = [mapping for _, mapping in results]
        outputs: Dict[str, Any] = {result_key: mapped_results}
        outputs["errors"] = errors
        return outputs, mapped_results

    async def _execute_parallel(
        self,
        definition: GraphDefinition,
        spec: NodeSpec,
        state: _GraphState,
        emitter: EventEmitter,
        graph_name: Optional[str],
        *,
        retry_manager: RetryManager,
        rate_manager: RateLimiterManager,
        permission_manager: PermissionManager,
        cancel_token: CancelToken,
        deadline: Optional[float],
        registries: Mapping[str, Any],
    ) -> tuple[Dict[str, Any], Any]:
        branches = spec.config.get("branches")
        if not isinstance(branches, list) or not branches:
            raise GraphExecutionError(
                "ERR_PARALLEL_EMPTY",
                f"Parallel node '{spec.id}' defines no branches",
                pointer=spec.pointer,
            )

        merge_policy = str(spec.config.get("merge_policy", "overwrite")).lower()
        mode = str(spec.config.get("mode", "all")).lower()

        branch_specs: list[tuple[str, NodeSpec]] = []
        for branch_id in branches:
            if not isinstance(branch_id, str):
                continue
            branch_spec = definition.nodes.get(branch_id)
            if branch_spec is None:
                raise GraphExecutionError(
                    "ERR_EDGE_ENDPOINT_INVALID",
                    f"Parallel branch '{branch_id}' is not defined",
                    pointer=spec.pointer,
                )
            branch_specs.append((branch_id, branch_spec))

        if not branch_specs:
            raise GraphExecutionError(
                "ERR_PARALLEL_EMPTY",
                f"Parallel node '{spec.id}' defines no valid branches",
                pointer=spec.pointer,
            )

        results: Dict[str, NodeRuntimeState] = {}

        async def run_branch(branch_id: str, branch_spec: NodeSpec) -> NodeRuntimeState:
            branch_state = await self._invoke_component_spec(
                branch_spec,
                state,
                emitter,
                graph_name,
                retry_manager=retry_manager,
                rate_manager=rate_manager,
                permission_manager=permission_manager,
                cancel_token=cancel_token,
                deadline=deadline,
                registries=registries,
            )
            return branch_state

        if mode in {"first_success", "any"}:
            task_map = {
                branch_id: asyncio.create_task(run_branch(branch_id, branch_spec))
                for branch_id, branch_spec in branch_specs
            }
            done, pending = await asyncio.wait(task_map.values(), return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            winning_task = next(iter(done))
            try:
                branch_state = winning_task.result()
            except Exception as exc:
                raise GraphExecutionError(
                    "ERR_NODE_RUNTIME",
                    f"Parallel node '{spec.id}' failed: {exc}",
                    pointer=spec.pointer,
                ) from exc
            winning_id = next(branch_id for branch_id, task in task_map.items() if task is winning_task)
            results[winning_id] = branch_state
        else:
            for branch_id, branch_spec in branch_specs:
                branch_state = await run_branch(branch_id, branch_spec)
                results[branch_id] = branch_state

        merged_outputs: Dict[str, Any] = {}
        if merge_policy == "namespace":
            merged_outputs = {branch_id: state.outputs for branch_id, state in results.items()}
        else:
            for branch_id, branch_state in results.items():
                for key, value in branch_state.outputs.items():
                    if merge_policy == "error" and key in merged_outputs and merged_outputs[key] != value:
                        raise GraphExecutionError(
                            "ERR_NODE_RUNTIME",
                            f"Parallel merge conflict for key '{key}'",
                            pointer=spec.pointer,
                        )
                    merged_outputs[key] = value

        return {"results": merged_outputs}, {branch_id: state.outputs for branch_id, state in results.items()}

    async def _invoke_component_spec(
        self,
        spec: NodeSpec,
        state: _GraphState,
        emitter: EventEmitter,
        graph_name: Optional[str],
        *,
        retry_manager: RetryManager,
        rate_manager: RateLimiterManager,
        permission_manager: PermissionManager,
        cancel_token: CancelToken,
        deadline: Optional[float],
        registries: Mapping[str, Any],
        loop_context: Optional[Dict[str, Any]] = None,
        emit_event: bool = True,
    ) -> NodeRuntimeState:
        if spec.component is None:
            return NodeRuntimeState(outputs={}, result=None)

        required_permissions: List[str] = []
        if spec.kind == "tool" and spec.component_meta is not None:
            raw_required = spec.component_meta.config.get("requires_permissions", [])
            if isinstance(raw_required, Sequence):
                required_permissions = [str(item) for item in raw_required]
            permission_manager.check_tool_permissions(spec.component_meta.id, required_permissions)

        async def attempt() -> tuple[NodeRuntimeState, Dict[str, Any]]:
            await rate_manager.acquire(
                node_id=spec.id,
                provider_id=spec.component_meta.provider_id if spec.component_meta else None,
            )
            inputs_payload = self._prepare_inputs(spec, state, loop_context=loop_context)
            state_view = self._make_state_view(state)
            context = build_component_context(
                node_id=spec.id,
                graph_name=graph_name,
                config=spec.config,
                emit=emitter.emit,
                cancel_token=cancel_token,
                deadline=deadline,
                registries=registries,
            )
            context["loop"] = loop_context
            
            # Execute before_execute hook if present
            from agent_ethan2.runtime.hooks import has_hook
            if has_hook(spec.component, 'before_execute'):
                modified_inputs = await spec.component.before_execute(inputs_payload, context)
                if modified_inputs is not None:
                    inputs_payload = modified_inputs
            
            # Execute main component logic
            invocation = spec.component(state_view, inputs_payload, context)
            result = await _maybe_await(invocation)
            
            # Execute after_execute hook if present
            if has_hook(spec.component, 'after_execute'):
                modified_result = await spec.component.after_execute(result, inputs_payload, context)
                if modified_result is not None:
                    result = modified_result
            
            outputs = self._prepare_outputs(spec, result)
            return NodeRuntimeState(outputs=outputs, result=result), inputs_payload

        # Initialize variables for error handler
        inputs_payload: Dict[str, Any] = {}
        
        policy = retry_manager.for_node(spec.id)
        try:
            if policy is not None:
                node_state, inputs_payload = await policy.execute(spec.id, attempt)
            else:
                node_state, inputs_payload = await attempt()
        except Exception as e:
            # Execute on_error hook if present
            from agent_ethan2.runtime.hooks import has_hook
            if has_hook(spec.component, 'on_error'):
                # Build minimal context for error handler
                error_context = build_component_context(
                    node_id=spec.id,
                    graph_name=graph_name,
                    config=spec.config,
                    emit=emitter.emit,
                    cancel_token=cancel_token,
                    deadline=deadline,
                    registries=registries,
                )
                try:
                    await spec.component.on_error(e, inputs_payload, error_context)
                except Exception:
                    # Silently ignore errors in error handlers to avoid infinite loops
                    pass
            raise

        if emit_event:
            self._emit_component_event(spec, emitter, inputs_payload, node_state.outputs, node_state.result)
        return node_state

    def _collect_outputs(self, definition: GraphDefinition, state: _GraphState) -> Dict[str, Any]:
        outputs: Dict[str, Any] = {}
        for mapping in definition.outputs:
            node_state = state.node_states.get(mapping.node_id)
            if node_state is None:
                raise GraphExecutionError(
                    "ERR_EDGE_ENDPOINT_INVALID",
                    f"Graph output references undefined node '{mapping.node_id}'",
                    pointer="/graph/outputs",
                )
            if mapping.output not in node_state.outputs:
                raise GraphExecutionError(
                    "ERR_NODE_TYPE",
                    f"Graph output '{mapping.key}' expects field '{mapping.output}' from node '{mapping.node_id}'",
                    pointer="/graph/outputs",
                )
            outputs[mapping.key] = node_state.outputs[mapping.output]
        return outputs

    def _resolve_expression(
        self,
        expression: Any,
        state: _GraphState,
        *,
        loop_context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if not isinstance(expression, str):
            return expression
        if expression.startswith("graph.inputs."):
            key = expression[len("graph.inputs."):]
            return state.inputs.get(key)
        if expression.startswith("node."):
            parts = expression.split(".")
            if len(parts) < 3:
                return None
            node_id = parts[1]
            field = parts[2]
            node_state = state.node_states.get(node_id)
            if node_state is None:
                return None
            return node_state.outputs.get(field)
        if expression == "map.item":
            if loop_context is None:
                return None
            return loop_context.get("map_item")
        if expression.startswith("map.item."):
            if loop_context is None:
                return None
            value = loop_context.get("map_item")
            path = expression[len("map.item."):].split(".")
            return _traverse_path(value, path)
        if expression == "map.index":
            if loop_context is None:
                return None
            return loop_context.get("map_index")
        if expression.startswith("const:"):
            return expression[len("const:"):]
        return expression

    def _resolve_result_expression(self, expression: Any, result: Any) -> Any:
        if not isinstance(expression, str):
            return expression
        if expression.startswith("$."):
            # Parse JSONPath: support both dict keys and array indices (e.g. $.choices[0].text)
            import re
            path_pattern = r'\.?([^\.\[]+)|\[(\d+)\]'
            matches = re.findall(path_pattern, expression[2:])
            current = result
            for key, index in matches:
                if index:  # Array index like [0]
                    idx = int(index)
                    if isinstance(current, (list, tuple)) and 0 <= idx < len(current):
                        current = current[idx]
                    else:
                        return None
                elif key:  # Dict key
                    if isinstance(current, Mapping) and key in current:
                        current = current[key]
                    else:
                        return None
            return current
        return expression

    def _emit_component_event(
        self,
        spec: NodeSpec,
        emitter: EventEmitter,
        inputs: Mapping[str, Any],
        outputs: Mapping[str, Any],
        result: Any,
    ) -> None:
        if spec.kind == "llm":
            provider_id = spec.component_meta.provider_id if spec.component_meta else None
            usage = result.get("usage") if isinstance(result, Mapping) else None
            tokens_in = usage.get("prompt_tokens") if isinstance(usage, Mapping) else None
            tokens_out = usage.get("completion_tokens") if isinstance(usage, Mapping) else None
            model = spec.component_meta.config.get("model") if spec.component_meta else None
            emitter.emit(
                "llm.call",
                node_id=spec.id,
                provider_id=provider_id,
                model=model,
                component_id=spec.component_meta.id if spec.component_meta else None,
                inputs=inputs,
                outputs=outputs,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )
        elif spec.kind == "tool":
            tool_id = spec.component_meta.tool_id if spec.component_meta else None
            required = []
            if spec.component_meta:
                raw_required = spec.component_meta.config.get("requires_permissions", [])
                if isinstance(raw_required, Sequence):
                    required = [str(item) for item in raw_required]
            emitter.emit(
                "tool.call",
                node_id=spec.id,
                tool_id=tool_id,
                 component_id=spec.component_meta.id if spec.component_meta else None,
                inputs=inputs,
                outputs=outputs,
                required_permissions=required,
            )

    def _collect_closables(self, definition: GraphDefinition) -> List[tuple[Any, Optional[str]]]:
        seen: Dict[int, tuple[Any, Optional[str]]] = {}
        for spec in definition.nodes.values():
            component = spec.component
            if component is None or not hasattr(component, "close"):
                continue
            component_id = spec.component_meta.id if spec.component_meta else None
            seen[id(component)] = (component, component_id)
        return list(seen.values())

    async def _close_components(
        self,
        closables: List[tuple[Any, Optional[str]]],
        emitter: _RunEventEmitter,
    ) -> None:
        for component, component_id in closables:
            try:
                result = component.close()
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:  # pragma: no cover - defensive
                emitter.emit(
                    "error.raised",
                    node_id=component_id,
                    kind="component",
                    message=f"close failed: {exc}",
                )


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _traverse_path(value: Any, path: list[str]) -> Any:
    current = value
    for part in path:
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return None
    return current
