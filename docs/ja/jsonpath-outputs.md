# JSONPath Output Extraction

AgentEthan2では、ノードの出力からJSONPath式を使用して特定の値を抽出できます。

## 基本構文

```yaml
components:
  - id: my_component
    type: llm
    provider: openai
    outputs:
      text: $.choices[0].text      # JSONPath式
```

## サポートされる機能

### 1. オブジェクトキー

```yaml
outputs:
  text: $.response.content
  model: $.metadata.model
```

**入力データ**:
```json
{
  "response": {"content": "Hello"},
  "metadata": {"model": "gpt-4"}
}
```

**抽出結果**:
- `text` → `"Hello"`
- `model` → `"gpt-4"`

### 2. 配列インデックス

```yaml
outputs:
  first: $.choices[0].text
  second: $.choices[1].text
```

**入力データ**:
```json
{
  "choices": [
    {"text": "First choice"},
    {"text": "Second choice"}
  ]
}
```

**抽出結果**:
- `first` → `"First choice"`
- `second` → `"Second choice"`

### 3. ネストされたパス

```yaml
outputs:
  value: $.data.results[0].score.confidence
```

**入力データ**:
```json
{
  "data": {
    "results": [
      {"score": {"confidence": 0.95}}
    ]
  }
}
```

**抽出結果**:
- `value` → `0.95`

## 構文規則

### パス構成要素

1. **ルート**: 必ず `$.` で開始
2. **キー**: `.` の後にキー名を記述
3. **配列**: `[数値]` で要素にアクセス

### 例

| JSONPath | 説明 |
|----------|------|
| `$.text` | ルートの `text` キー |
| `$.choices[0]` | `choices` 配列の最初の要素 |
| `$.choices[0].text` | `choices[0]` の `text` キー |
| `$.metadata.model` | `metadata` の `model` キー |
| `$.data[1].items[0]` | ネストされた配列アクセス |

## 実装例

### OpenAI Chat Completions

```yaml
components:
  - id: llm_openai
    type: llm
    provider: openai
    outputs:
      text: $.choices[0].message.content
      finish_reason: $.choices[0].finish_reason
      prompt_tokens: $.usage.prompt_tokens
      completion_tokens: $.usage.completion_tokens
```

**OpenAI APIレスポンス**:
```json
{
  "choices": [{
    "message": {"content": "AI response here"},
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 256
  }
}
```

### カスタムノード

```python
# ファクトリー関数
async def my_component(state, inputs, ctx):
    return {
        "results": [
            {"name": "Result 1", "score": 0.95},
            {"name": "Result 2", "score": 0.87}
        ],
        "metadata": {
            "total": 2,
            "best_score": 0.95
        }
    }
```

```yaml
components:
  - id: my_comp
    type: custom_logic
    outputs:
      best_name: $.results[0].name
      best_score: $.results[0].score
      total_count: $.metadata.total
```

## エラーハンドリング

パスが存在しない場合、`null` が返されます。

```yaml
outputs:
  value: $.nonexistent.path    # null
```

**例**:

**入力データ**:
```json
{"data": "value"}
```

**JSONPath**: `$.missing[0].key`

**結果**: `null`

## 制限事項

現在の実装では以下の機能は**サポートされていません**：

- ❌ ワイルドカード (`$.choices[*].text`)
- ❌ スライス (`$.choices[0:2]`)
- ❌ フィルター (`$.choices[?(@.score > 0.5)]`)
- ❌ 再帰検索 (`$..text`)
- ❌ 配列長 (`$.choices.length`)

これらの機能は将来のバージョンで追加される可能性があります。

## 内部実装

JSONPath抽出は `agent_ethan2/runtime/scheduler.py` の `_resolve_result_expression` メソッドで実装されています。

```python
def _resolve_result_expression(self, expression: Any, result: Any) -> Any:
    if not isinstance(expression, str):
        return expression
    if expression.startswith("$."):
        # 正規表現でパスをパース
        import re
        path_pattern = r'\.?([^\.\[]+)|\[(\d+)\]'
        matches = re.findall(path_pattern, expression[2:])
        current = result
        for key, index in matches:
            if index:  # 配列インデックス
                idx = int(index)
                if isinstance(current, (list, tuple)) and 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif key:  # オブジェクトキー
                if isinstance(current, Mapping) and key in current:
                    current = current[key]
                else:
                    return None
        return current
    return expression
```

## テスト

JSONPath機能は `tests/test_runtime_scheduler.py::test_jsonpath_array_index_resolution` でテストされています。

```python
@pytest.mark.asyncio
async def test_jsonpath_array_index_resolution() -> None:
    """Test that component outputs with JSONPath array indices are correctly resolved."""
    # ... テストコード
    assert result.outputs["result1"] == "first"   # $.choices[0].text
    assert result.outputs["result2"] == "second"  # $.choices[1].text
    assert result.outputs["score"] == 0.9         # $.choices[0].score
```

## ベストプラクティス

### 1. 防御的なファクトリー実装

ノードは常に期待される構造を返すようにします：

```python
async def call(state, inputs, ctx):
    response = await api_call()
    # 常に choices 配列を返す
    if not response.choices:
        return {"choices": [{"text": ""}]}
    return {
        "choices": [{
            "text": response.choices[0].message.content or ""
        }]
    }
```

### 2. デフォルト値の処理

nullチェックをグラフレベルで行います：

```yaml
graph:
  nodes:
    - id: llm1
      type: llm
      component: my_llm
    
    - id: fallback
      type: llm
      component: fallback_llm
      condition: node.llm1.text == null  # null時の代替処理
```

### 3. 複雑なパスは避ける

深くネストされたパスは読みにくくなります。ファクトリーでフラット化を推奨：

```python
# 悪い例: 深いネスト
return {
    "data": {
        "response": {
            "content": {
                "text": "value"
            }
        }
    }
}

# 良い例: フラット構造
return {
    "text": "value",
    "metadata": {...}
}
```

## 関連ドキュメント

- [Custom Logic Nodes](./custom_logic_node.md)
- [Runtime Configuration](./runtime-config.md)
- [YAML Reference](./yaml_reference.md)

