# ロギングとテレメトリ

テレメトリエクスポーターによるエージェントの監視とデバッグ。

## 概要

AgentEthan2は複数のテレメトリエクスポーターを提供してロギングと監視を行います：

- **JSONL** - JSON Lines形式のファイル出力
- **Console** - カラー付きターミナル出力
- **LangSmith** - LangSmith統合
- **Prometheus** - メトリクスエクスポート

## 設定

### YAML定義

```yaml
runtime:
  exporters:
    - type: jsonl
      path: run.jsonl
    - type: console
      verbose: false
      color: true
```

## JSONLエクスポーター

イベントをJSON Linesファイルに書き込みます。

```yaml
runtime:
  exporters:
    - type: jsonl
      path: logs/agent.jsonl
```

**出力**:
```json
{"event":"graph.start","graph_name":"my_agent","run_id":"abc123","timestamp":"2024-01-01T00:00:00Z"}
{"event":"node.start","node_id":"step1","timestamp":"2024-01-01T00:00:01Z"}
{"event":"node.finish","node_id":"step1","duration":1.5,"timestamp":"2024-01-01T00:00:02Z"}
```

## コンソールエクスポーター

イベントをコンソールに出力します。

```yaml
runtime:
  exporters:
    - type: console
      color: true
      verbose: true      # true で詳細表示、false でコンパクト表示
      filter_events:     # 例: ["graph.start", "graph.finish"]
        - graph.start
        - graph.finish
```

## LangSmithエクスポーター

トレースをLangSmithに送信します。

```yaml
runtime:
  exporters:
    - type: langsmith
      api_key: ${LANGSMITH_API_KEY}
      project_name: my-agent-project
```

## Prometheusエクスポーター

Prometheus用のメトリクスを公開します。

```yaml
runtime:
  exporters:
    - type: prometheus
      port: 9090
```

## 複数エクスポーター

複数のエクスポーターを組み合わせます：

```yaml
runtime:
  exporters:
    - type: jsonl
      path: logs/agent.jsonl
    - type: console
      color: true
      verbose: false
    - type: langsmith
      api_key: ${LANGSMITH_API_KEY}
      project_name: production
    - type: prometheus
      port: 9090
```

## サンプル

動作するコードについては [Example 08: Telemetry Exporters](../../examples/08_telemetry_exporters/) を参照してください。

## 次のステップ

- カスタムロギングについては [フックメソッド](./hook_methods.md) を参照
- [サンプル](./examples.md) について学ぶ
