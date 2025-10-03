"""Cost tracking utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from agent_ethan2.graph.errors import GraphExecutionError


@dataclass
class CostConfig:
    per_run_tokens: int | None


class CostLimiter:
    """Tracks token usage per run and enforces limits."""

    def __init__(self, config: Mapping[str, Any] | None = None) -> None:
        cfg = config or {}
        per_run = cfg.get("per_run_tokens")
        self._config = CostConfig(per_run_tokens=int(per_run) if per_run is not None else None)
        self._run_totals: Dict[str, int] = {}

    def record_llm_call(self, run_id: str, tokens_in: int | None, tokens_out: int | None) -> None:
        total = tokens_in or 0
        total += tokens_out or 0
        if total <= 0:
            return
        current = self._run_totals.get(run_id, 0) + total
        limit = self._config.per_run_tokens
        if limit is not None and current > limit:
            raise GraphExecutionError(
                "ERR_COST_LIMIT_EXCEEDED",
                f"Run '{run_id}' exceeded token budget ({current}>{limit})",
            )
        self._run_totals[run_id] = current
