# Runtime Configuration

YAML v2の `runtime` セクションでは、実行エンジン、ファクトリー、イベントエクスポーターを設定できます。

## 基本構造

```yaml
runtime:
  engine: lc.lcel                    # 実行エンジン（必須）
  graph_name: my_graph               # グラフ名（オプション）
  defaults:                          # デフォルト設定（オプション）
    provider: openai
  factories:                         # ファクトリー定義（オプション）
    providers: {...}
    tools: {...}
    components: {...}
  exporters:                         # イベントエクスポーター（オプション）
    - type: jsonl
      path: run.jsonl
```

## engine

実行エンジンを指定します。現在サポートされているのは：

- `lc.lcel`: LangChain LCEL (LangChain Expression Language) ベースの実行

```yaml
runtime:
  engine: lc.lcel
```

## graph_name

グラフの名前を指定します。テレメトリーイベントで使用されます。

```yaml
runtime:
  engine: lc.lcel
  graph_name: my_agent_v1
```

## defaults

グラフ全体のデフォルト設定を定義します。

```yaml
runtime:
  engine: lc.lcel
  defaults:
    provider: openai          # デフォルトプロバイダー
    temperature: 0.7          # デフォルト温度
    max_tokens: 256           # デフォルトトークン数
```

`defaults.provider` を設定すると、コンポーネント定義で `provider` を省略できます。

## factories

### 概要

`factories` セクションでは、プロバイダー、ツール、コンポーネントのファクトリー関数を定義します。

```yaml
runtime:
  factories:
    providers:
      openai: my_package.factories.openai_provider
      anthropic: my_package.factories.anthropic_provider
    tools:
      http: my_package.tools.http_tool
      search: my_package.tools.search_tool
    components:
      llm: my_package.components.llm_component
      router: my_package.components.router_component
```

### providers

プロバイダータイプとファクトリー関数のマッピングを定義します。

**形式**: `<provider_type>: <dotted.path.to.factory_function>`

```yaml
factories:
  providers:
    openai: examples.01_basic_llm.factories.provider_factory
```

**ファクトリー関数のシグネチャ**:

```python
def provider_factory(provider: NormalizedProvider) -> Mapping[str, Any]:
    """
    Args:
        provider: 正規化されたプロバイダー定義
            - provider.id: プロバイダーID
            - provider.type: プロバイダータイプ
            - provider.config: 設定dict
    
    Returns:
        プロバイダーインスタンス（dict推奨）
    """
    from openai import OpenAI
    return {
        "client": OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
        "model": provider.config.get("model", "gpt-4"),
    }
```

### tools

ツールタイプとファクトリー関数のマッピングを定義します。

```yaml
factories:
  tools:
    http: my_package.tools.http_tool_factory
```

**ファクトリー関数のシグネチャ**:

```python
def tool_factory(tool: NormalizedTool) -> Any:
    """
    Args:
        tool: 正規化されたツール定義
    
    Returns:
        ツールインスタンス
    """
    return MyHttpTool(config=tool.config)
```

### components

コンポーネントタイプとファクトリー関数のマッピングを定義します。

```yaml
factories:
  components:
    llm: my_package.components.llm_factory
```

**ファクトリー関数のシグネチャ**:

```python
from typing import Mapping, Any, Callable

def component_factory(
    component: NormalizedComponent,
    provider_instance: Mapping[str, Any],
    tool_instance: Any,
) -> Callable:
    """
    Args:
        component: 正規化されたコンポーネント定義
        provider_instance: プロバイダーファクトリーが返したインスタンス
        tool_instance: ツールファクトリーが返したインスタンス（該当する場合）
    
    Returns:
        async callable: async def call(state, inputs, ctx) -> Mapping[str, Any]
    """
    client = provider_instance["client"]
    model = provider_instance["model"]
    temperature = component.config.get("temperature", 0.7)
    
    async def call(state: Mapping[str, Any], inputs: Mapping[str, Any], ctx: Mapping[str, Any]) -> Mapping[str, Any]:
        prompt = inputs.get("prompt", "")
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return {
            "choices": [{
                "text": response.choices[0].message.content
            }],
            "usage": response.usage.model_dump(),
        }
    
    return call
```

## exporters

イベントのエクスポート先を設定します。複数のエクスポーターを同時に使用できます。

```yaml
runtime:
  exporters:
    - type: jsonl
      path: logs/run.jsonl
    - type: console
      color: true
      verbose: false
    - type: langsmith
      project_name: my-agent
    - type: prometheus
      port: 9090
```

### JSONL Exporter

行ごとにJSON形式でイベントをファイルに出力します。

```yaml
exporters:
  - type: jsonl
    path: run.jsonl           # 相対パスまたは絶対パス
```

**出力例**:

```json
{"event": "graph.start", "graph_name": "my_graph", "run_id": "abc123", "ts": 1234567890.123}
{"event": "node.start", "node_id": "llm1", "ts": 1234567890.456}
{"event": "llm.call", "node_id": "llm1", "provider_id": "openai", "tokens_in": 10, "tokens_out": 50, "ts": 1234567891.789}
{"event": "node.finish", "node_id": "llm1", "status": "success", "duration_ms": 1500.0, "ts": 1234567892.345}
{"event": "graph.finish", "graph_name": "my_graph", "status": "success", "ts": 1234567892.678}
```

## 完全な例

```yaml
meta:
  version: 2
  name: production-agent
  description: Production-ready agent with full runtime config

runtime:
  engine: lc.lcel
  graph_name: prod_agent_v1.0
  
  # デフォルト設定
  defaults:
    provider: openai
    temperature: 0.2
    max_tokens: 1024
  
  # ファクトリー定義
  factories:
    providers:
      openai: my_company.agents.factories.openai_provider
      anthropic: my_company.agents.factories.anthropic_provider
    tools:
      search: my_company.agents.tools.search_tool
      calculator: my_company.agents.tools.calculator_tool
    components:
      llm: my_company.agents.components.llm_component
      router: my_company.agents.components.router_component
      tool_caller: my_company.agents.components.tool_component
  
  # イベントエクスポーター
  exporters:
    - type: jsonl
      path: /var/log/agent-ethan2/runs.jsonl
    - type: console
      color: false
      verbose: true
    - type: prometheus
      port: 9100

providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o
  
  - id: claude
    type: anthropic
    config:
      model: claude-3-5-sonnet-20241022

# ... components, graph, policies ...
```

## ファクトリーの動的読み込み

`AgentEthan` クラスは以下の順序でファクトリーを解決します：

1. **コンストラクタ引数** (`provider_factories`, `tool_factories`, `component_factories`)
2. **YAML `runtime.factories`** セクション
3. **デフォルトファクトリー**（存在する場合）

コンストラクタ引数が優先されるため、YAML設定を上書きできます：

```python
agent = AgentEthan(
    "config.yaml",
    provider_factories={
        "openai": "custom.factories.openai_debug"  # YAML設定をオーバーライド
    }
)
```

## ファクトリーのベストプラクティス

### 1. 環境変数でシークレットを管理

```python
import os

def provider_factory(provider):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    return {"client": OpenAI(api_key=api_key)}
```

### 2. 設定のバリデーション

```python
def component_factory(component, provider_instance, tool_instance):
    required_config = ["temperature", "max_tokens"]
    for key in required_config:
        if key not in component.config:
            raise ValueError(f"Missing required config: {key}")
    # ...
```

### 3. エラーハンドリング

```python
async def call(state, inputs, ctx):
    try:
        response = await client.chat.completions.create(...)
        return {"text": response.choices[0].message.content}
    except Exception as e:
        # ログ記録
        import sys
        print(f"Error in LLM call: {e}", file=sys.stderr)
        # エラーを再スロー（Schedulerがポリシーに従って処理）
        raise
```

### 4. 再利用可能なファクトリーモジュール

```
my_package/
  factories/
    __init__.py
    providers.py     # openai_provider, anthropic_provider
    components.py    # llm_component, router_component
    tools.py         # search_tool, calculator_tool
```

```yaml
runtime:
  factories:
    providers:
      openai: my_package.factories.providers.openai_provider
    components:
      llm: my_package.factories.components.llm_component
```

## 関連ドキュメント

- [Facade API](./facade-api.md)
- [YAML Reference](./yaml_reference.md)
- [Examples](../examples/)

