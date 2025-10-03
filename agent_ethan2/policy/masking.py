"""Masking utilities for telemetry export."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence


@dataclass
class MaskingConfig:
    fields: Sequence[str]
    diff_fields: Sequence[str]
    mask_value: str


class MaskingEngine:
    """Applies masking rules to event payloads prior to export."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        cfg = config or {}
        fields = cfg.get("fields", [])
        diff_fields = cfg.get("diff_fields", [])
        mask_value = cfg.get("mask_value", "***")
        self._config = MaskingConfig(
            fields=[str(field) for field in fields],
            diff_fields=[str(field) for field in diff_fields],
            mask_value=str(mask_value),
        )
        # Per run diff tracking
        self._previous: Dict[str, Dict[str, Any]] = {}

    def mask(self, event: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        run_id = str(payload.get("run_id", ""))
        masked = deepcopy(payload)
        for field in self._config.fields:
            _set_path(masked, field, self._config.mask_value)
        if run_id:
            prev_for_run = self._previous.setdefault(run_id, {})
            for field in self._config.diff_fields:
                current_value = _get_path(masked, field)
                if current_value is None:
                    continue
                previous_value = prev_for_run.get(field)
                if previous_value is not None and previous_value != current_value:
                    _set_path(masked, field, self._config.mask_value)
                prev_for_run[field] = current_value
        return masked


def _get_path(data: Mapping[str, Any], path: str) -> Any:
    parts = [part for part in path.split(".") if part]
    current: Any = data
    for part in parts:
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return None
    return current


def _set_path(data: MutableMapping[str, Any], path: str, value: Any) -> None:
    parts = [part for part in path.split(".") if part]
    if not parts:
        return
    current: MutableMapping[str, Any] = data
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, MutableMapping):
            next_value = {}
            current[part] = next_value
        current = next_value  # type: ignore[assignment]
    current[parts[-1]] = value
