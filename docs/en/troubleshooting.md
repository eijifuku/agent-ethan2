# Troubleshooting

Common issues and solutions.

## Import Errors

### ModuleNotFoundError: No module named 'agent_ethan2'

**Cause**: Package not installed or not in editable mode.

**Solution**:
```bash
cd agent-ethan2
pip install -e .
```

### ModuleNotFoundError: No module named 'openai'

**Cause**: Dependencies not installed.

**Solution**:
```bash
pip install -e .
# or
pip install openai langchain-core langchain-openai
```

## API Key Errors

### Missing API key (openai.AuthenticationError)

**Cause**: The OpenAI client could not find a valid API key.

**Solution**:
```bash
export OPENAI_API_KEY=your-api-key-here
```

Or set in code:
```python
import os
os.environ["OPENAI_API_KEY"] = "your-key"
```

### openai.AuthenticationError: Invalid API key

**Cause**: Invalid API key format or expired key.

**Solution**:
- Check API key is correct
- Verify key hasn't been revoked
- Check for extra spaces/newlines

## YAML Errors

### YamlValidationError: 'meta' is a required property

**Cause**: Missing required YAML section.

**Solution**: Ensure YAML has all required sections:
```yaml
meta:
  version: 2
runtime:
  engine: lc.lcel
  factories:
    # ...
providers:
  # ...
graph:
  # ...
```

### YamlValidationError: Additional properties are not allowed

**Cause**: Invalid field name in YAML.

**Solution**: Check [YAML Reference](./yaml_reference.md) for valid fields.

### jsonschema.exceptions.ValidationError

**Cause**: YAML doesn't match schema.

**Solution**:
- Validate against `schemas/yaml_v2.json`
- Check field types (string vs integer, etc.)
- Ensure required fields are present

## Factory Errors

### GraphBuilderError [ERR_PROVIDER_DEFAULT_MISSING]

**Cause**: A node requiring a provider could not resolve one. Typical messages include `Node 'ask' requires a provider but none was resolved` or `Provider 'openai' for node 'ask' is not available`.

**Solution**:
- Ensure the referenced provider ID exists in the `providers` section
- If relying on `runtime.defaults.provider`, confirm the provider ID is valid
- Verify the provider factory is registered under `runtime.factories.providers`

### ImportError: cannot import name 'provider_factory'

**Cause**: Factory function doesn't exist or wrong path.

**Solution**:
- Verify function exists in module
- Check import path is correct
- Ensure module is in PYTHONPATH

## Component Errors

### KeyError: 'client'

**Cause**: Provider factory didn't return expected structure.

**Solution**: Ensure factory returns dict with required keys:
```python
def provider_factory(provider):
    return {
        "client": client_instance,
        "model": "model-name",
        "config": dict(provider.config)
    }
```

### GraphBuilderError [ERR_NODE_TYPE]: Component 'xxx' referenced by node 'yyy' is undefined

**Cause**: A node points to a component ID that does not exist or failed to materialize.

**Solution**: Define the component in YAML or fix the component ID:
```yaml
components:
  - id: xxx
    type: llm
    provider: openai
```

## Graph Errors

### GraphBuilderError [ERR_GRAPH_ENTRY_NOT_FOUND]

**Cause**: `graph.entry` points to a node that does not exist. Error message: `Graph entry 'xxx' does not exist`.

**Solution**: Ensure the entry node is defined:
```yaml
graph:
  entry: my_node
  nodes:
    - id: my_node
      # ...
```

### Circular dependency detected

**Cause**: Node chain loops back to itself.

**Solution**: Check node connections, ensure no cycles.

## Runtime Errors

### asyncio.TimeoutError

**Cause**: Request took too long.

**Solution**: Increase timeout:
```yaml
providers:
  - id: openai
    type: openai
    config:
      timeout: 60  # seconds
```

### RateLimitError: Rate limit exceeded

**Cause**: Too many requests to API.

**Solution**: Configure rate limiting:
```yaml
policies:
  rate_limit:
    providers:
      - target: openai
        type: token_bucket
        capacity: 5
        refill_rate: 1.0
```

## Docker Issues

### docker-compose: command not found

**Solution**: Install Docker Compose or use `docker compose` (V2).

### Permission denied (docker)

**Solution**: Add user to docker group:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Container exits immediately

**Cause**: Missing environment variables or dependencies.

**Solution**:
- Check `docker-compose logs agent-ethan2-dev`
- Ensure `.env` file exists with required variables
- Verify Dockerfile builds successfully

## Performance Issues

### Slow execution

**Possible causes**:
- Large context window
- Many history turns
- Slow API responses

**Solutions**:
- Reduce `max_turns` in history
- Use faster model (gpt-4o-mini)
- Implement caching
- Use parallel execution

### High memory usage

**Cause**: Large conversation history in memory.

**Solution**: Use Redis backend with TTL:
```yaml
histories:
  - id: chat
    backend:
      type: redis
      url: redis://localhost:6379
      max_turns: 50
      ttl: 3600
```

## Testing Issues

### pytest: No module named 'agent_ethan2'

**Solution**: Install in editable mode:
```bash
pip install -e .
pytest
```

### Tests fail with API errors

**Cause**: Tests trying to call real APIs.

**Solution**: Mock API calls or skip integration tests:
```bash
pytest -m "not integration"
```

## Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Telemetry

Enable JSONL export to see execution flow:
```yaml
runtime:
  exporters:
    - type: jsonl
      path: debug.jsonl
```

Then inspect:
```bash
cat debug.jsonl | jq '.'
```

### Use Console Exporter

```yaml
runtime:
  exporters:
    - type: console
      color: true
      verbose: true
      filter_events:
        - graph.start
        - graph.finish
```

### Validate YAML

```bash
python -c "
import yaml
import json
from jsonschema import validate

with open('config.yaml') as f:
    config = yaml.safe_load(f)
with open('schemas/yaml_v2.json') as f:
    schema = json.load(f)

validate(config, schema)
print('YAML is valid')
"
```

## Getting Help

1. Check [Examples](./examples.md) for working code
2. Review [YAML Reference](./yaml_reference.md)
3. Read [Setup Guide](./setup.md)
4. Check GitHub Issues
5. Ask in community channels

## Common Patterns

### "It worked in examples but not in my code"

**Check**:
- YAML structure matches examples
- Factory functions follow same pattern
- Environment variables are set
- Imports are correct

### "Connection refused" or "Network error"

**Check**:
- API endpoint is correct
- Firewall/proxy settings
- API service is running (for local LLMs)

### "Unexpected output format"

**Check**:
- JSONPath expressions in outputs
- Component return format
- Output mappings in YAML

## Next Steps

- Review [Examples](./examples.md)
- Read [YAML Reference](./yaml_reference.md)
- Check [Setup Guide](./setup.md)
