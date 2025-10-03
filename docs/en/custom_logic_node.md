# Custom Logic Nodes

Creating custom components with Python functions.

## Overview

Custom components allow you to implement any logic in Python:
- Data transformation
- API calls
- Database queries
- Business logic
- Integration with external services

## Quick Start

### 1. Define Component

```yaml
components:
  - id: my_custom
    type: custom_logic
    tool: calc_helper              # Optional tool reference
    inputs:
      data: graph.inputs.input_data
    outputs:
      result: $.processed
    config:
      function_path: my_agent.logic.process_data
```

The `type` must match a key registered under `runtime.factories.components`. Optional `provider` and `tool` fields expose resolved instances to your factory, letting you reuse LLM clients or tool wrappers (`agent_ethan2/registry/resolver.py:93-113`).

### 2. Implement Function

```python
# my_agent/logic.py
async def process_data(state, inputs, ctx):
    """Process input data."""
    data = inputs.get("data", [])
    
    # Your custom logic
    processed = [item.upper() for item in data]
    
    return {
        "processed": processed,
        "count": len(processed)
    }
```

### 3. Register Factory

```yaml
runtime:
  factories:
    components:
      custom_logic: my_agent.factories.custom_component_factory
```

```python
# my_agent/factories.py
import importlib

def custom_component_factory(component, provider_instance, tool_instance):
    """Load and return custom function."""
    config = component.config
    function_path = config.get("function_path")

    if not function_path:
        raise ValueError("function_path required for custom components")
    
    # Import function
    module_path, function_name = function_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    function = getattr(module, function_name)
    
    return function
```

```yaml
graph:
  nodes:
    - id: process
      type: component
      component: my_custom
      inputs:
        payload: graph.inputs.payload
      outputs:
        result: $.result
```

## Function Signature

```python
async def my_function(
    state: Mapping[str, Any],
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any]
) -> Mapping[str, Any]:
    """
    Custom component function.
    
    Args:
        state: Graph state (read-only)
        inputs: Component inputs
        ctx: Execution context
    
    Returns:
        Component outputs (dict)
    """
    # Your logic here
    return {"result": "..."}
```

### Parameters

- **state**: Graph state (session_id, history, etc.)
- **inputs**: Component inputs from YAML mappings
- **ctx**: Context (node_id, config, emit, cancel_token, etc.)

### Return Value

Return a dict with component outputs:

```python
return {
    "field1": "value1",
    "field2": 42,
    "field3": ["array", "values"]
}
```

## Examples

### Data Transformation

```python
async def transform_data(state, inputs, ctx):
    """Transform input data."""
    items = inputs.get("items", [])
    
    transformed = [
        {
            "id": item["id"],
            "name": item["name"].upper(),
            "processed": True
        }
        for item in items
    ]
    
    return {"transformed": transformed}
```

### API Call

```python
import aiohttp

async def fetch_weather(state, inputs, ctx):
    """Fetch weather data."""
    city = inputs.get("city", "London")
    api_key = ctx.get("config", {}).get("api_key")
    
    async with aiohttp.ClientSession() as session:
        url = f"https://api.weather.com/v1/weather?city={city}&key={api_key}"
        async with session.get(url) as response:
            data = await response.json()
    
    return {
        "temperature": data["temp"],
        "conditions": data["conditions"],
        "forecast": data["forecast"]
    }
```

### Database Query

```python
async def query_database(state, inputs, ctx):
    """Query database."""
    user_id = inputs.get("user_id")
    
    # Assuming db connection in ctx
    db = ctx.get("db")
    
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id
        )
    
    return {
        "user": dict(row) if row else None,
        "found": row is not None
    }
```

### Business Logic

```python
async def calculate_price(state, inputs, ctx):
    """Calculate order price with discounts."""
    items = inputs.get("items", [])
    user_tier = inputs.get("user_tier", "bronze")
    
    # Calculate base price
    subtotal = sum(item["price"] * item["quantity"] for item in items)
    
    # Apply tier discount
    discounts = {"bronze": 0, "silver": 0.05, "gold": 0.10, "platinum": 0.15}
    discount = discounts.get(user_tier, 0)
    total = subtotal * (1 - discount)
    
    return {
        "subtotal": subtotal,
        "discount": discount,
        "total": total,
        "savings": subtotal - total
    }
```

## Using Providers

Access provider instances in custom components:

```python
def custom_with_llm_factory(component, provider_instance, tool_instance):
    """Custom component that uses LLM."""
    client = provider_instance["client"]
    model = provider_instance["model"]
    
    async def custom_logic(state, inputs, ctx):
        text = inputs.get("text", "")
        
        # Use LLM
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"Analyze: {text}"}]
        )
        analysis = response.choices[0].message.content
        
        # Custom processing
        result = {
            "analysis": analysis,
            "length": len(text),
            "word_count": len(text.split())
        }
        
        return result
    
    return custom_logic
```

## Using Tools

Access tool instances:

```python
def custom_with_tool_factory(component, provider_instance, tool_instance):
    """Custom component that uses a tool."""
    
    async def custom_logic(state, inputs, ctx):
        query = inputs.get("query", "")
        
        # Use tool
        tool_result = await tool_instance(query)
        
        # Process result
        processed = {
            "raw": tool_result,
            "summary": tool_result[:100],
            "found": bool(tool_result)
        }
        
        return processed
    
    return custom_logic
```

## Error Handling

```python
async def safe_custom_logic(state, inputs, ctx):
    """Custom logic with error handling."""
    try:
        data = inputs.get("data")
        if not data:
            raise ValueError("data is required")
        
        # Process
        result = process(data)
        
        return {"result": result, "success": True}
    
    except Exception as e:
        # Log error
        print(f"Error in custom logic: {e}")
        
        # Return error state
        return {
            "result": None,
            "success": False,
            "error": str(e)
        }
```

## Best Practices

1. **Keep Functions Focused** - One responsibility per function
2. **Handle Errors Gracefully** - Don't let exceptions crash the agent
3. **Validate Inputs** - Check inputs before processing
4. **Use Async** - Always use `async def` for concurrent execution
5. **Document Well** - Add docstrings and type hints
6. **Test Independently** - Unit test your functions

## Examples

See [Example 06: Custom Components](../../examples/06_component/) for working code.

## Next Steps

- Learn about [Hook Methods](./hook_methods.md)
- See [Custom Tools](./custom_tools.md)
- Read [Examples](./examples.md)
