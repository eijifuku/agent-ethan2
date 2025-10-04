"""Base utilities for provider factory implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping as MappingABC
import os
from typing import Any, Mapping, Optional

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedProvider


class ProviderFactoryBase(ABC):
    """Base class for provider factories with shared validation helpers."""

    #: Default error code for provider factory failures. Subclasses can override.
    error_code = "ERR_PROVIDER_FACTORY"

    def __call__(self, provider: NormalizedProvider) -> Mapping[str, Any]:
        if not isinstance(provider, NormalizedProvider):  # pragma: no cover - defensive
            raise GraphExecutionError(
                self.error_code,
                "Provider factory received an unexpected provider payload",
                pointer="/providers",
            )
        try:
            result = self.build(provider)
        except GraphExecutionError:
            raise
        except Exception as exc:  # pragma: no cover - actual cause covered in tests
            raise GraphExecutionError(
                self.error_code,
                f"Failed to initialize provider '{provider.type}': {exc}",
                pointer=self._pointer(provider),
            ) from exc

        if not isinstance(result, MappingABC):
            raise GraphExecutionError(
                self.error_code,
                "Provider factory must return a mapping with provider context",
                pointer=self._pointer(provider),
            )
        return result

    @abstractmethod
    def build(self, provider: NormalizedProvider) -> Mapping[str, Any]:
        """Create the provider context returned to downstream components."""

    # Helper utilities -----------------------------------------------------------------

    def get_config_value(
        self,
        provider: NormalizedProvider,
        key: str,
        *,
        env_var: Optional[str] = None,
        default: Optional[Any] = None,
    ) -> Any:
        """Read a config value from the provider or fall back to an environment variable."""

        if key in provider.config and provider.config[key] not in (None, ""):
            return provider.config[key]
        if env_var:
            env_value = os.getenv(env_var)
            if env_value not in (None, ""):
                return env_value
        return default

    def require_config_value(
        self,
        provider: NormalizedProvider,
        key: str,
        *,
        env_var: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Any:
        """Retrieve a required config value or raise a structured error."""

        value = self.get_config_value(provider, key, env_var=env_var)
        if value in (None, ""):
            if message is None:
                message = (
                    f"Missing required configuration '{key}'. "
                    f"Set providers[].config.{key} or the {env_var or key.upper()} environment variable."
                )
            raise GraphExecutionError(
                self.error_code,
                message,
                pointer=self._pointer(provider),
            )
        return value

    def coerce_float(self, provider: NormalizedProvider, value: Any, *, field: str) -> Optional[float]:
        """Convert a value to float or raise a descriptive error."""

        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise GraphExecutionError(
                self.error_code,
                f"Invalid float value for '{field}': {value!r}",
                pointer=self._pointer(provider),
            ) from exc

    def coerce_int(self, provider: NormalizedProvider, value: Any, *, field: str) -> Optional[int]:
        """Convert a value to int or raise a descriptive error."""

        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise GraphExecutionError(
                self.error_code,
                f"Invalid integer value for '{field}': {value!r}",
                pointer=self._pointer(provider),
            ) from exc

    def _pointer(self, provider: NormalizedProvider) -> str:
        return f"/providers/{provider.id}"


__all__ = ["ProviderFactoryBase"]
