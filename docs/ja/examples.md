# サンプル

付属のサンプルのウォークスルー。

## 概要

`examples/` ディレクトリには主要機能を示す10個の動作するサンプルが含まれています：

1. **01_basic_llm** - シンプルなLLM呼び出し
2. **02_llm_with_tool** - LLM + ツール統合
3. **03_router** - 条件付きルーティング
4. **04_map_parallel** - Map/並列実行
5. **05_retry_ratelimit** - リトライとレート制限
6. **06_component** - カスタムノード
7. **07_full_agent** - 完全なエージェント
8. **08_telemetry_exporters** - ロギング/テレメトリ
9. **09_hooks** - ライフサイクルフック
10. **10_conversation_history** - マルチターン会話

## Example 01: Basic LLM

**場所**: `examples/01_basic_llm/`

**デモ内容**:
- シンプルなLLM呼び出し
- プロバイダー設定
- ファクトリー関数
- YAML設定

**実行方法**:
```bash
cd examples/01_basic_llm
export OPENAI_API_KEY=your-key
python run.py
```

## Example 02: LLM with Tool

**場所**: `examples/02_llm_with_tool/`

**デモ内容**:
- ツール統合
- 計算機ツール
- LLM + ツールワークフロー
- 出力フォーマット

**実行方法**:
```bash
cd examples/02_llm_with_tool
export OPENAI_API_KEY=your-key
python run.py
```

## Example 03: Router

**場所**: `examples/03_router/`

**デモ内容**:
- 条件付きルーティング
- インテント分類
- ルーターノードタイプ
- マルチブランチワークフロー

**実行方法**:
```bash
cd examples/03_router
export OPENAI_API_KEY=your-key
python run.py
```

## Example 04: Map/Parallel

**場所**: `examples/04_map_parallel/`

**デモ内容**:
- コレクションのマップ
- 並列処理
- バッチ操作
- 失敗ハンドリング

**実行方法**:
```bash
cd examples/04_map_parallel
export OPENAI_API_KEY=your-key
python run.py
```

## Example 05: Retry & Rate Limit

**場所**: `examples/05_retry_ratelimit/`

**デモ内容**:
- リトライポリシー
- レート制限（トークンバケット、固定ウィンドウ）
- エラーハンドリング
- 回復力のある実行

**実行方法**:
```bash
cd examples/05_retry_ratelimit
export OPENAI_API_KEY=your-key
python run.py
```

## Example 06: Custom Components

**場所**: `examples/06_component/`

**デモ内容**:
- カスタムPython関数
- データ変換
- ビジネスロジック
- 動的ノードロード

**実行方法**:
```bash
cd examples/06_component
export OPENAI_API_KEY=your-key
python run.py
```

## Example 07: Full Agent

**場所**: `examples/07_full_agent/`

**デモ内容**:
- 完全なエージェントワークフロー
- ルーター + ツール + LLM
- インテント分類
- マルチステップ処理

**実行方法**:
```bash
cd examples/07_full_agent
export OPENAI_API_KEY=your-key
python run.py
```

## Example 08: Telemetry Exporters

**場所**: `examples/08_telemetry_exporters/`

**デモ内容**:
- JSONLエクスポーター
- コンソールエクスポーター
- LangSmith統合
- Prometheusメトリクス
- 複数エクスポーター

**実行方法**:
```bash
cd examples/08_telemetry_exporters
export OPENAI_API_KEY=your-key
python run_console.py
python run_multiple.py
python run_yaml_config.py
```

## Example 09: Lifecycle Hooks

**場所**: `examples/09_hooks/`

**デモ内容**:
- before_executeフック
- after_executeフック
- on_errorフック
- ロギングとキャッシングのユースケース

**実行方法**:
```bash
cd examples/09_hooks
export OPENAI_API_KEY=your-key
python run.py         # Normal execution
python run_error.py   # Error handling
```

## Example 10: Conversation History

**場所**: `examples/10_conversation_history/`

**デモ内容**:
- マルチターン会話
- メモリバックエンド
- Redisバックエンド
- 複数の履歴インスタンス
- セッション管理

**実行方法**:
```bash
cd examples/10_conversation_history
export OPENAI_API_KEY=your-key
python run.py
```

## すべてのサンプルを実行

```bash
export OPENAI_API_KEY=your-key

for dir in examples/*/; do
    if [ -f "$dir/run.py" ]; then
        echo "Running $dir"
        (cd "$dir" && python run.py)
    fi
done
```

## 次のステップ

- 一般的な問題については [トラブルシューティング](./troubleshooting.md) を参照
- 完全な仕様については [YAMLリファレンス](./yaml_reference.md) を参照
- [カスタムロジックノード](./custom_logic_node.md) について学ぶ
