"""JSONL telemetry exporter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import IO, Any, Mapping, Optional

from agent_ethan2.telemetry.event_bus import TelemetryExporter


class JsonlExporter(TelemetryExporter):
    """Writes each event as a JSON line to disk or a file-like object."""

    def __init__(self, path: Optional[str | Path] = None, *, stream: Optional[IO[str]] = None) -> None:
        if path is None and stream is None:
            raise ValueError("Either path or stream must be provided")
        self._path = Path(path) if path is not None else None
        self._stream = stream

    def export(self, event: str, payload: Mapping[str, Any]) -> None:
        record = {"event": event, **payload}
        line = json.dumps(record, ensure_ascii=False)
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        else:
            assert self._stream is not None
            self._stream.write(line + "\n")
            self._stream.flush()
