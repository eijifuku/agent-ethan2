"""History storage backend abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping, Sequence


class HistoryBackend(ABC):
    """Abstract base class for conversation history storage backends."""
    
    @abstractmethod
    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        ...
    
    @abstractmethod
    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        Append a single message to the conversation history.
        
        Args:
            session_id: Unique session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content
        """
        ...
    
    @abstractmethod
    async def set_history(
        self,
        session_id: str,
        messages: Sequence[dict[str, str]],
    ) -> None:
        """
        Replace entire conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            messages: List of message dicts
        """
        ...
    
    @abstractmethod
    async def clear_history(self, session_id: str) -> None:
        """
        Clear all history for a session.
        
        Args:
            session_id: Unique session identifier
        """
        ...


class InMemoryHistoryBackend(HistoryBackend):
    """In-memory conversation history storage (for development/testing)."""
    
    def __init__(self, max_turns: int | None = None):
        """
        Initialize in-memory history backend.
        
        Args:
            max_turns: Maximum number of turns to keep (None = unlimited)
        """
        self._storage: dict[str, list[dict[str, str]]] = {}
        self._max_turns = max_turns
    
    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        """Get history from memory."""
        return list(self._storage.get(session_id, []))
    
    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Append message to memory."""
        if session_id not in self._storage:
            self._storage[session_id] = []
        
        self._storage[session_id].append({
            "role": role,
            "content": content,
        })
        
        # Prune old messages if max_turns is set
        if self._max_turns is not None:
            # Keep last max_turns messages
            self._storage[session_id] = self._storage[session_id][-self._max_turns:]
    
    async def set_history(
        self,
        session_id: str,
        messages: Sequence[dict[str, str]],
    ) -> None:
        """Replace history in memory."""
        self._storage[session_id] = [
            {"role": str(msg["role"]), "content": str(msg["content"])}
            for msg in messages
            if isinstance(msg, dict) and "role" in msg and "content" in msg
        ]
        
        # Prune if necessary
        if self._max_turns is not None:
            self._storage[session_id] = self._storage[session_id][-self._max_turns:]
    
    async def clear_history(self, session_id: str) -> None:
        """Clear history from memory."""
        if session_id in self._storage:
            del self._storage[session_id]


class RedisHistoryBackend(HistoryBackend):
    """Redis-based conversation history storage (production-ready)."""
    
    def __init__(
        self,
        redis_url: str,
        key_prefix: str = "chat_history:",
        max_turns: int | None = None,
        ttl: int | None = None,
    ):
        """
        Initialize Redis history backend.
        
        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379/0")
            key_prefix: Prefix for Redis keys
            max_turns: Maximum number of turns to keep
            ttl: Time-to-live in seconds (None = no expiration)
        """
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._max_turns = max_turns
        self._ttl = ttl
        self._redis = None
    
    async def _ensure_connected(self):
        """Lazy connection to Redis."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = await redis.from_url(self._redis_url)
            except ImportError:
                raise RuntimeError(
                    "Redis backend requires 'redis' package. "
                    "Install with: pip install redis"
                )
    
    def _make_key(self, session_id: str) -> str:
        """Create Redis key for a session."""
        return f"{self._key_prefix}{session_id}"
    
    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        """Get history from Redis."""
        await self._ensure_connected()
        key = self._make_key(session_id)
        
        # Get all messages from Redis list
        messages_raw = await self._redis.lrange(key, 0, -1)
        
        import json
        messages = []
        for msg_bytes in messages_raw:
            try:
                msg = json.loads(msg_bytes.decode('utf-8'))
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(msg)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return messages
    
    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Append message to Redis."""
        await self._ensure_connected()
        key = self._make_key(session_id)
        
        import json
        message = {"role": role, "content": content}
        
        # Append to Redis list
        await self._redis.rpush(key, json.dumps(message))
        
        # Trim to max_turns
        if self._max_turns is not None:
            await self._redis.ltrim(key, -self._max_turns, -1)
        
        # Set TTL
        if self._ttl is not None:
            await self._redis.expire(key, self._ttl)
    
    async def set_history(
        self,
        session_id: str,
        messages: Sequence[dict[str, str]],
    ) -> None:
        """Replace history in Redis."""
        await self._ensure_connected()
        key = self._make_key(session_id)
        
        import json
        
        # Delete existing
        await self._redis.delete(key)
        
        # Add all messages
        if messages:
            serialized = [json.dumps(msg) for msg in messages]
            await self._redis.rpush(key, *serialized)
            
            # Trim to max_turns
            if self._max_turns is not None:
                await self._redis.ltrim(key, -self._max_turns, -1)
            
            # Set TTL
            if self._ttl is not None:
                await self._redis.expire(key, self._ttl)
    
    async def clear_history(self, session_id: str) -> None:
        """Clear history from Redis."""
        await self._ensure_connected()
        key = self._make_key(session_id)
        await self._redis.delete(key)


# Factory function to create backends from config
def create_history_backend(config: Mapping[str, Any]) -> HistoryBackend:
    """
    Create a history backend from configuration.
    
    Args:
        config: Backend configuration dict
        
    Returns:
        HistoryBackend instance
        
    Example:
        # In-memory
        backend = create_history_backend({
            "type": "memory",
            "max_turns": 20
        })
        
        # Redis
        backend = create_history_backend({
            "type": "redis",
            "url": "redis://localhost:6379/0",
            "key_prefix": "chat:",
            "max_turns": 50,
            "ttl": 3600
        })
    """
    backend_type = config.get("type", "memory").lower()
    
    if backend_type == "memory":
        return InMemoryHistoryBackend(
            max_turns=config.get("max_turns")
        )
    
    elif backend_type == "redis":
        return RedisHistoryBackend(
            redis_url=config.get("url", "redis://localhost:6379/0"),
            key_prefix=config.get("key_prefix", "chat_history:"),
            max_turns=config.get("max_turns"),
            ttl=config.get("ttl"),
        )
    
    else:
        raise ValueError(f"Unknown history backend type: {backend_type}")

