"""Simple event emitter utilities used across the runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Protocol


class EventEmitter(Protocol):
    """Protocol for event emission."""

    def emit(self, event: str, **payload: Any) -> None:
        ...


class NullEventEmitter:
    """Emitter that drops all events."""

    def emit(self, event: str, **payload: Any) -> None:  # pragma: no cover - trivial
        return


@dataclass
class InMemoryEventEmitter:
    """Emitter that stores events in memory (useful for tests)."""

    events: List[Dict[str, Any]]

    def __init__(self) -> None:
        self.events = []

    def emit(self, event: str, **payload: Any) -> None:
        record: Dict[str, Any] = {"event": event, **payload}
        self.events.append(record)


def ensure_emitter(emitter: EventEmitter | None) -> EventEmitter:
    """Return the provided emitter or a null implementation."""

    if emitter is None:
        return NullEventEmitter()
    return emitter
