# Example 09: Component Lifecycle Hooks

This example demonstrates the lifecycle hook system that allows components to execute custom logic before, after, and during error handling.

## Overview

Component hooks provide a clean way to add cross-cutting concerns to your components:

- **`before_execute`**: Called before component execution (logging, validation, input transformation)
- **`after_execute`**: Called after successful execution (logging, caching, output transformation)
- **`on_error`**: Called when execution fails (error logging, alerting, recovery)

## Hook Signature

```python
from typing import Any, Mapping, Optional

class ComponentHooks(Protocol):
    async def before_execute(
        self,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Optional[Mapping[str, Any]]:
        """
        Execute before main logic.
        
        Returns:
            Modified inputs (or None to use original)
        """
        ...
    
    async def after_execute(
        self,
        result: Any,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> Optional[Any]:
        """
        Execute after main logic.
        
        Returns:
            Modified result (or None to use original)
        """
        ...
    
    async def on_error(
        self,
        error: Exception,
        inputs: Mapping[str, Any],
        ctx: Mapping[str, Any]
    ) -> None:
        """Handle errors (cannot modify)."""
        ...
```

## Context Object

The `ctx` parameter provides execution context:

```python
ctx = {
    "node_id": str,           # Current node ID
    "graph_name": str,        # Graph name
    "config": dict,           # Node configuration
    "emit": callable,         # Event emitter
    "cancel_token": object,   # Cancellation token
    "deadline": float|None,   # Execution deadline
    "registries": dict,       # Registry instances
}
```

## Examples

### 1. Logging Hooks

Run the basic example with logging hooks:

```bash
docker-compose exec agent-ethan2-dev python3 examples/09_hooks/run.py
```

**Output:**
```
============================================================
[process_llm] 🚀 BEFORE EXECUTE
============================================================
  Prompt: Explain Python decorators in one sentence.
  Model: gpt-4o-mini

============================================================
[process_llm] ✅ AFTER EXECUTE
============================================================
  Response: Python decorators are a syntactic feature...
  Duration: 1.722s

📊 Metadata (added by after_execute hook):
  {
    "node_id": "process_llm",
    "duration": 1.7217621803283691,
    "model": "gpt-4o-mini"
  }
```

### 2. Error Handling Hooks

Run the error handling example:

```bash
docker-compose exec agent-ethan2-dev python3 examples/09_hooks/run_error.py
```

**Output:**
```
============================================================
[process_llm] ❌ ERROR
============================================================
  Error: AuthenticationError: Error code: 401
  Inputs: {'prompt': 'This will fail...'}
```

## Implementation

### LoggingLLM Component

```python
class LoggingLLM:
    async def before_execute(self, inputs, ctx):
        print(f"[{ctx['node_id']}] 🚀 BEFORE EXECUTE")
        # Add timestamp to inputs
        return {**inputs, "_started_at": time.time()}
    
    async def after_execute(self, result, inputs, ctx):
        duration = time.time() - inputs.get('_started_at', 0)
        print(f"[{ctx['node_id']}] ✅ Duration: {duration:.3f}s")
        # Add metadata to result
        return {**result, "_metadata": {"duration": duration}}
    
    async def on_error(self, error, inputs, ctx):
        print(f"[{ctx['node_id']}] ❌ ERROR: {error}")
        # Send alert (in production)
    
    async def __call__(self, state, inputs, ctx):
        # Main logic
        return await self.execute(state, inputs, ctx)
```

### CachedComponent

```python
class CachedComponent:
    def __init__(self):
        self.cache = {}
    
    async def before_execute(self, inputs, ctx):
        cache_key = json.dumps(inputs, sort_keys=True)
        if cache_key in self.cache:
            ctx['_cached_result'] = self.cache[cache_key]
            print("💾 Cache HIT")
        return None
    
    async def after_execute(self, result, inputs, ctx):
        if '_cached_result' not in ctx:
            cache_key = json.dumps(inputs, sort_keys=True)
            self.cache[cache_key] = result
            print("💾 Cached result")
        return None
    
    async def __call__(self, state, inputs, ctx):
        if '_cached_result' in ctx:
            return ctx['_cached_result']
        # Expensive computation
        return await expensive_operation(inputs)
```

## Use Cases

### 1. Input Validation

```python
async def before_execute(self, inputs, ctx):
    if 'required_field' not in inputs:
        raise ValueError("Missing required_field")
    return inputs
```

### 2. Performance Monitoring

```python
async def after_execute(self, result, inputs, ctx):
    duration = time.time() - inputs.get('_started_at', 0)
    metrics.record(f"node.{ctx['node_id']}.duration", duration)
    return result
```

### 3. Error Notification

```python
async def on_error(self, error, inputs, ctx):
    await slack.send_alert(
        channel="#alerts",
        message=f"Component {ctx['node_id']} failed: {error}"
    )
```

### 4. Response Caching

```python
async def before_execute(self, inputs, ctx):
    cached = await redis.get(cache_key(inputs))
    if cached:
        ctx['_cached'] = cached
    return inputs

async def after_execute(self, result, inputs, ctx):
    if '_cached' not in ctx:
        await redis.set(cache_key(inputs), result, ttl=3600)
    return result
```

### 5. Retry Logic Enhancement

```python
async def on_error(self, error, inputs, ctx):
    # Log error with context
    logger.error(f"Attempt failed", extra={
        "node_id": ctx['node_id'],
        "error": str(error),
        "inputs": inputs
    })
    # The retry policy will handle the actual retry
```

## Files

- `run.py` - Normal execution with logging hooks
- `run_error.py` - Error handling demonstration
- `config.yaml` - Configuration for normal execution
- `config_error.yaml` - Configuration for error testing
- `components/hooked_llm.py` - LoggingLLM and CachedComponent implementations
- `factories.py` - Factory functions for components

## Key Points

1. **All hooks are optional** - Implement only what you need
2. **Hooks run in order** - `before_execute` → main logic → `after_execute`
3. **`on_error` runs before retry** - Called on every failed attempt
4. **Return `None` to keep original** - Or return modified data
5. **Context sharing** - Use `ctx` dict to share data between hooks
6. **Exceptions in hooks are silenced** - To prevent infinite error loops

## Related Examples

- [Example 05: Retry/Rate Limit](../05_retry_ratelimit/) - Retry policies work with hooks
- [Example 06: Custom Component](../06_component/) - Custom components can use hooks
- [Example 07: Full Agent](../07_full_agent/) - Production-ready agent with hooks

