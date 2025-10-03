"""Permission enforcement for tool execution."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Sequence, Set

from agent_ethan2.graph.errors import GraphExecutionError


class PermissionManager:
    """Tracks allowed permissions per tool/component."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        cfg = config or {}
        default_allow = cfg.get("default_allow", [])
        self._default_allow: Set[str] = {str(item) for item in default_allow}
        allow_map = cfg.get("allow", {})
        self._allow: Dict[str, Set[str]] = {}
        if isinstance(allow_map, Mapping):
            for key, values in allow_map.items():
                if isinstance(values, Iterable):
                    self._allow[str(key)] = {str(item) for item in values}

    def check_tool_permissions(self, component_id: str, required: Sequence[str]) -> None:
        allowed = set(self._default_allow)
        allowed.update(self._allow.get(component_id, set()))
        missing = {str(item) for item in required} - allowed
        if missing:
            raise GraphExecutionError(
                "ERR_TOOL_PERMISSION_DENIED",
                f"Component '{component_id}' lacks permissions: {sorted(missing)}",
                pointer=f"/components/{component_id}",
            )
