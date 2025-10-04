# Providers (Advanced)

Guidance for extending or replacing the built-in provider factories.

## When to Write a Custom Factory

Create a factory when you need to:

- Support a provider that is not bundled with AgentEthan2 (Azure OpenAI, Bedrock, local services, etc.).
- Augment the default behaviour with additional validation, telemetry, or resource management.
- Share expensive client instances across multiple providers.

## Using `ProviderFactoryBase`

Start from `ProviderFactoryBase` to reuse validation utilities and consistent error handling.

```python
from __future__ import annotations

import os
from typing import Mapping

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedProvider
from agent_ethan2.providers.base import ProviderFactoryBase


class AzureOpenAIProviderFactory(ProviderFactoryBase):
    error_code = "ERR_PROVIDER_AZURE_OPENAI"

    def build(self, provider: NormalizedProvider) -> Mapping[str, object]:
        try:
            from openai import AzureOpenAI  # azure-openai SDK
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise GraphExecutionError(
                self.error_code,
                "Install azure-openai to use the Azure OpenAI provider.",
                pointer=self._pointer(provider),
            ) from exc

        api_key = self.require_config_value(
            provider,
            "api_key",
            env_var="AZURE_OPENAI_API_KEY",
        )
        endpoint = self.require_config_value(
            provider,
            "endpoint",
            env_var="AZURE_OPENAI_ENDPOINT",
        )
        deployment = self.require_config_value(provider, "deployment")

        api_version = self.get_config_value(
            provider,
            "api_version",
            env_var="AZURE_OPENAI_API_VERSION",
            default="2024-05-01",
        )

        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
        )

        return {
            "client": client,
            "deployment": deployment,
            "api_version": api_version,
            "config": dict(provider.config),
        }


def create_azure_openai_provider(provider: NormalizedProvider) -> Mapping[str, object]:
    return AzureOpenAIProviderFactory()(provider)
```

## Registering Custom Factories

### Via YAML

```yaml
runtime:
  factories:
    providers:
      azure_openai: my_project.factories.azure.create_azure_openai_provider
```

### Via `AgentEthan`

```python
agent = AgentEthan(
    "agent.yaml",
    provider_factories={
        "azure_openai": "my_project.factories.azure.create_azure_openai_provider",
    },
)
```

Constructor arguments override YAML, which in turn override the built-in defaults.

## Overriding Defaults

To replace the default OpenAI factory, point the `openai` key to your implementation.

```yaml
runtime:
  factories:
    providers:
      openai: my_project.factories.openai_logging_provider
```

If you only need to tweak configuration, you can wrap the default factory:

```python
from agent_ethan2.providers.openai import create_openai_provider


def create_openai_with_logging(provider: NormalizedProvider):
    context = create_openai_provider(provider)
    context["client"].responses.stream = True  # example tweak
    return context
```

## Validation and Error Codes

- Use `require_config_value` for required fields to get consistent `GraphExecutionError` instances.
- Override `error_code` on your factory class to make diagnostics easy to trace.
- Surface actionable error messages (e.g., which environment variable is missing).

## Testing Tips

- Monkeypatch SDK classes to avoid live network calls.
- Assert on the mapping returned by the factory and the arguments passed to the SDK constructor.
- Cover error scenarios (missing credentials, invalid numeric values) to ensure your factory fails fast.

## Next Steps

- [Providers overview](./providers.md)
- [Runtime configuration](./runtime-config.md)
