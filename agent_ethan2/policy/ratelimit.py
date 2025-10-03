"""Rate limit management for graph execution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import monotonic
from typing import Any, Dict, Mapping, Optional

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.runtime.events import EventEmitter


class RateLimiter:
    async def acquire(self, emitter: EventEmitter, *, scope: str, target: str) -> None:
        raise NotImplementedError


@dataclass
class TokenBucketRateLimiter(RateLimiter):
    capacity: int
    refill_rate: float
    tokens: float
    updated_at: float
    lock: asyncio.Lock

    def __init__(self, capacity: int, refill_rate: float) -> None:
        if capacity <= 0 or refill_rate <= 0:
            raise GraphExecutionError("ERR_RL_POLICY_PARAM", "Invalid token bucket parameters")
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.updated_at = monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, emitter: EventEmitter, *, scope: str, target: str) -> None:
        async with self.lock:
            now = monotonic()
            elapsed = now - self.updated_at
            if elapsed > 0:
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.updated_at = now
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            wait_time = (1.0 - self.tokens) / self.refill_rate
            emitter.emit("rate.limit.wait", scope=scope, target=target, wait_time=wait_time)
        await asyncio.sleep(wait_time)
        async with self.lock:
            now = monotonic()
            elapsed = now - self.updated_at
            if elapsed > 0:
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.updated_at = now
            self.tokens = max(0.0, self.tokens - 1.0)


@dataclass
class FixedWindowRateLimiter(RateLimiter):
    limit: int
    window: float
    window_start: float
    count: int
    lock: asyncio.Lock

    def __init__(self, limit: int, window: float) -> None:
        if limit <= 0 or window <= 0:
            raise GraphExecutionError("ERR_RL_POLICY_PARAM", "Invalid fixed window parameters")
        self.limit = limit
        self.window = window
        self.window_start = monotonic()
        self.count = 0
        self.lock = asyncio.Lock()

    async def acquire(self, emitter: EventEmitter, *, scope: str, target: str) -> None:
        async with self.lock:
            now = monotonic()
            if now - self.window_start >= self.window:
                self.window_start = now
                self.count = 0
            if self.count < self.limit:
                self.count += 1
                return
            wait_time = self.window - (now - self.window_start)
            emitter.emit("rate.limit.wait", scope=scope, target=target, wait_time=wait_time)
        await asyncio.sleep(wait_time)
        async with self.lock:
            self.window_start = monotonic()
            self.count = 1


class RateLimiterManager:
    """Resolves rate limiters for providers and nodes."""

    def __init__(self, config: Mapping[str, Any], emitter: EventEmitter) -> None:
        self._emitter = emitter
        self._provider_limits: Dict[str, RateLimiter] = {}
        self._node_limits: Dict[str, RateLimiter] = {}
        self._shared_providers: Dict[str, str] = {}
        providers = config.get("providers", [])
        nodes = config.get("nodes", [])
        shared = config.get("shared_providers", {})
        if isinstance(providers, list):
            for entry in providers:
                self._register(entry, self._provider_limits)
        if isinstance(nodes, list):
            for entry in nodes:
                self._register(entry, self._node_limits)
        if isinstance(shared, Mapping):
            for provider_id, shared_id in shared.items():
                if not isinstance(provider_id, str) or not isinstance(shared_id, str):
                    raise GraphExecutionError("ERR_RL_POLICY_PARAM", "shared_providers must map strings")
                self._shared_providers[provider_id] = shared_id

    def _register(self, entry: Any, target_map: Dict[str, RateLimiter]) -> None:
        if not isinstance(entry, Mapping):
            raise GraphExecutionError("ERR_RL_POLICY_PARAM", "Rate limit entry must be a mapping")
        target = entry.get("target")
        limiter_type = str(entry.get("type", "token_bucket")).lower()
        if not isinstance(target, str):
            raise GraphExecutionError("ERR_RL_POLICY_PARAM", "Rate limit entry missing target")
        if limiter_type == "token_bucket":
            capacity = int(entry.get("capacity", 1))
            refill_rate = float(entry.get("refill_rate", 1.0))
            limiter = TokenBucketRateLimiter(capacity=capacity, refill_rate=refill_rate)
        elif limiter_type == "fixed_window":
            limit = int(entry.get("limit", 1))
            window = float(entry.get("window", 1.0))
            limiter = FixedWindowRateLimiter(limit=limit, window=window)
        else:
            raise GraphExecutionError("ERR_RL_POLICY_PARAM", f"Unsupported rate limit type '{limiter_type}'")
        target_map[target] = limiter

    async def acquire(self, *, node_id: str, provider_id: Optional[str]) -> None:
        shared_id = None
        if provider_id and provider_id in self._shared_providers:
            shared_id = self._shared_providers[provider_id]
        limiter_key = shared_id or provider_id
        if limiter_key and limiter_key in self._provider_limits:
            await self._provider_limits[limiter_key].acquire(
                self._emitter,
                scope="provider",
                target=limiter_key,
            )
        if node_id in self._node_limits:
            await self._node_limits[node_id].acquire(
                self._emitter,
                scope="node",
                target=node_id,
            )
