# Chat History

Multi-turn conversation management in AgentEthan2.

## Overview

AgentEthan2 provides built-in support for conversation history, allowing your agents to maintain context across multiple turns. The history system is:

- **Pluggable** - Multiple backend options (Memory, Redis, custom)
- **Flexible** - Multiple history instances per agent
- **Configurable** - YAML-based configuration
- **Session-aware** - Separate histories per session/user

## Quick Start

### 1. Define History in YAML

```yaml
histories:
  - id: main_chat
    backend:
      type: memory
      max_turns: 20
    system_message: "You are a helpful assistant."
```

### 2. Use in Component

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
      history_id: main_chat
      session_id_key: session_id
```

### 3. Run Agent

```python
from agent_ethan2.agent import AgentEthan

agent = AgentEthan("config.yaml")

# Turn 1
result = agent.run_sync({
    "user_message": "My name is Alice",
    "session_id": "user_123"
})

# Turn 2 - Agent remembers Alice
result = agent.run_sync({
    "user_message": "What's my name?",
    "session_id": "user_123"
})
# Output: "Your name is Alice"
```

---

## History Configuration

### YAML Definition

```yaml
histories:
  - id: string               # Required: unique identifier
    backend:                 # Optional: backend config
      type: memory | redis   # Backend type
      url: string            # Redis URL (redis only)
      key_prefix: string     # Redis key prefix
      max_turns: integer     # Max conversation turns
      ttl: integer           # TTL in seconds (redis)
    system_message: string   # Optional: system message
```

### Backend Types

#### Memory Backend (Development)

```yaml
histories:
  - id: dev_chat
    backend:
      type: memory
      max_turns: 20
    system_message: "You are helpful."
```

**Pros:**
- Simple, no setup required
- Fast

**Cons:**
- Lost on restart
- Not shared across processes

#### Redis Backend (Production)

```yaml
histories:
  - id: prod_chat
    backend:
      type: redis
      url: redis://localhost:6379/0
      key_prefix: "chat:"
      max_turns: 100
      ttl: 3600  # 1 hour expiration
    system_message: "You are helpful."
```

**Pros:**
- Persistent across restarts
- Shared across processes
- Auto-expiration (TTL)

**Cons:**
- Requires Redis server
- Network overhead

### Legacy `graph.history` (Deprecated)

For backward compatibility the loader still accepts the older `graph.history` block from YAML v1 (`agent_ethan2/ir/model.py:479-510`). New projects should use the `histories` section, but existing configs remain valid:

```yaml
graph:
  entry: chat
  history:
    enabled: true
    input_key: user_message
    output_key: assistant_reply
    max_turns: 10
    system_message: "You are a helpful assistant."
```

When both `graph.history` and `histories` are present, the dedicated history instances take precedence. Plan migrations by defining a `histories` entry and referencing it via `history_id`.

---

## Multiple History Instances

Define multiple histories for different contexts:

```yaml
histories:
  # General conversation
  - id: main_chat
    backend:
      type: memory
      max_turns: 20
    system_message: "You are a helpful assistant."
  
  # Code-specific context
  - id: code_context
    backend:
      type: memory
      max_turns: 10
    system_message: "You are a coding assistant. Be concise."
  
  # Short-term memory
  - id: short_term
    backend:
      type: memory
      max_turns: 3
    system_message: "Answer briefly."
```

### Route to Different Histories

```yaml
graph:
  entry: classify
  nodes:
    - id: classify
      type: router
      component: classifier
      next:
        general: general_chat
        code: code_chat
    
    - id: general_chat
      type: llm
      component: general_bot
      config:
        history_id: main_chat  # Use main history
    
    - id: code_chat
      type: llm
      component: code_bot
      config:
        history_id: code_context  # Use code history
```

---

## Component Configuration

### Enable History

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
      history_id: main_chat
      session_id_key: session_id  # Where to find session ID
```

### Config Fields

| Field | Type | Description |
|-------|------|-------------|
| `use_history` | boolean | Enable history for this component |
| `history_id` | string | Reference to history instance |
| `session_id_key` | string | State/input key for session ID (default: `session_id`) |

---

## Factory Implementation

### Basic Implementation

```python
from agent_ethan2.runtime.history_backend import create_history_backend

def llm_with_history_factory(component, provider_instance, tool_instance):
    client = provider_instance["client"]
    model = provider_instance["model"]
    
    use_history = component.config.get("use_history", False)
    history_id = component.config.get("history_id")
    
    # Cache backends to reuse across calls
    backend_cache = {}
    
    async def call(state, inputs, ctx):
        prompt = inputs.get("prompt", "")
        messages = [{"role": "user", "content": prompt}]
        
        if use_history and history_id:
            # Get history config from registries
            histories = ctx.get("registries", {}).get("histories", {})
            history_config = histories.get(history_id)
            
            if history_config:
                # Create or reuse backend
                if history_id not in backend_cache:
                    backend_cache[history_id] = create_history_backend(
                        history_config.backend
                    )
                backend = backend_cache[history_id]
                
                # Get session ID
                session_id_key = component.config.get("session_id_key", "session_id")
                session_id = (
                    inputs.get(session_id_key) or
                    state.get(session_id_key) or
                    "default"
                )
                
                # Retrieve history
                history_messages = await backend.get_history(session_id)
                
                # Build messages
                messages = []
                if history_config.system_message:
                    messages.append({
                        "role": "system",
                        "content": history_config.system_message
                    })
                messages.extend(history_messages)
                messages.append({"role": "user", "content": prompt})
                
                # Call LLM
                response = client.chat.completions.create(
                    model=model,
                    messages=messages
                )
                response_text = response.choices[0].message.content
                
                # Save to history
                await backend.append_message(session_id, "user", prompt)
                await backend.append_message(session_id, "assistant", response_text)
                
                return {
                    "choices": [{"text": response_text}],
                    "usage": response.usage.model_dump()
                }
        
        # No history - simple call
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return {
            "choices": [{"text": response.choices[0].message.content}],
            "usage": response.usage.model_dump()
        }
    
    return call
```

---

## Session Management

### Passing Session ID

**Via State**:
```python
result = agent.run_sync(
    inputs={"user_message": "Hello"},
    initial_state={"session_id": "user_123"}
)
```

**Via Inputs**:
```python
result = agent.run_sync({
    "user_message": "Hello",
    "session_id": "user_123"
})
```

### Session ID Sources

The session ID is resolved in this order:
1. `inputs[session_id_key]`
2. `state[session_id_key]`
3. `component.config.session_id` (static fallback)
4. `"default"`

---

## Backend API

### Create Backend

```python
from agent_ethan2.runtime.history_backend import create_history_backend

backend = create_history_backend({
    "type": "memory",
    "max_turns": 20
})
```

### Get History

```python
messages = await backend.get_history("session_123")
# Returns: [{"role": "user", "content": "..."}, ...]
```

### Append Message

```python
await backend.append_message(
    session_id="session_123",
    role="user",
    content="Hello"
)
```

### Clear History

```python
await backend.clear_history("session_123")
```

---

## Custom Backend

Implement the `HistoryBackend` protocol:

```python
from typing import Mapping, Sequence

class MyCustomBackend:
    """Custom history backend."""
    
    async def get_history(self, session_id: str) -> Sequence[Mapping[str, str]]:
        """Get conversation history for session."""
        # Your implementation
        pass
    
    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """Append message to history."""
        # Your implementation
        pass
    
    async def clear_history(self, session_id: str) -> None:
        """Clear history for session."""
        # Your implementation
        pass
```

Register in factory:

```python
def create_history_backend(config):
    backend_type = config.get("type")
    
    if backend_type == "my_custom":
        return MyCustomBackend(config)
    elif backend_type == "memory":
        return InMemoryHistoryBackend(config)
    # ...
```

---

## Best Practices

1. **Use Redis in Production** - For persistent, multi-process history
2. **Set TTL** - Prevent indefinite storage growth
3. **Limit max_turns** - Control context window size
4. **Per-User Sessions** - Use user IDs as session IDs
5. **System Messages** - Include role/persona in system message

---

## Examples

See [Example 10: Conversation History](../../examples/10_conversation_history/) for working code.

---

## Next Steps

- Learn about [Hook Methods](./hook_methods.md)
- See [Providers](./providers.md) for LLM configuration
- Read [YAML Reference](./yaml_reference.md) for complete spec
