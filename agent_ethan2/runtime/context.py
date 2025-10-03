"""Runtime context helpers for component invocation."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable, Iterator, MutableMapping
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


class CancelToken:
    """Simple cancellation token shared with components."""

    def __init__(self) -> None:
        self._event = asyncio.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    async def wait(self) -> None:
        await self._event.wait()


@dataclass
class ComponentContextData:
    node_id: str
    graph_name: Optional[str]
    config: Mapping[str, Any]
    emit: Any
    cancel_token: CancelToken
    deadline: Optional[float]
    registries: Mapping[str, Any]
    logger: logging.Logger


class ComponentContext(MutableMapping[str, Any]):
    """Context object passed to Python components."""

    def __init__(self, data: ComponentContextData) -> None:
        self._data: Dict[str, Any] = {
            "node_id": data.node_id,
            "graph_name": data.graph_name,
            "config": data.config,
            "emit": data.emit,
            "cancel_token": data.cancel_token,
            "deadline": data.deadline,
            "registries": data.registries,
            "logger": data.logger,
        }

    # MutableMapping interface
    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __getattr__(self, item: str) -> Any:
        try:
            return self._data[item]
        except KeyError as exc:  # pragma: no cover - defensive
            raise AttributeError(item) from exc

    def as_dict(self) -> Mapping[str, Any]:
        return dict(self._data)


def build_component_context(
    *,
    node_id: str,
    graph_name: Optional[str],
    config: Mapping[str, Any],
    emit: Any,
    cancel_token: CancelToken,
    deadline: Optional[float],
    registries: Mapping[str, Any],
) -> ComponentContext:
    logger_name = f"agent_ethan2.node.{node_id}"
    logger = logging.getLogger(logger_name)
    data = ComponentContextData(
        node_id=node_id,
        graph_name=graph_name,
        config=config,
        emit=emit,
        cancel_token=cancel_token,
        deadline=deadline,
        registries=registries,
        logger=logger,
    )
    return ComponentContext(data)
