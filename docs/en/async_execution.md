# Async Execution

Understanding async/await in AgentEthan2.

## Overview

AgentEthan2 is built on asyncio for efficient concurrent execution.

## Key Concepts

### Async Components

All components must be async:

```python
async def my_component(state, inputs, ctx):
    # Your async code
    result = await some_async_call()
    return {"result": result}
```

### Awaiting Results

Always `await` async calls:

```python
# Correct
result = await client.chat.completions.create(...)

# Wrong
result = client.chat.completions.create(...)  # Returns coroutine
```

## Parallel Execution

Use `parallel` node type for concurrent execution:

```yaml
graph:
  nodes:
    - id: parallel_step
      type: parallel
      next: [task1, task2, task3]  # All run concurrently
```

## Running Agent

### Sync API

```python
agent = AgentEthan("config.yaml")
result = agent.run_sync({"input": "..."})
```

### Async API

```python
agent = AgentEthan("config.yaml")
result = await agent.run({"input": "..."})
```

## Best Practices

1. **Always use async/await** in components
2. **Use parallel nodes** for independent tasks
3. **Don't block the event loop** - use async libraries
4. **Handle timeouts** with asyncio.timeout

## Examples

See all examples for async patterns.

