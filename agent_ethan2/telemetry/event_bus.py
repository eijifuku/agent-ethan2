"""Event bus and telemetry exporters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from agent_ethan2.policy.cost import CostLimiter
from agent_ethan2.policy.masking import MaskingEngine
from agent_ethan2.policy.permissions import PermissionManager


class TelemetryExporter:
    """Protocol-like interface for telemetry exporters."""

    def export(self, event: str, payload: Mapping[str, Any]) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class EventRecord:
    event: str
    payload: Mapping[str, Any]
    error: Optional[str] = None


class EventBus:
    """Routes runtime events through masking and to registered exporters."""

    def __init__(
        self,
        *,
        exporters: Optional[Iterable[TelemetryExporter]] = None,
        masking: Optional[MaskingEngine] = None,
        permissions: Optional[PermissionManager] = None,
        cost: Optional[CostLimiter] = None,
    ) -> None:
        self._exporters: List[TelemetryExporter] = list(exporters or [])
        self._masking = masking or MaskingEngine()
        self._permissions = permissions or PermissionManager()
        self._cost = cost or CostLimiter()
        self._sequence: MutableMapping[str, int] = {}
        self._fallback: List[EventRecord] = []

    def register(self, exporter: TelemetryExporter) -> None:
        self._exporters.append(exporter)

    @property
    def fallback_records(self) -> Sequence[EventRecord]:
        return tuple(self._fallback)

    def emit(self, event: str, **payload: Any) -> None:
        run_id = payload.get("run_id")
        if not run_id:
            raise ValueError("Event payload missing run_id")
        run_id = str(run_id)
        sequence = self._sequence.get(run_id, 0)
        raw_payload = dict(payload)
        raw_payload.setdefault("sequence", sequence)
        self._sequence[run_id] = sequence + 1

        # Enforce permissions/cost prior to masking/export
        if event == "tool.call":
            required = raw_payload.get("required_permissions", [])
            if isinstance(required, Sequence):
                component_id = raw_payload.get("component_id") or raw_payload.get("node_id", "")
                self._permissions.check_tool_permissions(str(component_id), [str(item) for item in required])
        elif event == "llm.call":
            tokens_in = _safe_int(raw_payload.get("tokens_in"))
            tokens_out = _safe_int(raw_payload.get("tokens_out"))
            self._cost.record_llm_call(run_id, tokens_in, tokens_out)

        masked_payload = self._masking.mask(event, raw_payload)

        for exporter in self._exporters:
            try:
                exporter.export(event, masked_payload)
            except Exception as exc:  # pragma: no cover - exporter failures
                self._fallback.append(EventRecord(event=event, payload=masked_payload, error=str(exc)))


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return None
