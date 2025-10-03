"""Retry policy utilities for graph execution."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.runtime.events import EventEmitter

Operation = Callable[[], Awaitable[Any]]


def _is_retryable(exc: BaseException) -> bool:
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    if isinstance(status, int) and (status == 429 or 500 <= status < 600):
        return True
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    message = str(exc).lower()
    return "timeout" in message or "temporarily" in message or "retry" in message


@dataclass
class RetryPolicy:
    strategy: str
    max_attempts: int
    interval: float
    jitter: float
    emitter: EventEmitter

    async def execute(self, node_id: str, operation: Operation) -> Any:
        attempt = 0
        while True:
            try:
                return await operation()
            except Exception as exc:  # noqa: BLE001 - we re-raise after evaluation
                attempt += 1
                if attempt >= self.max_attempts or not _is_retryable(exc):
                    raise
                delay = self._compute_delay(attempt)
                self.emitter.emit(
                    "retry.attempt",
                    node_id=node_id,
                    attempt=attempt,
                    delay=delay,
                    error=str(exc),
                )
                if delay > 0:
                    await asyncio.sleep(delay)

    def _compute_delay(self, attempt: int) -> float:
        if self.strategy == "fixed":
            return self.interval
        if self.strategy == "exponential":
            return self.interval * (2 ** (attempt - 1))
        if self.strategy == "jitter":
            base = self.interval * max(1, attempt)
            return base + random.uniform(0.0, self.jitter)
        return self.interval


class RetryManager:
    """Resolves retry policies for graph nodes."""

    def __init__(self, config: Mapping[str, Any], emitter: EventEmitter) -> None:
        self._emitter = emitter
        self._default_policy = self._build_policy(config.get("default"))
        overrides = config.get("overrides", [])
        self._overrides: Dict[str, RetryPolicy] = {}
        if isinstance(overrides, list):
            for entry in overrides:
                target = entry.get("target") if isinstance(entry, Mapping) else None
                if not isinstance(target, str):
                    raise GraphExecutionError(
                        "ERR_RETRY_PREDICATE",
                        "Retry override requires a target identifier",
                    )
                self._overrides[target] = self._build_policy(entry)

    def _build_policy(self, entry: Optional[Mapping[str, Any]]) -> Optional[RetryPolicy]:
        if entry is None:
            return None
        strategy = str(entry.get("strategy", "fixed")).lower()
        if strategy not in {"fixed", "exponential", "jitter"}:
            raise GraphExecutionError("ERR_RETRY_PREDICATE", f"Unsupported retry strategy '{strategy}'")
        max_attempts = int(entry.get("max_attempts", 1))
        if max_attempts < 1:
            raise GraphExecutionError("ERR_RETRY_PREDICATE", "max_attempts must be >=1")
        interval = float(entry.get("interval", 0.0))
        jitter = float(entry.get("jitter", 0.0))
        return RetryPolicy(
            strategy=strategy,
            max_attempts=max_attempts,
            interval=interval,
            jitter=jitter,
            emitter=self._emitter,
        )

    def for_node(self, node_id: str) -> Optional[RetryPolicy]:
        return self._overrides.get(node_id, self._default_policy)
