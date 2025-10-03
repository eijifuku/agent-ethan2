"""Error types for graph construction and execution."""

from __future__ import annotations

from typing import Optional


class GraphError(RuntimeError):
    """Base class for graph-related failures with error codes."""

    def __init__(self, code: str, message: str, *, pointer: Optional[str] = None) -> None:
        self.code = code
        self.pointer = pointer or "/"
        super().__init__(f"[{code}] {message} at {self.pointer}")


class GraphBuilderError(GraphError):
    """Raised when the graph definition cannot be constructed."""


class GraphExecutionError(GraphError):
    """Raised when execution fails at runtime."""
