# Nodes

Understanding the building blocks of your agent workflow.

## What are Nodes?

Nodes are the execution units in your agent graph. Each node:
- Has a unique ID
- References a component
- Receives inputs
- Produces outputs
- Can connect to other nodes

## Node Types

AgentEthan2 supports multiple node types:

| Type | Description | Use Case |
|------|-------------|----------|
| `llm` | LLM call | Chat, generation, completion |
| `tool` | Tool execution | Search, calculation, API calls |
| `router` | Conditional routing | Intent classification, branching |
| `map` | Map over collection | Batch processing |
| `parallel` | Parallel execution | Concurrent operations |
| `component` | Generic Python component | Any custom logic |

---

## LLM Node

Executes an LLM component.

### Configuration

```yaml
graph:
  nodes:
    - id: ask_llm
      type: llm
      component: assistant
      inputs:
        prompt: graph.inputs.user_message
      outputs:
        response: $.choices[0].text
      config:
        temperature: 0.7
```

### Fields

- `component`: Reference to LLM component
- `inputs`: Input mappings
- `outputs`: Output mappings (JSONPath)
- `config`: Node-level configuration overrides

### Example

```yaml
components:
  - id: assistant
    type: llm
    provider: openai
    outputs:
      response: $.choices[0].text

graph:
  nodes:
    - id: chat
      type: llm
      component: assistant
      inputs:
        prompt: graph.inputs.message
```

---

## Tool Node

Executes a tool component.

### Configuration

```yaml
graph:
  nodes:
    - id: calculate
      type: tool
      component: calculator
      inputs:
        operation: graph.inputs.op
        operands: graph.inputs.nums
      outputs:
        result: $.result
```

### Example

```yaml
tools:
  - id: calc
    type: calculator

components:
  - id: calculator
    type: tool
    tool: calc
    outputs:
      result: $.result

graph:
  nodes:
    - id: compute
      type: tool
      component: calculator
      inputs:
        operation: graph.inputs.operation
        operands: graph.inputs.values
```

---

## Router Node

Conditional routing based on component output.

### Configuration

```yaml
graph:
  nodes:
    - id: classify
      type: router
      component: classifier
      next:
        greet: greeting_handler
        question: qa_handler
        default: fallback
```

### Next Field

The `next` field is an object where:
- **Keys** are route values (from component output)
- **Values** are target node IDs

### Example

```yaml
components:
  - id: classifier
    type: router
    provider: openai
    inputs:
      text: graph.inputs.user_message
    outputs:
      route: $.route  # Must output a 'route' field

graph:
  nodes:
    - id: classify
      type: router
      component: classifier
      next:
        greet: greet_node
        help: help_node
        default: fallback_node
    
    - id: greet_node
      type: llm
      component: greeter
    
    - id: help_node
      type: llm
      component: helper
    
    - id: fallback_node
      type: llm
      component: fallback
```

**Component Implementation**:

```python
async def router_factory(component, provider_instance, tool_instance):
    async def route(state, inputs, ctx):
        text = inputs.get("text", "")
        
        # Simple keyword matching
        if "hello" in text.lower():
            return {"route": "greet"}
        elif "help" in text.lower():
            return {"route": "help"}
        else:
            return {"route": "default"}
    
    return route
```

---

## Map Node

Execute component over each item in a collection.

### Configuration

```yaml
graph:
  nodes:
    - id: process_items
      type: map
      component: item_processor
      config:
        collection: graph.inputs.items  # Source collection
        failure_mode: continue          # continue | stop
        ordered: true                   # Preserve order
        result_key: processed_items     # Output key
```

### Config Fields

| Field | Type | Description |
|-------|------|-------------|
| `collection` | expression | Collection to map over |
| `failure_mode` | string | `continue` (skip errors) or `stop` (fail fast) |
| `ordered` | boolean | Preserve order (`true`) or allow reordering (`false`) |
| `result_key` | string | Key for output results |

### Example

```yaml
components:
  - id: item_processor
    type: map
    provider: openai
    inputs:
      item: current_item  # Special: current item
    outputs:
      processed: $.result

graph:
  nodes:
    - id: process_all
      type: map
      component: item_processor
      config:
        collection: graph.inputs.items
        failure_mode: continue
        ordered: true
        result_key: results
      next: summarize
    
    - id: summarize
      type: llm
      component: summarizer
      inputs:
        items: process_all.results
```

**Input**:
```python
agent.run_sync({
    "items": ["apple", "banana", "cherry"]
})
```

**Output**:
```python
{
    "results": [
        {"processed": "APPLE", "length": 5},
        {"processed": "BANANA", "length": 6},
        {"processed": "CHERRY", "length": 6}
    ]
}
```

---

## Parallel Node

Execute multiple nodes concurrently.

### Configuration

```yaml
graph:
  nodes:
    - id: parallel_step
      type: parallel
      component: parallel_handler
      next: [step2, step3, step4]  # All execute in parallel
```

### Next Field

The `next` field is an array of node IDs to execute in parallel.

### Example

```yaml
graph:
  nodes:
    - id: start
      type: llm
      component: input_processor
      next: [search, calculate, translate]  # Parallel
    
    - id: search
      type: tool
      component: web_search
      next: merge
    
    - id: calculate
      type: tool
      component: calculator
      next: merge
    
    - id: translate
      type: llm
      component: translator
      next: merge
    
    - id: merge
      type: llm
      component: merger
      inputs:
        search_results: search.results
        calc_result: calculate.result
        translation: translate.text
```

All three nodes (`search`, `calculate`, `translate`) execute concurrently.

---

## Component Node

Execute arbitrary Python logic via a component factory.

### Configuration

```yaml
graph:
  nodes:
    - id: custom_step
      type: component
      component: my_custom_logic
      inputs:
        data: graph.inputs.data
      outputs:
        result: $.output
```

### Example

```yaml
components:
  - id: my_custom_logic
    type: custom_logic            # Any factory key registered under runtime.factories.components
    provider: openai              # Optional
    tool: calc_helper             # Optional tool reference (define under `tools`)
    inputs:
      data: graph.inputs.input_data
    outputs:
      result: $.processed
    config:
      function_path: my_agent.logic.process_data

graph:
  nodes:
    - id: process
      type: component
      component: my_custom_logic
```

**Component Implementation**:

```python
# my_agent/logic.py
async def process_data(state, inputs, ctx):
    """Custom processing logic."""
    data = inputs.get("data", [])
    
    # Custom logic
    processed = [item.upper() for item in data]
    
    return {
        "processed": processed,
        "count": len(processed)
    }
```

---

## Node Connections

### Linear Flow

```yaml
graph:
  entry: step1
  nodes:
    - id: step1
      type: llm
      component: comp1
      next: step2
    
    - id: step2
      type: tool
      component: comp2
      next: step3
    
    - id: step3
      type: llm
      component: comp3
```

### Branching (Router)

```yaml
graph:
  entry: router
  nodes:
    - id: router
      type: router
      component: classifier
      next:
        route_a: handler_a
        route_b: handler_b
    
    - id: handler_a
      type: llm
      component: comp_a
    
    - id: handler_b
      type: llm
      component: comp_b
```

### Parallel Execution

```yaml
graph:
  entry: parallel_start
  nodes:
    - id: parallel_start
      type: parallel
      component: starter
      next: [task_a, task_b, task_c]
    
    - id: task_a
      type: llm
      component: comp_a
      next: merge
    
    - id: task_b
      type: tool
      component: comp_b
      next: merge
    
    - id: task_c
      type: llm
      component: comp_c
      next: merge
    
    - id: merge
      type: llm
      component: merger
```

---

## Input/Output Mappings

### Input Expressions

Nodes can reference:

- **Graph inputs**: `graph.inputs.key`
- **Node outputs**: `node.step1.output_key`
- **Constants**: `const:my-string`
- **Literals**: `"literal"`, `42`, `true`

Example:
```yaml
nodes:
  - id: step2
    type: llm
    component: comp
    inputs:
      user_input: graph.inputs.message
      previous_result: node.step1.response
      default_temp: 0.7
```

### Output Expressions (JSONPath)

Extract data from component results:

```yaml
outputs:
  text: $.choices[0].text
  usage: $.usage
  first_result: $.results[0]
  all_data: $
```

---

## Node Configuration

### Component-Level Config

Defined in `components`:

```yaml
components:
  - id: assistant
    type: llm
    provider: openai
    config:
      temperature: 0.7
      max_output_tokens: 256
```

### Node-Level Config

Overrides component config:

```yaml
graph:
  nodes:
    - id: chat
      type: llm
      component: assistant
      config:
        temperature: 0.9  # Override
        max_output_tokens: 512  # Override
```

---

## Best Practices

1. **Use Descriptive IDs** - `classify_intent` instead of `node1`
2. **Keep Nodes Focused** - One responsibility per node
3. **Leverage Parallel** - Use parallel execution for independent tasks
4. **Handle Errors** - Use retry policies and error handling
5. **Document Complex Logic** - Add descriptions to components

---

## Next Steps

- Learn about [Custom Logic Nodes](./custom_logic_node.md)
- See [Examples](./examples.md) for working code
- Read [YAML Reference](./yaml_reference.md) for complete spec
