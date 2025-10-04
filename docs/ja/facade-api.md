# Facade API (AgentEthan)

`AgentEthan` クラスは、AgentEthan2の高レベルFacade APIです。YAML設定から自動的に依存関係を解決し、シンプルなインターフェースでエージェントを実行できます。

## 基本的な使い方

### 最小構成

```python
from agent_ethan2.agent import AgentEthan

agent = AgentEthan("config.yaml")
result = agent.run_sync({"user_prompt": "Hello, world!"})
print(result.outputs)
```

### 非同期実行

```python
import asyncio
from agent_ethan2.agent import AgentEthan

async def main():
    agent = AgentEthan("config.yaml")
    result = await agent.run({"user_prompt": "Hello, world!"})
    print(result.outputs)

asyncio.run(main())
```

## コンストラクタ引数

```python
AgentEthan(
    config_path: Union[str, Path],
    *,
    provider_factories: Optional[Mapping[str, str]] = None,
    tool_factories: Optional[Mapping[str, str]] = None,
    component_factories: Optional[Mapping[str, str]] = None,
    log_path: Optional[Union[str, Path]] = None,
)
```

### パラメータ

- **`config_path`**: YAML v2設定ファイルのパス（必須）
- **`provider_factories`**: プロバイダーファクトリーのマッピング（オプション、YAML設定をオーバーライド）
- **`tool_factories`**: ツールファクトリーのマッピング（オプション）
- **`component_factories`**: コンポーネントファクトリーのマッピング（オプション）
- **`log_path`**: JSONLログファイルのパス（オプション、デフォルトは `config_dir/run.jsonl`）

### ファクトリーのオーバーライド

コード内でファクトリーを指定することもできます：

```python
agent = AgentEthan(
    "config.yaml",
    provider_factories={
        "openai": "my_custom.factories.openai_factory"
    },
    component_factories={
        "llm": "my_custom.factories.llm_component"
    }
)
```

## 実行メソッド

### `run_sync(inputs, *, timeout=None, run_id=None, event_emitter=None)`

同期的に実行（内部で `asyncio.run()` を使用）。`event_emitter` を指定すると、`AgentEthan` が内部で構築する `EventBus` の代わりに任意のエミッターを利用できます（`agent_ethan2/agent.py:164-201`）。

```python
result = agent.run_sync(
    {"user_prompt": "Summarize AI news"},
    timeout=30.0,
    event_emitter=my_event_bus,
)
```

### `await run(inputs, *, timeout=None, run_id=None, event_emitter=None)`

非同期で実行。`run_id` を指定するとテレメトリやログで追跡しやすくなります。

```python
result = await agent.run(
    {"user_prompt": "Summarize AI news"},
    timeout=30.0,
    run_id="custom-run-id-123",
    event_emitter=my_event_bus,
)
```

### 返り値: `GraphResult`

```python
@dataclass
class GraphResult:
    outputs: Mapping[str, Any]
    node_states: Mapping[str, NodeRuntimeState]
    run_id: str
```

`node_states` には各ノードの出力と戻り値が保持されます（`agent_ethan2/runtime/scheduler.py:34-120`）。

## YAML設定との連携

`AgentEthan` は `runtime.factories` セクションから自動的にファクトリーを読み込みます：

```yaml
runtime:
  engine: lc.lcel
  graph_name: my_graph
  defaults:
    provider: openai
  exporters:
    - type: jsonl
      path: run.jsonl
```

組み込みのデフォルトファクトリー（`openai` プロバイダーや `llm`/`tool` コンポーネントなど）が自動で適用されるため、典型的な構成では追加の `runtime.factories` 設定は不要です。必要に応じて `runtime.factories` にエントリを追加することで既定の挙動を上書きできます。

この設定により、以下が自動的に行われます：

1. **ファクトリーの読み込み**: コンストラクタ、YAML、組み込みデフォルトをマージ
2. **レジストリの構築**: `ProviderResolver`, `ToolResolver`, `ComponentResolver` を自動生成
3. **依存解決**: プロバイダー、ツール、ノードのインスタンス化
4. **グラフ構築**: IR（中間表現）からグラフ定義を生成
5. **イベントバスの設定**: `exporters` セクションに基づいてエクスポーターを設定

## 内部処理フロー

```
config.yaml
    ↓
[YamlLoaderV2] YAML検証・パース
    ↓
[normalize_document] IR正規化
    ↓
[Registry] ファクトリー解決・依存注入
    ↓
[GraphBuilder] 実行グラフ構築
    ↓
[Scheduler] 非同期実行
    ↓
GraphResult
```

## エラーハンドリング

```python
from agent_ethan2.agent import AgentEthan
from agent_ethan2.graph import GraphExecutionError

try:
    agent = AgentEthan("config.yaml")
    result = agent.run_sync({"user_prompt": "..."})
except FileNotFoundError as e:
    print(f"Config file not found: {e}")
except GraphExecutionError as e:
    print(f"Execution failed: {e}")
```

## 低レベルAPIとの比較

### Before（低レベルAPI、56行）

```python
from agent_ethan2.loader import YamlLoaderV2
from agent_ethan2.ir import normalize_document
from agent_ethan2.registry import Registry
from agent_ethan2.registry.resolver import (
    ComponentResolver, ProviderResolver, ToolResolver
)
from agent_ethan2.graph import GraphBuilder
from agent_ethan2.runtime.scheduler import Scheduler
from agent_ethan2.telemetry import EventBus
from agent_ethan2.telemetry.exporters.jsonl import JsonlExporter

# YAML読み込み
loader = YamlLoaderV2()
document = loader.load_file("config.yaml")
ir_result = normalize_document(document)

# レジストリ構築
registry = Registry(
    provider_resolver=ProviderResolver(
        factories={"openai": "path.to.provider_factory"},
        cache={},
    ),
    tool_resolver=ToolResolver(factories={}, cache={}),
    component_resolver=ComponentResolver(
        factories={"llm": "path.to.component_factory"},
        cache={},
    ),
)
resolved = registry.materialize(ir_result.ir)

# グラフ構築
definition = GraphBuilder().build(ir_result.ir, resolved)

# イベントバス
emitter = EventBus(exporters=[JsonlExporter(path="run.jsonl")])

# 実行
scheduler = Scheduler()
result = await scheduler.run(
    definition,
    inputs={"user_prompt": "..."},
    event_emitter=emitter,
)
```

### After（Facade API、3行）

```python
from agent_ethan2.agent import AgentEthan

agent = AgentEthan("config.yaml")
result = agent.run_sync({"user_prompt": "..."})
```

## ベストプラクティス

### 1. YAML設定でファクトリーを定義

```yaml
runtime:
  factories:
    providers:
      openai: my_package.factories.provider_factory
    components:
      llm: my_package.factories.component_factory
```

### 2. 環境変数でシークレットを管理

```python
# factories.py
import os

def provider_factory(provider):
    return {
        "client": OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
        "model": provider.config.get("model"),
    }
```

### 3. 再利用可能なファクトリーパッケージを作成

```
my_project/
  config.yaml
  factories/
    __init__.py
    openai.py      # provider_factory
    anthropic.py   # provider_factory
    llm.py         # component_factory
```

### 4. エージェントインスタンスの再利用

```python
# 初期化は1回だけ
agent = AgentEthan("config.yaml")

# 複数回実行
for prompt in prompts:
    result = agent.run_sync({"user_prompt": prompt})
    print(result.outputs)
```

## 制限事項

- **同期 `run_sync` の制約**: 既存のイベントループ内では使用できません（`asyncio.run()` を使用するため）
- **設定の動的変更**: 一度初期化すると、設定を変更するには新しいインスタンスが必要
- **ファクトリーキャッシュ**: デフォルトでファクトリーの結果はキャッシュされません

## 関連ドキュメント

- [YAML v2 Schema](../schemas/yaml_v2.json)
- [Runtime Configuration](./runtime-config.md)
- [Examples](../examples/)
