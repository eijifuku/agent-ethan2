"""Execution tree reconstruction from event stream."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from agent_ethan2.telemetry.event_bus import TelemetryExporter


@dataclass
class NodeTimeline:
    node_id: str
    kind: Optional[str] = None
    started_at: Optional[float] = None
    duration_ms: Optional[float] = None
    status: Optional[str] = None
    retries: List[Mapping[str, Any]] = field(default_factory=list)


class ExecutionTreeBuilder(TelemetryExporter):
    """Builds a simple execution timeline from runtime events."""

    def __init__(self) -> None:
        self._graph: Dict[str, Any] = {}
        self._nodes: Dict[str, NodeTimeline] = {}
        self._run_id: Optional[str] = None

    def export(self, event: str, payload: Mapping[str, Any]) -> None:
        run_id = str(payload.get("run_id", ""))
        if self._run_id is None:
            self._run_id = run_id
        if run_id and self._run_id != run_id:
            return  # ignore different runs

        if event == "graph.start":
            self._graph = {
                "run_id": run_id,
                "graph_name": payload.get("graph_name"),
                "entrypoint": payload.get("entrypoint"),
                "start_ts": payload.get("ts"),
            }
        elif event == "graph.finish":
            self._graph.update(
                {
                    "finish_ts": payload.get("ts"),
                    "status": payload.get("status"),
                    "outputs": payload.get("outputs"),
                }
            )
        elif event == "node.start":
            node_id = str(payload.get("node_id"))
            timeline = self._nodes.setdefault(node_id, NodeTimeline(node_id=node_id))
            timeline.kind = payload.get("kind")
            timeline.started_at = payload.get("started_at") or payload.get("ts")
        elif event == "node.finish":
            node_id = str(payload.get("node_id"))
            timeline = self._nodes.setdefault(node_id, NodeTimeline(node_id=node_id))
            timeline.kind = payload.get("kind", timeline.kind)
            timeline.duration_ms = payload.get("duration_ms")
            timeline.status = payload.get("status")
        elif event == "retry.attempt":
            node_id = str(payload.get("node_id"))
            timeline = self._nodes.setdefault(node_id, NodeTimeline(node_id=node_id))
            timeline.retries.append(
                {
                    "attempt": payload.get("attempt"),
                    "delay": payload.get("delay"),
                    "ts": payload.get("ts"),
                    "error": payload.get("error"),
                }
            )
        elif event in {"timeout", "cancelled"}:
            self._graph.setdefault("warnings", []).append(
                {"event": event, "ts": payload.get("ts")}
            )

    def build(self) -> Mapping[str, Any]:
        nodes = []
        for node_id, timeline in self._nodes.items():
            nodes.append(
                {
                    "node_id": node_id,
                    "kind": timeline.kind,
                    "started_at": timeline.started_at,
                    "duration_ms": timeline.duration_ms,
                    "status": timeline.status,
                    "retries": timeline.retries,
                }
            )
        return {
            "graph": self._graph,
            "nodes": sorted(nodes, key=lambda item: item.get("started_at") or 0.0),
        }
