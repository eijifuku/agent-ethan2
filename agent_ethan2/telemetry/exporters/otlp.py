"""Simplified OTLP exporter for tests."""

from __future__ import annotations

from typing import Any, List, Mapping

from agent_ethan2.telemetry.event_bus import TelemetryExporter


class OtlpExporter(TelemetryExporter):
    """Collects events for OTLP-like export (in-memory stub)."""

    def __init__(self) -> None:
        self.records: List[Mapping[str, Any]] = []

    def export(self, event: str, payload: Mapping[str, Any]) -> None:
        self.records.append({"event": event, **payload})
