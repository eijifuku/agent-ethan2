# カスタムロジックノード

Python関数を使ったカスタムロジックノードの作成方法。

## 概要

カスタムロジックノードでは、Python で任意のロジックを実装できます：
- データ変換
- API呼び出し
- データベースクエリ
- ビジネスロジック
- 外部サービスとの統合

## クイックスタート

### 1. ノードの定義

```yaml
components:
  - id: my_custom
    type: custom_logic
    tool: calc_helper                # 任意: ツール参照を共有
    inputs:
      data: graph.inputs.input_data
    outputs:
      result: $.processed
    config:
      function_path: my_agent.logic.process_data
```

`type` は `runtime.factories.components` に登録したキーと一致させる必要があります。`provider` や `tool` を指定すると、ファクトリーに解決済みインスタンスが渡されます（`agent_ethan2/registry/resolver.py:93-113`）。

### 2. 関数の実装

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

### 3. ファクトリーの登録

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

## 関数シグネチャ

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

### パラメータ

- **state**: グラフの状態（session_id、履歴など）
- **inputs**: YAML マッピングからのノード入力
- **ctx**: コンテキスト（node_id、config、emit、cancel_token など）

### 戻り値

ノードの出力を含む dict を返します：

```python
return {
    "field1": "value1",
    "field2": 42,
    "field3": ["array", "values"]
}
```

## サンプル

### データ変換

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

### API呼び出し

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

### データベースクエリ

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

### ビジネスロジック

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

## プロバイダーの使用

カスタムロジックノードでプロバイダーインスタンスにアクセスします：

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

## ツールの使用

ツールインスタンスにアクセスします：

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

## エラーハンドリング

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

## ベストプラクティス

1. **関数を集中させる** - 1つの関数に1つの責務
2. **エラーを適切に処理** - 例外でエージェントをクラッシュさせない
3. **入力をバリデート** - 処理前に入力をチェック
4. **Asyncを使用** - 並行実行のために常に `async def` を使用
5. **ドキュメントを書く** - docstringと型ヒントを追加
6. **独立してテスト** - 関数を単体テスト

## サンプル

動作するコードについては [Example 06: Custom Components](../../examples/06_component/) を参照してください。

## 次のステップ

- [フックメソッド](./hook_methods.md) について学ぶ
- [カスタムツール](./custom_tools.md) を参照
- [サンプル](./examples.md) を参照
