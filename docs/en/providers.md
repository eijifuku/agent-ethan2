# Providers

Configure and use LLM providers in AgentEthan2.

## Default Factories

AgentEthan2 ships with ready-to-use provider factories. They are automatically registered and can be referenced in YAML without any extra plumbing.

| Provider type | Factory path | Key settings |
| ------------- | ------------ | ------------ |
| `openai`      | `agent_ethan2.providers.openai.create_openai_provider` | `api_key`, `model`, `base_url`, `organization`, `timeout`, `max_retries`, `temperature` |
| `anthropic`   | `agent_ethan2.providers.anthropic.create_anthropic_provider` | `api_key`, `model`, `max_tokens`, `temperature` |

The factories read configuration from `providers[].config` and fall back to well-known environment variables when the value is not present.

## Basic Usage

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      # api_key is resolved from config or OPENAI_API_KEY

components:
  - id: answer_llm
    type: llm
    provider: openai
    inputs:
      prompt: graph.inputs.user_prompt
    outputs:
      text: $.choices[0].text
```

No custom factory registration is required—the default OpenAI factory will instantiate the client and expose it to the component.

## Environment Variables

| Provider | Key | Purpose |
| -------- | --- | ------- |
| OpenAI | `OPENAI_API_KEY` | API key fallback |
| OpenAI | `OPENAI_MODEL` | Default model name |
| OpenAI | `OPENAI_BASE_URL` | Base URL for OpenAI-compatible endpoints |
| OpenAI | `OPENAI_ORGANIZATION` | Organization identifier |
| OpenAI | `OPENAI_TIMEOUT` | Request timeout (seconds) |
| OpenAI | `OPENAI_MAX_RETRIES` | Retry count |
| OpenAI | `OPENAI_TEMPERATURE` | Default sampling temperature |
| Anthropic | `ANTHROPIC_API_KEY` | API key fallback |
| Anthropic | `ANTHROPIC_MODEL` | Default model name |
| Anthropic | `ANTHROPIC_MAX_TOKENS` | Completion token limit |
| Anthropic | `ANTHROPIC_TEMPERATURE` | Sampling temperature |

Define the environment variables when you do not want to commit sensitive values to source control.

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

## Local and Self-Hosted Models

The OpenAI factory supports alternate base URLs that implement the OpenAI REST contract (Ollama, LM Studio, vLLM, etc.). When a `base_url` is provided, the API key becomes optional.

```yaml
providers:
  - id: local_llm
    type: openai
    config:
      model: llama3
      base_url: http://localhost:11434/v1
      api_key: dummy  # optional for Ollama-style endpoints
```

## Multiple Providers

You can mix different providers in the same project without additional wiring.

```yaml
providers:
  - id: openai_fast
    type: openai
    config:
      model: gpt-4o-mini

  - id: claude
    type: anthropic
    config:
      model: claude-3-5-sonnet-latest
      max_tokens: 2048

components:
  - id: classifier
    type: llm
    provider: openai_fast
  - id: writer
    type: llm
    provider: claude
```

## Provider Context Structure

Factories return a mapping that is passed to component factories. The built-in providers expose:

```python
{
    "client": <SDK client>,
    "model": "...",            # resolved model name
    "config": {...},             # copy of providers[].config
    # OpenAI-only:
    "base_url": "..." or None,
    "organization": "..." or None,
    "timeout": float | None,
    "max_retries": int | None,
    "temperature": float | None,
    # Anthropic-only:
    "max_tokens": int | None,
    "temperature": float | None,
}
```

Components can pull information from this mapping to configure calls.

## Overriding Factories

AgentEthan merges provider factories in the following order (last wins):

1. Constructor arguments passed to `AgentEthan` (`provider_factories`)
2. `runtime.factories.providers` in YAML
3. Built-in defaults (`DEFAULT_PROVIDER_FACTORIES`)

If you want to replace or extend the default behaviour, define a custom factory and register it through YAML or code. See [Providers (Advanced)](./providers-advanced.md) for recipes and best practices.

## Best Practices

- Store secrets in environment variables rather than YAML files.
- Configure sensible timeouts and retry limits for production.
- Reuse provider IDs across components to share client instances.
- Use local models for development workflows when possible.
- Keep provider configuration minimal; push complex logic into custom factories when needed.

## Reference Material

- [Runtime configuration](./runtime-config.md)
- [Providers (Advanced)](./providers-advanced.md)
- [Examples directory](../examples/)
