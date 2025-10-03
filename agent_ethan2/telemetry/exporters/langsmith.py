"""LangSmith telemetry exporter."""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional

from agent_ethan2.telemetry.event_bus import TelemetryExporter


class LangSmithExporter(TelemetryExporter):
    """Exports events to LangSmith for tracing and monitoring."""

    def __init__(
        self,
        *,
        project_name: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        """
        Initialize LangSmith exporter.
        
        Args:
            project_name: LangSmith project name (defaults to LANGSMITH_PROJECT env var)
            api_key: LangSmith API key (defaults to LANGSMITH_API_KEY env var)
            endpoint: LangSmith API endpoint (defaults to LANGSMITH_ENDPOINT env var)
        """
        self.project_name = project_name or os.getenv("LANGSMITH_PROJECT", "agent-ethan2")
        self.api_key = api_key or os.getenv("LANGSMITH_API_KEY")
        self.endpoint = endpoint or os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        
        if not self.api_key:
            raise ValueError(
                "LangSmith API key is required. "
                "Set LANGSMITH_API_KEY environment variable or pass api_key parameter."
            )
        
        # Lazy import to avoid hard dependency
        try:
            from langsmith import Client
            self.client = Client(api_url=self.endpoint, api_key=self.api_key)
        except ImportError as e:
            raise ImportError(
                "langsmith package is required for LangSmithExporter. "
                "Install with: pip install langsmith"
            ) from e
        
        # Track run IDs to LangSmith run IDs
        self._run_mapping: dict[str, str] = {}
        # Track active traces
        self._active_traces: dict[str, Any] = {}

    def export(self, event: str, payload: Mapping[str, Any]) -> None:
        """Export event to LangSmith."""
        run_id = payload.get("run_id")
        if not run_id:
            return
        
        # Map AgentEthan events to LangSmith
        if event == "graph.start":
            self._handle_graph_start(run_id, payload)
        elif event == "node.start":
            self._handle_node_start(run_id, payload)
        elif event == "node.complete":
            self._handle_node_complete(run_id, payload)
        elif event == "llm.call":
            self._handle_llm_call(run_id, payload)
        elif event == "tool.call":
            self._handle_tool_call(run_id, payload)
        elif event == "graph.complete":
            self._handle_graph_complete(run_id, payload)
        elif event == "error.raised":
            self._handle_error(run_id, payload)

    def _handle_graph_start(self, run_id: str, payload: Mapping[str, Any]) -> None:
        """Handle graph start event."""
        graph_name = payload.get("graph_name", "unknown")
        
        # Create root trace
        trace = self.client.create_run(
            name=graph_name,
            run_type="chain",
            inputs=payload.get("inputs", {}),
            project_name=self.project_name,
        )
        
        self._run_mapping[run_id] = str(trace.id)
        self._active_traces[run_id] = trace

    def _handle_node_start(self, run_id: str, payload: Mapping[str, Any]) -> None:
        """Handle node start event."""
        if run_id not in self._run_mapping:
            return
        
        parent_run_id = self._run_mapping[run_id]
        node_id = payload.get("node_id", "unknown")
        node_kind = payload.get("kind", "unknown")
        
        # Create child run for this node
        node_run = self.client.create_run(
            name=f"{node_kind}:{node_id}",
            run_type=self._map_node_kind_to_run_type(node_kind),
            inputs=payload.get("inputs", {}),
            parent_run_id=parent_run_id,
            project_name=self.project_name,
        )
        
        # Store node run ID
        self._run_mapping[f"{run_id}:{node_id}"] = str(node_run.id)

    def _handle_node_complete(self, run_id: str, payload: Mapping[str, Any]) -> None:
        """Handle node complete event."""
        node_id = payload.get("node_id", "unknown")
        node_run_key = f"{run_id}:{node_id}"
        
        if node_run_key not in self._run_mapping:
            return
        
        node_run_id = self._run_mapping[node_run_key]
        
        # Update run with outputs
        self.client.update_run(
            run_id=node_run_id,
            outputs=payload.get("outputs", {}),
            end_time=payload.get("timestamp"),
        )

    def _handle_llm_call(self, run_id: str, payload: Mapping[str, Any]) -> None:
        """Handle LLM call event."""
        # LLM calls are already tracked via node events
        # This can be used for additional metadata
        pass

    def _handle_tool_call(self, run_id: str, payload: Mapping[str, Any]) -> None:
        """Handle tool call event."""
        # Tool calls are already tracked via node events
        pass

    def _handle_graph_complete(self, run_id: str, payload: Mapping[str, Any]) -> None:
        """Handle graph complete event."""
        if run_id not in self._run_mapping:
            return
        
        graph_run_id = self._run_mapping[run_id]
        
        # Update root trace
        self.client.update_run(
            run_id=graph_run_id,
            outputs=payload.get("outputs", {}),
            end_time=payload.get("timestamp"),
        )
        
        # Cleanup
        del self._run_mapping[run_id]
        if run_id in self._active_traces:
            del self._active_traces[run_id]

    def _handle_error(self, run_id: str, payload: Mapping[str, Any]) -> None:
        """Handle error event."""
        if run_id not in self._run_mapping:
            return
        
        graph_run_id = self._run_mapping[run_id]
        
        # Update run with error
        self.client.update_run(
            run_id=graph_run_id,
            error=payload.get("message", "Unknown error"),
            end_time=payload.get("timestamp"),
        )

    def _map_node_kind_to_run_type(self, kind: str) -> str:
        """Map AgentEthan node kind to LangSmith run type."""
        mapping = {
            "llm": "llm",
            "tool": "tool",
            "router": "chain",
            "map": "chain",
            "parallel": "chain",
            "component": "chain",
        }
        return mapping.get(kind, "chain")

