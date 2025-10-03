"""Console telemetry exporter for debugging."""

from __future__ import annotations

import json
import sys
from typing import Any, Mapping, Optional, TextIO


from agent_ethan2.telemetry.event_bus import TelemetryExporter


class ConsoleExporter(TelemetryExporter):
    """Prints events to console (stdout/stderr) for debugging."""

    def __init__(
        self,
        *,
        stream: Optional[TextIO] = None,
        color: bool = True,
        verbose: bool = False,
        filter_events: Optional[list[str]] = None,
    ) -> None:
        """
        Initialize console exporter.
        
        Args:
            stream: Output stream (defaults to sys.stdout)
            color: Enable colored output
            verbose: Show full payloads
            filter_events: Only show specific events (e.g., ["graph.start", "graph.complete"])
        """
        self.stream = stream or sys.stdout
        self.color = color
        self.verbose = verbose
        self.filter_events = set(filter_events) if filter_events else None

    def export(self, event: str, payload: Mapping[str, Any]) -> None:
        """Export event to console."""
        # Filter events if specified
        if self.filter_events and event not in self.filter_events:
            return
        
        # Format event
        if self.verbose:
            output = self._format_verbose(event, payload)
        else:
            output = self._format_compact(event, payload)
        
        # Apply colors
        if self.color:
            output = self._apply_color(event, output)
        
        # Write to stream
        self.stream.write(output + "\n")
        self.stream.flush()

    def _format_compact(self, event: str, payload: Mapping[str, Any]) -> str:
        """Compact single-line format."""
        run_id = payload.get("run_id", "unknown")[:8]
        sequence = payload.get("sequence", 0)
        
        # Event-specific formatting
        if event == "graph.start":
            graph_name = payload.get("graph_name", "unknown")
            return f"[{run_id}:{sequence:03d}] 🚀 START graph={graph_name}"
        
        elif event == "graph.complete":
            return f"[{run_id}:{sequence:03d}] ✅ COMPLETE"
        
        elif event == "node.start":
            node_id = payload.get("node_id", "unknown")
            kind = payload.get("kind", "unknown")
            return f"[{run_id}:{sequence:03d}]   → {kind}:{node_id}"
        
        elif event == "node.complete":
            node_id = payload.get("node_id", "unknown")
            return f"[{run_id}:{sequence:03d}]   ✓ {node_id}"
        
        elif event == "llm.call":
            node_id = payload.get("node_id", "unknown")
            tokens_in = payload.get("tokens_in", 0)
            tokens_out = payload.get("tokens_out", 0)
            return f"[{run_id}:{sequence:03d}]     LLM {node_id} (tokens: {tokens_in}→{tokens_out})"
        
        elif event == "tool.call":
            node_id = payload.get("node_id", "unknown")
            tool_name = payload.get("tool_name", "unknown")
            return f"[{run_id}:{sequence:03d}]     TOOL {node_id} ({tool_name})"
        
        elif event == "error.raised":
            node_id = payload.get("node_id", "unknown")
            message = payload.get("message", "unknown")[:50]
            return f"[{run_id}:{sequence:03d}] ❌ ERROR {node_id}: {message}"
        
        elif event == "retry.attempt":
            node_id = payload.get("node_id", "unknown")
            attempt = payload.get("attempt", 0)
            return f"[{run_id}:{sequence:03d}]   ⟳ RETRY {node_id} (attempt {attempt})"
        
        elif event == "rate.limit.wait":
            target = payload.get("target", "unknown")
            wait_time = payload.get("wait_time", 0)
            return f"[{run_id}:{sequence:03d}]   ⏳ RATE_LIMIT {target} (wait {wait_time:.2f}s)"
        
        else:
            return f"[{run_id}:{sequence:03d}] {event}"

    def _format_verbose(self, event: str, payload: Mapping[str, Any]) -> str:
        """Verbose multi-line format with full payload."""
        run_id = payload.get("run_id", "unknown")[:8]
        sequence = payload.get("sequence", 0)
        
        lines = [
            f"[{run_id}:{sequence:03d}] {event}",
            json.dumps(payload, indent=2, ensure_ascii=False, default=str)
        ]
        return "\n".join(lines)

    def _apply_color(self, event: str, output: str) -> str:
        """Apply ANSI color codes based on event type."""
        # ANSI color codes
        RESET = "\033[0m"
        GRAY = "\033[90m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        BLUE = "\033[94m"
        RED = "\033[91m"
        CYAN = "\033[96m"
        
        # Event-based coloring
        if event.startswith("graph."):
            return f"{CYAN}{output}{RESET}"
        elif event.startswith("node."):
            return f"{BLUE}{output}{RESET}"
        elif event.startswith("llm."):
            return f"{GREEN}{output}{RESET}"
        elif event.startswith("tool."):
            return f"{YELLOW}{output}{RESET}"
        elif event.startswith("error."):
            return f"{RED}{output}{RESET}"
        elif event.startswith("retry.") or event.startswith("rate."):
            return f"{YELLOW}{output}{RESET}"
        else:
            return f"{GRAY}{output}{RESET}"

