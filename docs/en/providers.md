# Providers

Configuring LLM providers for your agent.

## Overview

Providers are LLM service connections (OpenAI, Anthropic, local models, etc.). Each provider:
- Has a unique ID
- Specifies a type
- Contains provider-specific configuration
- Is instantiated by a factory function

## Configuration

### YAML Definition

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
```

### Factory Implementation

```python
import os
from openai import OpenAI

def provider_factory(provider):
    """Create OpenAI client from provider config."""
    api_key = provider.config.get("api_key") or os.getenv("OPENAI_API_KEY")
    model = provider.config.get("model", "gpt-4o-mini")
    
    client = OpenAI(api_key=api_key)
    
    return {
        "client": client,
        "model": model,
        "config": dict(provider.config)
    }
```

## OpenAI Provider

### Basic Configuration

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
```

### Advanced Configuration

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
      organization: org-xxx
      timeout: 30
      max_retries: 3
      temperature: 0.7
```

## Local LLMs (OpenAI-Compatible)

Use `base_url` for local models like Ollama, LM Studio, etc.

### Ollama

```yaml
providers:
  - id: ollama
    type: openai
    config:
      model: llama2
      base_url: http://localhost:11434/v1
      api_key: dummy  # Ollama doesn't need a real key
```

### LM Studio

```yaml
providers:
  - id: lmstudio
    type: openai
    config:
      model: local-model
      base_url: http://localhost:1234/v1
      api_key: dummy
```

### Factory with base_url Support

```python
def provider_factory(provider):
    api_key = provider.config.get("api_key") or os.getenv("OPENAI_API_KEY")
    model = provider.config.get("model", "gpt-4o-mini")
    
    # Support for local LLMs
    client_kwargs = {"api_key": api_key}
    if "base_url" in provider.config:
        client_kwargs["base_url"] = provider.config["base_url"]
    
    client = OpenAI(**client_kwargs)
    
    return {"client": client, "model": model}
```

## Multiple Providers

Use different providers for different tasks:

```yaml
providers:
  - id: openai_fast
    type: openai
    config:
      model: gpt-4o-mini
  
  - id: openai_smart
    type: openai
    config:
      model: gpt-4o
  
  - id: local_llm
    type: openai
    config:
      model: llama2
      base_url: http://localhost:11434/v1

components:
  - id: classifier
    type: llm
    provider: openai_fast  # Fast model for classification
  
  - id: writer
    type: llm
    provider: openai_smart  # Smart model for generation
  
  - id: summarizer
    type: llm
    provider: local_llm  # Local model for summarization
```

## Provider Return Format

Factory functions should return a dict with:

```python
{
    "client": client_instance,    # LLM client
    "model": "model-name",         # Model identifier
    "config": dict(provider.config)  # Original config
}
```

This allows components to access:
- `provider_instance["client"]` - The LLM client
- `provider_instance["model"]` - Model name
- `provider_instance["config"]` - Provider config

## Environment Variables

Use environment variables for sensitive data:

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
```

```bash
export OPENAI_API_KEY=sk-...
```

## Best Practices

1. **Use Environment Variables** - Never hardcode API keys
2. **Set Reasonable Timeouts** - Prevent hanging requests
3. **Configure Retries** - Handle transient failures
4. **Use Local LLMs for Development** - Reduce costs
5. **Separate Fast/Smart Models** - Optimize cost and latency

## Examples

See [examples/01_basic_llm/](../../examples/01_basic_llm/) for working code.

## Next Steps

- Learn about [Custom Logic Nodes](./custom_logic_node.md)
- See [Chat History](./chat_history.md) for conversation management
- Read [YAML Reference](./yaml_reference.md) for complete spec

