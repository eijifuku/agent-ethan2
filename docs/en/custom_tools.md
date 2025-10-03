# Custom Tools

Creating custom tools for your agent.

## Overview

Tools are reusable functions that components can call. Examples:
- Web search
- Calculator
- Database queries
- API calls
- File operations

## Quick Start

### 1. Define Tool

```yaml
tools:
  - id: calculator
    type: calculator
    provider: openai           # Optional: share a provider instance
    config:
      precision: 2
```

`provider` is optional. When present, AgentEthan passes the resolved provider instance to your tool factory so that you can reuse clients or credentials (`agent_ethan2/ir/model.py:291-303`).

### 2. Implement Factory

```python
def calculator_tool_factory(tool, provider_instance):
    """Create calculator tool."""
    precision = tool.config.get("precision", 2)
    client = provider_instance["client"] if provider_instance else None

    async def call(state, inputs, ctx):
        operation = inputs.get("operation")
        operands = inputs.get("operands", [])

        if operation == "add":
            total = sum(operands)
        elif operation == "multiply":
            total = 1
            for value in operands:
                total *= value
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return {
            "result": round(total, precision),
            "used_client": bool(client),
            "operation": operation,
        }

    return call

Tool factories must return a callable that accepts `(state, inputs, ctx)`—the same signature used by component callables—so that the scheduler can pass graph state, resolved inputs, and execution context.
```

### 3. Use in Component

```yaml
components:
  - id: calc_component
    type: tool
    tool: calculator
    inputs:
      operation: graph.inputs.op
      operands: graph.inputs.nums
    outputs:
      result: $.result
      operation: $.operation
```

Register the corresponding factory under `runtime.factories.tools.calculator` so the resolver can import it (`agent_ethan2/registry/resolver.py:63-83`).

## Examples

### Web Search Tool

```python
import aiohttp

def search_tool_factory(tool, provider_instance):
    api_key = tool.config.get("api_key")
    
    async def search(query, max_results=5):
        async with aiohttp.ClientSession() as session:
            url = f"https://api.search.com/search?q={query}&limit={max_results}"
            headers = {"Authorization": f"Bearer {api_key}"}
            async with session.get(url, headers=headers) as response:
                data = await response.json()
        
        return {
            "results": data.get("results", []),
            "count": len(data.get("results", []))
        }
    
    return search
```

### Database Tool

```python
def db_tool_factory(tool, provider_instance):
    connection_string = tool.config.get("connection_string")
    
    async def query(sql, params=None):
        async with asyncpg.connect(connection_string) as conn:
            rows = await conn.fetch(sql, *(params or []))
        
        return {
            "rows": [dict(row) for row in rows],
            "count": len(rows)
        }
    
    return query
```

## See Also

- [LangChain Tools](./using_langchain_tools.md)
- [Custom Logic Nodes](./custom_logic_node.md)
- [Examples](./examples.md)
