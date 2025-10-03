# Example 10: Conversation History

## Overview

AgentEthan2 supports multiple conversation history instances with pluggable backends.

### Features

1. **Multiple History Instances** - Define multiple histories with different configurations
2. **Pluggable Backends** - Memory, Redis, or custom backends
3. **Node-level Selection** - Each node can use a specific history instance
4. **Backend Abstraction** - Easy to switch between storage backends

## YAML Configuration

### Define History Instances

```yaml
# Top-level histories definition
histories:
  # Main conversation history
  - id: main_chat
    backend:
      type: memory        # or 'redis'
      max_turns: 20       # Keep last 20 turns
    system_message: "You are a helpful assistant."
  
  # Code-specific history  
  - id: code_context
    backend:
      type: memory
      max_turns: 10
    system_message: "You are a code assistant."
  
  # Short-term memory
  - id: short_term
    backend:
      type: memory
      max_turns: 3
    system_message: "Answer briefly."
```

### Use History in Components

```yaml
components:
  # Main chatbot using main_chat history
  - id: main_bot
    type: llm_with_history
    provider: openai
    inputs:
      prompt: graph.inputs.user_message
    outputs:
      response: $.choices[0].text
    config:
      use_history: true
      history_id: main_chat  # Reference to history instance
  
  # Code assistant using code_context history
  - id: code_bot
    type: llm_with_history
    provider: openai
    inputs:
      prompt: graph.inputs.code_question
    outputs:
      response: $.choices[0].text
    config:
      use_history: true
      history_id: code_context  # Different history
```

## Backend Types

### In-Memory Backend (Development)

```yaml
histories:
  - id: chat
    backend:
      type: memory
      max_turns: 20  # Optional: limit history size
```

**Pros:**
- Simple, no external dependencies
- Fast

**Cons:**
- Lost on restart
- Not shared across processes

### Redis Backend (Production)

```yaml
histories:
  - id: chat
    backend:
      type: redis
      url: "redis://localhost:6379/0"
      key_prefix: "chat:"
      max_turns: 50
      ttl: 3600  # Expire after 1 hour
```

**Pros:**
- Persistent
- Shared across processes
- Auto-expiration (TTL)

**Cons:**
- Requires Redis server
- Network overhead

## Programmatic Usage

### Create Backend Instance

```python
from agent_ethan2.runtime.history_backend import (
    InMemoryHistoryBackend,
    RedisHistoryBackend,
    create_history_backend,
)

# In-memory
history = InMemoryHistoryBackend(max_turns=20)

# Redis
history = RedisHistoryBackend(
    redis_url="redis://localhost:6379/0",
    key_prefix="chat:",
    max_turns=50,
    ttl=3600,
)

# From config dict
history = create_history_backend({
    "type": "redis",
    "url": "redis://localhost:6379/0",
    "max_turns": 50,
})
```

### Use Backend

```python
# Get history for a session
messages = await history.get_history("session_123")

# Append message
await history.append_message(
    session_id="session_123",
    role="user",
    content="Hello!",
)

await history.append_message(
    session_id="session_123",
    role="assistant",
    content="Hi there!",
)

# Replace entire history
await history.set_history(
    session_id="session_123",
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ],
)

# Clear history
await history.clear_history("session_123")
```

## Component Implementation

### Factory with History Backend Support

```python
from agent_ethan2.runtime.history_backend import create_history_backend

def llm_with_history_factory(component, provider_instance, tool_instance):
    client = provider_instance["client"]
    model = provider_instance["model"]
    
    use_history = component.config.get("use_history", False)
    history_id = component.config.get("history_id")
    
    # Get history config from global IR (passed via context)
    async def call(state, inputs, ctx):
        prompt = inputs.get("prompt", "")
        
        if use_history and history_id:
            # Get history instance from registries
            history_config = ctx.get("registries", {}).get("histories", {}).get(history_id)
            
            if history_config:
                # Create backend from config
                backend = create_history_backend(history_config.backend)
                
                # Get session ID from state
                session_id = state.get("session_id", "default")
                
                # Retrieve history
                history_messages = await backend.get_history(session_id)
                
                # Build messages with history
                messages = []
                if history_config.system_message:
                    messages.append({
                        "role": "system",
                        "content": history_config.system_message
                    })
                messages.extend(history_messages)
                messages.append({"role": "user", "content": prompt})
            else:
                # Fallback: no history
                messages = [{"role": "user", "content": prompt}]
        else:
            messages = [{"role": "user", "content": prompt}]
        
        # Call LLM
        response = await call_llm(client, model, messages)
        
        # Save response to history
        if use_history and history_id and history_config:
            await backend.append_message(session_id, "user", prompt)
            await backend.append_message(session_id, "assistant", response)
        
        return {"text": response}
    
    return call
```

## Multi-History Example

```yaml
histories:
  - id: main
    backend: {type: memory, max_turns: 20}
    system_message: "You are helpful."
  
  - id: code
    backend: {type: memory, max_turns: 10}
    system_message: "You are a coder."

graph:
  entry: router
  nodes:
    # Route based on intent
    - id: router
      type: router
      component: classifier
      next:
        general: main_chat
        code: code_chat
    
    # Main chat with main history
    - id: main_chat
      type: llm
      component: main_bot  # uses history_id: main
    
    # Code chat with code history
    - id: code_chat
      type: llm
      component: code_bot  # uses history_id: code
```

**Result:**
- General questions use `main` history (20 turns)
- Code questions use `code` history (10 turns)
- Each maintains separate conversation context

## Custom Backend

Implement `HistoryBackend` interface:

```python
from agent_ethan2.runtime.history_backend import HistoryBackend

class DatabaseHistoryBackend(HistoryBackend):
    def __init__(self, db_url: str, table: str):
        self.db = connect(db_url)
        self.table = table
    
    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        rows = await self.db.query(
            f"SELECT role, content FROM {self.table} "
            f"WHERE session_id = ? ORDER BY created_at",
            session_id
        )
        return [{"role": r.role, "content": r.content} for r in rows]
    
    async def append_message(self, session_id: str, role: str, content: str):
        await self.db.execute(
            f"INSERT INTO {self.table} (session_id, role, content) VALUES (?, ?, ?)",
            session_id, role, content
        )
    
    # ... implement other methods
```

## Key Points

1. **Histories are defined globally** in `histories` section
2. **Nodes reference histories** via `history_id` in config
3. **Backends are pluggable** - memory, redis, custom
4. **Session management** is app responsibility (pass `session_id` in state)
5. **Auto-pruning** via `max_turns` or TTL

## Files

- `config.yaml` - Basic programmatic history example
- `config_multi_histories.yaml` - Multiple history instances with YAML definition
- `run.py` - Simple execution example
- `factories.py` - Factory with history backend support
- `README_v2.md` - This documentation

## Related Files

- `agent_ethan2/runtime/history_backend.py` - Backend abstraction layer
- `agent_ethan2/runtime/history.py` - Helper functions (legacy)
- `agent_ethan2/ir/model.py` - NormalizedHistory dataclass

