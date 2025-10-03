# ノード

エージェントワークフローの構成要素を理解する。

## ノードとは？

ノードはエージェントグラフの実行単位です。各ノードは：
- 一意のIDを持つ
- ノードを参照する
- 入力を受け取る
- 出力を生成する
- 他のノードに接続できる

## ノードタイプ

AgentEthan2は複数のノードタイプをサポートしています：

| タイプ | 説明 | ユースケース |
|------|-------------|----------|
| `llm` | LLM呼び出し | チャット、生成、補完 |
| `tool` | ツール実行 | 検索、計算、API呼び出し |
| `router` | 条件付きルーティング | インテント分類、分岐 |
| `map` | コレクションのマップ | バッチ処理 |
| `parallel` | 並列実行 | 並行操作 |
| `component` | 汎用Pythonノード | 任意のカスタムロジック |

---

## LLMノード

LLMノードを実行します。

### 設定

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

### フィールド

- `component`: LLMノードへの参照
- `inputs`: 入力マッピング
- `outputs`: 出力マッピング（JSONPath）
- `config`: ノードレベルの設定オーバーライド

### 例

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

## ツールノード

ツールノードを実行します。

### 設定

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

### 例

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

## ルーターノード

ノード出力に基づく条件付きルーティング。

### 設定

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

### nextフィールド

`next`フィールドはオブジェクトで：
- **キー**はルート値（ノード出力から）
- **値**はターゲットノードID

### 例

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

**ノード実装**:

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

## Mapノード

コレクションの各アイテムに対してノードを実行します。

### 設定

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

### 設定フィールド

| フィールド | 型 | 説明 |
|-------|------|-------------|
| `collection` | expression | マップするコレクション |
| `failure_mode` | string | `continue`（エラーをスキップ）または `stop`（即座に失敗） |
| `ordered` | boolean | 順序を保持（`true`）または並べ替えを許可（`false`） |
| `result_key` | string | 出力結果のキー |

### 例

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

**入力**:
```python
agent.run_sync({
    "items": ["apple", "banana", "cherry"]
})
```

**出力**:
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

## Parallelノード

複数のノードを並行して実行します。

### 設定

```yaml
graph:
  nodes:
    - id: parallel_step
      type: parallel
      component: parallel_handler
      next: [step2, step3, step4]  # All execute in parallel
```

### nextフィールド

`next`フィールドは並列実行するノードIDの配列です。

### 例

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

3つのノード（`search`, `calculate`, `translate`）がすべて並行して実行されます。

---

## Componentノード

任意のPythonロジックをノード経由で実行します。

### 設定

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

### 例

```yaml
components:
  - id: my_custom_logic
    type: custom_logic               # runtime.factories.components に登録したキー
    provider: openai                 # 任意
    tool: calc_helper                # 任意（tools で定義）
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

**ノード実装**:

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

## ノードの接続

### 直線的なフロー

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

### 分岐（ルーター）

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

### 並列実行

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

## 入力/出力マッピング

### 入力式

ノードは以下を参照できます：

- **グラフ入力**: `graph.inputs.key`
- **ノード出力**: `node.step1.output_key`
- **定数**: `const:文字列`
- **リテラル**: `"literal"`, `42`, `true`

例:
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

### 出力式（JSONPath）

ノード結果からデータを抽出：

```yaml
outputs:
  text: $.choices[0].text
  usage: $.usage
  first_result: $.results[0]
  all_data: $
```

---

## ノード設定

### ノードレベル設定

`components` で定義：

```yaml
components:
  - id: assistant
    type: llm
    provider: openai
    config:
      temperature: 0.7
      max_output_tokens: 256
```

### ノードレベル設定

ノード設定をオーバーライド：

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

## ベストプラクティス

1. **説明的なIDを使用** - `node1` ではなく `classify_intent`
2. **ノードを集中させる** - ノードごとに1つの責務
3. **並列を活用** - 独立したタスクには並列実行を使用
4. **エラーを処理** - リトライポリシーとエラーハンドリングを使用
5. **複雑なロジックを文書化** - ノードに説明を追加

---

## 次のステップ

- [カスタムロジックノード](./custom_logic_node.md) について学ぶ
- 動作するコードについては [サンプル](./examples.md) を参照
- 完全な仕様については [YAMLリファレンス](./yaml_reference.md) を参照
