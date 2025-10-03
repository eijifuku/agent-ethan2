"""Prometheus metrics exporter."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from agent_ethan2.telemetry.event_bus import TelemetryExporter


class PrometheusExporter(TelemetryExporter):
    """Exports metrics to Prometheus."""

    def __init__(
        self,
        *,
        port: int = 9090,
        registry: Optional[Any] = None,
    ) -> None:
        """
        Initialize Prometheus exporter.
        
        Args:
            port: Port for Prometheus metrics endpoint
            registry: Prometheus registry (defaults to CollectorRegistry)
        """
        try:
            from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
            from prometheus_client import start_http_server
        except ImportError as e:
            raise ImportError(
                "prometheus_client package is required for PrometheusExporter. "
                "Install with: pip install prometheus-client"
            ) from e
        
        self.registry = registry or CollectorRegistry()
        
        # Define metrics
        self.graph_starts = Counter(
            "agent_ethan_graph_starts_total",
            "Total number of graph executions started",
            ["graph_name"],
            registry=self.registry
        )
        
        self.graph_completions = Counter(
            "agent_ethan_graph_completions_total",
            "Total number of graph executions completed",
            ["graph_name", "status"],
            registry=self.registry
        )
        
        self.node_executions = Counter(
            "agent_ethan_node_executions_total",
            "Total number of node executions",
            ["node_id", "kind"],
            registry=self.registry
        )
        
        self.node_duration = Histogram(
            "agent_ethan_node_duration_seconds",
            "Node execution duration in seconds",
            ["node_id", "kind"],
            registry=self.registry
        )
        
        self.llm_calls = Counter(
            "agent_ethan_llm_calls_total",
            "Total number of LLM API calls",
            ["node_id"],
            registry=self.registry
        )
        
        self.llm_tokens = Counter(
            "agent_ethan_llm_tokens_total",
            "Total number of LLM tokens consumed",
            ["node_id", "direction"],
            registry=self.registry
        )
        
        self.tool_calls = Counter(
            "agent_ethan_tool_calls_total",
            "Total number of tool calls",
            ["tool_name"],
            registry=self.registry
        )
        
        self.errors = Counter(
            "agent_ethan_errors_total",
            "Total number of errors",
            ["node_id", "error_type"],
            registry=self.registry
        )
        
        self.retries = Counter(
            "agent_ethan_retries_total",
            "Total number of retry attempts",
            ["node_id"],
            registry=self.registry
        )
        
        self.rate_limit_waits = Counter(
            "agent_ethan_rate_limit_waits_total",
            "Total number of rate limit waits",
            ["target", "scope"],
            registry=self.registry
        )
        
        self.active_runs = Gauge(
            "agent_ethan_active_runs",
            "Number of currently active graph executions",
            registry=self.registry
        )
        
        # Start HTTP server for metrics
        try:
            start_http_server(port, registry=self.registry)
        except OSError:
            # Port already in use, skip
            pass
        
        # Track node start times for duration calculation
        self._node_start_times: dict[str, float] = {}

    def export(self, event: str, payload: Mapping[str, Any]) -> None:
        """Export event as Prometheus metrics."""
        if event == "graph.start":
            self._handle_graph_start(payload)
        elif event == "graph.complete":
            self._handle_graph_complete(payload)
        elif event == "node.start":
            self._handle_node_start(payload)
        elif event == "node.complete":
            self._handle_node_complete(payload)
        elif event == "llm.call":
            self._handle_llm_call(payload)
        elif event == "tool.call":
            self._handle_tool_call(payload)
        elif event == "error.raised":
            self._handle_error(payload)
        elif event == "retry.attempt":
            self._handle_retry(payload)
        elif event == "rate.limit.wait":
            self._handle_rate_limit(payload)

    def _handle_graph_start(self, payload: Mapping[str, Any]) -> None:
        """Handle graph start event."""
        graph_name = payload.get("graph_name", "unknown")
        self.graph_starts.labels(graph_name=graph_name).inc()
        self.active_runs.inc()

    def _handle_graph_complete(self, payload: Mapping[str, Any]) -> None:
        """Handle graph complete event."""
        graph_name = payload.get("graph_name", "unknown")
        status = "success" if not payload.get("error") else "error"
        self.graph_completions.labels(graph_name=graph_name, status=status).inc()
        self.active_runs.dec()

    def _handle_node_start(self, payload: Mapping[str, Any]) -> None:
        """Handle node start event."""
        import time
        node_id = payload.get("node_id", "unknown")
        run_id = payload.get("run_id", "unknown")
        kind = payload.get("kind", "unknown")
        
        self.node_executions.labels(node_id=node_id, kind=kind).inc()
        
        # Record start time for duration calculation
        key = f"{run_id}:{node_id}"
        self._node_start_times[key] = time.time()

    def _handle_node_complete(self, payload: Mapping[str, Any]) -> None:
        """Handle node complete event."""
        import time
        node_id = payload.get("node_id", "unknown")
        run_id = payload.get("run_id", "unknown")
        kind = payload.get("kind", "unknown")
        
        # Calculate duration
        key = f"{run_id}:{node_id}"
        if key in self._node_start_times:
            duration = time.time() - self._node_start_times[key]
            self.node_duration.labels(node_id=node_id, kind=kind).observe(duration)
            del self._node_start_times[key]

    def _handle_llm_call(self, payload: Mapping[str, Any]) -> None:
        """Handle LLM call event."""
        node_id = payload.get("node_id", "unknown")
        tokens_in = payload.get("tokens_in", 0)
        tokens_out = payload.get("tokens_out", 0)
        
        self.llm_calls.labels(node_id=node_id).inc()
        
        if tokens_in:
            self.llm_tokens.labels(node_id=node_id, direction="input").inc(tokens_in)
        if tokens_out:
            self.llm_tokens.labels(node_id=node_id, direction="output").inc(tokens_out)

    def _handle_tool_call(self, payload: Mapping[str, Any]) -> None:
        """Handle tool call event."""
        tool_name = payload.get("tool_name", "unknown")
        self.tool_calls.labels(tool_name=tool_name).inc()

    def _handle_error(self, payload: Mapping[str, Any]) -> None:
        """Handle error event."""
        node_id = payload.get("node_id", "unknown")
        error_type = payload.get("error_type", "unknown")
        self.errors.labels(node_id=node_id, error_type=error_type).inc()

    def _handle_retry(self, payload: Mapping[str, Any]) -> None:
        """Handle retry event."""
        node_id = payload.get("node_id", "unknown")
        self.retries.labels(node_id=node_id).inc()

    def _handle_rate_limit(self, payload: Mapping[str, Any]) -> None:
        """Handle rate limit event."""
        target = payload.get("target", "unknown")
        scope = payload.get("scope", "unknown")
        self.rate_limit_waits.labels(target=target, scope=scope).inc()

