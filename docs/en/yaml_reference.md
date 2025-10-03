# YAML Definition Reference

Complete reference for AgentEthan2 YAML configuration.

## Table of Contents

- [Overview](#overview)
- [Top-Level Structure](#top-level-structure)
- [meta](#meta) - Metadata
- [runtime](#runtime) - Runtime configuration
- [providers](#providers) - LLM providers
- [tools](#tools) - Tool definitions  
- [components](#components) - Reusable components
- [graph](#graph) - Workflow graph
- [histories](#histories) - Conversation history
- [policies](#policies) - Retry, rate limiting, etc.

---

## Overview

AgentEthan2 uses YAML to define agent workflows. The YAML file consists of several sections that define metadata, providers, components, and the execution graph.

### Minimal Example

```yaml
meta:
  version: 2
  name: my-agent

runtime:
  engine: lc.lcel
  factories:
    providers:
      openai: my_agent.provider_factory
    components:
      llm: my_agent.llm_factory

providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini

components:
  - id: assistant
    type: llm
    provider: openai
    inputs:
      prompt: graph.inputs.user_message
    outputs:
      response: $.choices[0].text

graph:
  entry: ask
  nodes:
    - id: ask
      type: llm
      component: assistant
  outputs:
    - key: final_response
      node: ask
      output: response
```

---

## Top-Level Structure

```yaml
meta:              # Required: Metadata about the agent
runtime:           # Required: Runtime configuration
providers:         # Required: LLM provider definitions
tools:             # Optional: Tool definitions
components:        # Optional: Component definitions
graph:             # Required: Execution graph
histories:         # Optional: Conversation history configs
policies:          # Optional: Retry, rate limit policies
```

---

## meta

Metadata about the agent configuration.

### Schema

```yaml
meta:
  version: 2                    # Required: integer, must be 2
  name: string                  # Optional: agent name
  description: string           # Optional: agent description
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | integer | Yes | YAML schema version, must be `2` |
| `name` | string | No | Human-readable agent name |
| `description` | string | No | Agent description |

### Example

```yaml
meta:
  version: 2
  name: customer-support-agent
  description: AI agent for customer support queries
```

---

## runtime

Runtime configuration for the agent execution.

### Schema

```yaml
runtime:
  engine: string                # Required: execution engine
  graph_name: string            # Optional: graph identifier
  defaults:                     # Optional: default values
    key: value
  factories:                    # Optional: factory function paths
    providers:
      type: path.to.function
    tools:
      type: path.to.function
    components:
      type: path.to.function
  exporters:                    # Optional: telemetry exporters
    - type: string
      path: string
      ...additional config
```

### Fields

#### `engine` (required)
- **Type**: string
- **Description**: Execution engine identifier
- **Common values**: `lc.lcel` (LangChain LCEL-compatible)

#### `graph_name` (optional)
- **Type**: string
- **Description**: Identifier for the graph (used in telemetry)
- **Default**: Auto-generated

#### `defaults` (optional)
- **Type**: object
- **Description**: Default values accessible to all components
- **Example**:
```yaml
runtime:
  defaults:
    temperature: 0.7
    max_tokens: 256
    provider: openai
```

#### `factories` (optional)
- **Type**: object
- **Description**: Maps types to factory function paths
- **Structure**:
  - `providers`: Map of provider type → factory path
  - `tools`: Map of tool type → factory path
  - `components`: Map of component type → factory path

**Example**:
```yaml
runtime:
  factories:
    providers:
      openai: my_agent.factories.openai_provider
      anthropic: my_agent.factories.anthropic_provider
    tools:
      calculator: my_agent.tools.calculator_factory
    components:
      llm: my_agent.components.llm_factory
      custom: my_agent.components.custom_factory
```

#### `exporters` (optional)
- **Type**: array of objects
- **Description**: Telemetry exporters for logging/monitoring
- **Common types**:
  - `jsonl`: JSON Lines file output
  - `console`: Console output
  - `langsmith`: LangSmith integration
  - `prometheus`: Prometheus metrics

**Example**:
```yaml
runtime:
  exporters:
    - type: jsonl
      path: run.jsonl
    - type: console
      color: true
      verbose: false
    - type: langsmith
      api_key: ${LANGSMITH_API_KEY}
      project_name: my-agent
    - type: prometheus
      port: 9090
```

---

## providers

LLM provider definitions.

### Schema

```yaml
providers:
  - id: string                  # Required: unique identifier
    type: string                # Required: provider type
    config:                     # Optional: provider-specific config
      key: value
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique provider identifier |
| `type` | string | Yes | Provider type (must match a factory) |
| `config` | object | No | Provider-specific configuration |

### Common Config Fields (OpenAI-compatible)

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini         # Model name
      api_key: ${OPENAI_API_KEY} # API key (or env var)
      base_url: http://...       # For local LLMs (Ollama, etc.)
      organization: org-xxx      # OpenAI organization
      timeout: 30                # Request timeout in seconds
      max_retries: 3             # Max retry attempts
```

### Examples

**OpenAI**:
```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
```

**Local LLM (Ollama)**:
```yaml
providers:
  - id: ollama
    type: openai
    config:
      model: llama2
      base_url: http://localhost:11434/v1
      api_key: dummy  # Ollama doesn't need real key
```

---

## tools

Tool definitions for use in components.

### Schema

```yaml
tools:
  - id: string                  # Required: unique identifier
    type: string                # Required: tool type
    provider: string            # Optional: provider reference
    config:                     # Optional: tool-specific config
      key: value
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique tool identifier |
| `type` | string | Yes | Tool type (must match a factory) |
| `provider` | string | No | Provider ID to use for this tool |
| `config` | object | No | Tool-specific configuration |

### Example

```yaml
tools:
  - id: calculator
    type: calculator
    config:
      precision: 2
  
  - id: web_search
    type: tavily_search
    config:
      api_key: ${TAVILY_API_KEY}
      max_results: 5
```

---

## components

Reusable component definitions.

### Schema

```yaml
components:
  - id: string                  # Required: unique identifier
    type: string                # Required: component type
    provider: string            # Optional: provider reference
    tool: string                # Optional: tool reference
    inputs:                     # Optional: input mappings
      key: expression
    outputs:                    # Optional: output mappings
      key: jsonpath
    config:                     # Optional: component config
      key: value
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique component identifier |
| `type` | string | Yes | Component type (must match a factory) |
| `provider` | string | No | Provider ID to use |
| `tool` | string | No | Tool ID to use |
| `inputs` | object | No | Input mappings (expression → value) |
| `outputs` | object | No | Output mappings (key → JSONPath) |
| `config` | object | No | Component-specific configuration |

### Input Expressions

Inputs support several expression types:

- **Graph inputs**: `graph.inputs.key`
- **Node outputs**: `node.step_id.output_key`
- **Constants**: `const:my-string`
- **Literal values**: `"literal string"`, `42`, `false`

### Output Expressions (JSONPath)

Outputs use JSONPath to extract data from component results:

- `$.choices[0].text` - First choice text
- `$.choices[0].message.content` - Message content
- `$.data.result` - Nested field
- `$` - Entire output

### Example

```yaml
components:
  - id: assistant
    type: llm
    provider: openai
    inputs:
      prompt: graph.inputs.user_message
    outputs:
      response: $.choices[0].text
      usage: $.usage
    config:
      temperature: 0.7
      max_output_tokens: 256
  
  - id: calculator
    type: tool
    tool: calc
    inputs:
      operation: graph.inputs.operation
      operands: graph.inputs.operands
    outputs:
      result: $.result
```

---

## graph

Execution graph definition.

### Schema

```yaml
graph:
  entry: string                 # Required: entry node ID
  nodes:                        # Required: list of nodes
    - id: string                # Required: node identifier
      type: string              # Required: node type
      component: string         # Required: component reference
      next: string | array | object  # Optional: next node(s)
      condition: string         # Optional: condition expression
      inputs:                   # Optional: input overrides
        key: expression
      outputs:                  # Optional: output overrides
        key: jsonpath
      config:                   # Optional: node-level config
        key: value
  outputs:                      # Optional: graph outputs
    - key: string               # Required: output key
      node: string              # Required: source node
      output: string            # Required: output field
```

### Node Types

| Type | Description |
|------|-------------|
| `llm` | LLM call |
| `tool` | Tool execution |
| `router` | Conditional routing |
| `map` | Map over collection |
| `parallel` | Parallel execution |
| `component` | Generic Python component |

### Next Field

The `next` field determines flow:

**Single next node**:
```yaml
nodes:
  - id: step1
    type: llm
    component: assistant
    next: step2
```

**Multiple next nodes (parallel)**:
```yaml
nodes:
  - id: step1
    type: llm
    component: assistant
    next: [step2, step3]  # Both execute in parallel
```

**Conditional next (router)**:
```yaml
nodes:
  - id: router
    type: router
    component: classifier
    next:
      greet: greeting_handler
      question: question_handler
      default: fallback_handler
```

### Examples

**Simple Linear Graph**:
```yaml
graph:
  entry: ask
  nodes:
    - id: ask
      type: llm
      component: assistant
  outputs:
    - key: response
      node: ask
      output: response
```

**Multi-Step Graph**:
```yaml
graph:
  entry: classify
  nodes:
    - id: classify
      type: router
      component: classifier
      next:
        search: web_search
        calc: calculator
        chat: chatbot
    
    - id: web_search
      type: tool
      component: search_tool
      next: summarize
    
    - id: calculator
      type: tool
      component: calc_tool
      next: format_result
    
    - id: chatbot
      type: llm
      component: chat_llm
  
  outputs:
    - key: final_answer
      node: summarize
      output: result
```

---

## histories

Conversation history configurations.

### Schema

```yaml
histories:
  - id: string                  # Required: history identifier
    backend:                    # Optional: backend config
      type: memory | redis      # Backend type
      url: string               # Redis URL (for redis type)
      key_prefix: string        # Redis key prefix
      max_turns: integer        # Max conversation turns
      ttl: integer              # TTL in seconds (redis)
    system_message: string      # Optional: system message
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique history identifier |
| `backend.type` | string | No | Backend type: `memory` or `redis` |
| `backend.max_turns` | integer | No | Maximum turns to keep |
| `backend.ttl` | integer | No | TTL in seconds (Redis only) |
| `system_message` | string | No | System message prepended to history |

### Examples

**In-Memory History**:
```yaml
histories:
  - id: main_chat
    backend:
      type: memory
      max_turns: 20
    system_message: "You are a helpful assistant."
```

**Redis History**:
```yaml
histories:
  - id: persistent_chat
    backend:
      type: redis
      url: redis://localhost:6379/0
      key_prefix: "chat:"
      max_turns: 100
      ttl: 3600
    system_message: "You are a helpful assistant."
```

**Multiple Histories**:
```yaml
histories:
  - id: main_chat
    backend:
      type: memory
      max_turns: 20
    system_message: "You are helpful."
  
  - id: code_context
    backend:
      type: memory
      max_turns: 10
    system_message: "You are a coding assistant."
```

### Using History in Components

Reference history in component config:

```yaml
components:
  - id: chatbot
    type: llm
    provider: openai
    inputs:
      prompt: graph.inputs.user_message
    outputs:
      response: $.choices[0].text
    config:
      use_history: true
      history_id: main_chat  # Reference to history
      session_id_key: session_id  # State key for session ID
```

---

## policies

Execution policies (retry, rate limiting, etc.)

### Schema

```yaml
policies:
  retry:                        # Retry policy
    default:
      max_attempts: integer
      backoff: string           # exponential, linear, constant
    overrides:
      - target: string          # Node ID
        max_attempts: integer
        backoff: string
  
  rate_limit:                   # Rate limiting
    providers:
      - target: string          # Provider ID
        type: token_bucket | fixed_window
        capacity: integer       # Bucket capacity
        refill_rate: number     # Tokens per second
    nodes:
      - target: string          # Node ID
        type: token_bucket | fixed_window
        limit: integer
        window: number          # Window in seconds
    shared_providers:
      provider_id: shared_name  # Share limits across providers
  
  masking:                      # Data masking (implementation-specific)
    patterns:
      - pattern: regex
        replacement: string
  
  error:                        # Error handling (implementation-specific)
    on_error: continue | stop
```

### Examples

**Retry Policy**:
```yaml
policies:
  retry:
    default:
      max_attempts: 3
      backoff: exponential
    overrides:
      - target: critical_node
        max_attempts: 5
        backoff: exponential
```

**Rate Limiting**:
```yaml
policies:
  rate_limit:
    providers:
      - target: openai
        type: token_bucket
        capacity: 10
        refill_rate: 1.0  # 1 token per second
    
    nodes:
      - target: expensive_node
        type: fixed_window
        limit: 5
        window: 60  # 5 requests per 60 seconds
```

---

## Complete Example

```yaml
meta:
  version: 2
  name: full-featured-agent
  description: Complete example showing all features

runtime:
  engine: lc.lcel
  graph_name: full_agent
  defaults:
    temperature: 0.7
  factories:
    providers:
      openai: agent.factories.openai_provider
    components:
      llm: agent.factories.llm_component
      router: agent.factories.router_component
    tools:
      search: agent.tools.search_tool
  exporters:
    - type: jsonl
      path: run.jsonl
    - type: console
      color: true
      verbose: false

providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}

tools:
  - id: web_search
    type: tavily_search
    config:
      api_key: ${TAVILY_API_KEY}

histories:
  - id: main_chat
    backend:
      type: memory
      max_turns: 20
    system_message: "You are a helpful assistant."

components:
  - id: classifier
    type: router
    provider: openai
    inputs:
      text: graph.inputs.user_message
    outputs:
      route: $.route
  
  - id: chatbot
    type: llm
    provider: openai
    inputs:
      prompt: graph.inputs.user_message
    outputs:
      response: $.choices[0].text
    config:
      use_history: true
      history_id: main_chat
  
  - id: searcher
    type: tool
    tool: web_search
    inputs:
      query: graph.inputs.user_message
    outputs:
      results: $.results

graph:
  entry: classify
  nodes:
    - id: classify
      type: router
      component: classifier
      next:
        chat: chatbot
        search: search_and_answer
    
    - id: chatbot
      type: llm
      component: chatbot
    
    - id: search_and_answer
      type: tool
      component: searcher
  
  outputs:
    - key: final_response
      node: chatbot
      output: response

policies:
  retry:
    default:
      max_attempts: 3
      backoff: exponential
  
  rate_limit:
    providers:
      - target: openai
        type: token_bucket
        capacity: 10
        refill_rate: 1.0
```

---

## Next Steps

- See [Providers](./providers.md) for provider configuration
- See [Nodes](./nodes.md) for node type details
- See [Examples](./examples.md) for working code
