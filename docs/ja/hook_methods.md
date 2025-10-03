# フックメソッド

コンポーネント実行を細かく制御するためのライフサイクルフック。

## 概要

フックを使用すると、コンポーネント実行の重要なポイントでインターセプトできます：
- `before_execute` - コンポーネント実行前
- `after_execute` - コンポーネント完了後
- `on_error` - コンポーネント失敗時

## フックメソッド

### before_execute

コンポーネント実行前に呼び出されます。入力を変更できます。

```python
async def before_execute(
    self,
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any]
) -> Optional[Mapping[str, Any]]:
    """
    Called before component execution.
    
    Args:
        inputs: Component inputs
        ctx: Execution context
    
    Returns:
        Modified inputs (or None to keep original)
    """
    print(f"Executing with inputs: {inputs}")
    # Optional: modify inputs
    return {"modified_input": inputs.get("input") + "_modified"}
```

### after_execute

コンポーネント実行後に呼び出されます。結果を変更できます。

```python
async def after_execute(
    self,
    result: Any,
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any]
) -> Optional[Any]:
    """
    Called after component execution.
    
    Args:
        result: Component result
        inputs: Component inputs
        ctx: Execution context
    
    Returns:
        Modified result (or None to keep original)
    """
    print(f"Result: {result}")
    # Optional: modify result
    return {"enhanced_result": result}
```

### on_error

コンポーネントが失敗したときに呼び出されます。

```python
async def on_error(
    self,
    error: Exception,
    inputs: Mapping[str, Any],
    ctx: Mapping[str, Any]
) -> None:
    """
    Called when component execution fails.
    
    Args:
        error: The exception that occurred
        inputs: Component inputs
        ctx: Execution context
    """
    print(f"Error occurred: {error}")
    # Log error, send alert, etc.
```

## 実装

### クラスベースコンポーネント

```python
class LoggingLLM:
    """LLM with logging hooks."""
    
    def __init__(self, client, model):
        self.client = client
        self.model = model
    
    async def __call__(self, state, inputs, ctx):
        """Main execution."""
        prompt = inputs.get("prompt", "")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return {
            "choices": [{"text": response.choices[0].message.content}],
            "usage": response.usage.model_dump()
        }
    
    async def before_execute(self, inputs, ctx):
        """Log inputs before execution."""
        print(f"[{ctx.get('node_id')}] Input: {inputs.get('prompt')}")
        return None  # Don't modify inputs
    
    async def after_execute(self, result, inputs, ctx):
        """Log outputs after execution."""
        print(f"[{ctx.get('node_id')}] Output: {result.get('choices', [{}])[0].get('text')}")
        return None  # Don't modify result
    
    async def on_error(self, error, inputs, ctx):
        """Log errors."""
        print(f"[{ctx.get('node_id')}] Error: {error}")
```

### 関数ベースコンポーネントとフック

ラッパークラスを使用します：

```python
class ComponentWithHooks:
    def __init__(self, call_fn):
        self.call_fn = call_fn
    
    async def __call__(self, state, inputs, ctx):
        return await self.call_fn(state, inputs, ctx)
    
    async def before_execute(self, inputs, ctx):
        print(f"Before: {inputs}")
    
    async def after_execute(self, result, inputs, ctx):
        print(f"After: {result}")
    
    async def on_error(self, error, inputs, ctx):
        print(f"Error: {error}")

def component_factory(component, provider_instance, tool_instance):
    async def call(state, inputs, ctx):
        # Your logic
        return {"result": "..."}
    
    return ComponentWithHooks(call)
```

## ユースケース

### ロギング

```python
async def before_execute(self, inputs, ctx):
    logger.info(f"Executing {ctx['node_id']} with inputs: {inputs}")

async def after_execute(self, result, inputs, ctx):
    logger.info(f"{ctx['node_id']} completed: {result}")
```

### キャッシング

```python
class CachedComponent:
    def __init__(self, call_fn):
        self.call_fn = call_fn
        self.cache = {}
    
    async def __call__(self, state, inputs, ctx):
        return await self.call_fn(state, inputs, ctx)
    
    async def before_execute(self, inputs, ctx):
        # Check cache
        cache_key = str(inputs)
        if cache_key in self.cache:
            print(f"Cache hit: {cache_key}")
            # Return cached result as inputs to skip execution
            return {"_cached_result": self.cache[cache_key]}
    
    async def after_execute(self, result, inputs, ctx):
        # Store in cache
        if "_cached_result" not in inputs:
            cache_key = str(inputs)
            self.cache[cache_key] = result
        return result
```

### バリデーション

```python
async def before_execute(self, inputs, ctx):
    # Validate inputs
    if "required_field" not in inputs:
        raise ValueError("Missing required_field")
    
    # Sanitize inputs
    return {
        "sanitized_input": inputs.get("input", "").strip().lower()
    }
```

### エラー回復

```python
async def on_error(self, error, inputs, ctx):
    # Log to external service
    error_tracker.log(error, context=ctx)
    
    # Send alert
    if isinstance(error, CriticalError):
        alert_service.send(f"Critical error in {ctx['node_id']}")
```

## サンプル

動作するコードについては [Example 09: Hooks](../../examples/09_hooks/) を参照してください。

## ベストプラクティス

1. **フックをシンプルに保つ** - 複雑なロジックを追加しない
2. **エラーを飲み込まない** - on_errorでエラーを伝播させる
3. **変更がない場合はNoneを返す** - 変更された値のみを返す
4. **横断的関心事に使用** - ロギング、メトリクス、キャッシング

## 次のステップ

- [カスタムロジックノード](./custom_logic_node.md) を参照
- [チャット履歴](./chat_history.md) について学ぶ
- [サンプル](./examples.md) を参照
