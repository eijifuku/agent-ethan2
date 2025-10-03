# チャット履歴

AgentEthan2におけるマルチターン会話管理。

## 概要

AgentEthan2は会話履歴の組み込みサポートを提供し、複数のターンにわたってエージェントがコンテキストを維持できるようにします。履歴システムは：

- **プラガブル** - 複数のバックエンドオプション（Memory、Redis、カスタム）
- **柔軟** - エージェントごとに複数の履歴インスタンス
- **設定可能** - YAMLベースの設定
- **セッション対応** - セッション/ユーザーごとに個別の履歴

## クイックスタート

### 1. YAMLで履歴を定義

```yaml
histories:
  - id: main_chat
    backend:
      type: memory
      max_turns: 20
    system_message: "You are a helpful assistant."
```

### 2. ノードで使用

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

### 3. エージェントを実行

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

## 履歴の設定

### YAML定義

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

### バックエンドタイプ

#### Memoryバックエンド（開発用）

```yaml
histories:
  - id: dev_chat
    backend:
      type: memory
      max_turns: 20
    system_message: "You are helpful."
```

**利点:**
- シンプル、セットアップ不要
- 高速

**欠点:**
- 再起動で失われる
- プロセス間で共有されない

#### Redisバックエンド（本番用）

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

**利点:**
- 再起動後も永続化
- プロセス間で共有
- 自動有効期限（TTL）

**欠点:**
- Redisサーバーが必要
- ネットワークオーバーヘッド

### レガシー `graph.history`（非推奨）

後方互換性のため、旧フォーマットである `graph.history` も引き続き読み込まれます（`agent_ethan2/ir/model.py:479-510`）。新しいプロジェクトでは `histories` セクションを推奨しますが、既存設定は以下のように動作します。

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

`graph.history` と `histories` を同時に指定した場合は、`histories` に定義した履歴が優先されます。移行時は `history_id` を利用するよう順次更新してください。

---

## 複数の履歴インスタンス

異なるコンテキスト用に複数の履歴を定義：

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

### 異なる履歴へのルーティング

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

## ノード設定

### 履歴を有効化

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

### 設定フィールド

| フィールド | 型 | 説明 |
|-------|------|-------------|
| `use_history` | boolean | このノードで履歴を有効化 |
| `history_id` | string | 履歴インスタンスへの参照 |
| `session_id_key` | string | セッションIDの状態/入力キー（デフォルト: `session_id`） |

---

## ファクトリー実装

### 基本実装

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

## セッション管理

### セッションIDの渡し方

**状態経由**:
```python
result = agent.run_sync(
    inputs={"user_message": "Hello"},
    initial_state={"session_id": "user_123"}
)
```

**入力経由**:
```python
result = agent.run_sync({
    "user_message": "Hello",
    "session_id": "user_123"
})
```

### セッションIDの解決順序

セッションIDは次の順序で解決されます：
1. `inputs[session_id_key]`
2. `state[session_id_key]`
3. `component.config.session_id`（静的フォールバック）
4. `"default"`

---

## バックエンドAPI

### バックエンドの作成

```python
from agent_ethan2.runtime.history_backend import create_history_backend

backend = create_history_backend({
    "type": "memory",
    "max_turns": 20
})
```

### 履歴の取得

```python
messages = await backend.get_history("session_123")
# Returns: [{"role": "user", "content": "..."}, ...]
```

### メッセージの追加

```python
await backend.append_message(
    session_id="session_123",
    role="user",
    content="Hello"
)
```

### 履歴のクリア

```python
await backend.clear_history("session_123")
```

---

## カスタムバックエンド

`HistoryBackend`プロトコルを実装します：

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

ファクトリーに登録：

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

## ベストプラクティス

1. **本番環境ではRedisを使用** - 永続的でマルチプロセス対応の履歴用
2. **TTLを設定** - 無期限のストレージ増加を防ぐ
3. **max_turnsを制限** - コンテキストウィンドウサイズを制御
4. **ユーザーごとのセッション** - セッションIDとしてユーザーIDを使用
5. **システムメッセージ** - システムメッセージにロール/ペルソナを含める

---

## サンプル

動作するコードについては [Example 10: Conversation History](../../examples/10_conversation_history/) を参照してください。

---

## 次のステップ

- [フックメソッド](./hook_methods.md) について学ぶ
- LLM設定については [プロバイダー](./providers.md) を参照
- 完全な仕様については [YAMLリファレンス](./yaml_reference.md) を参照
