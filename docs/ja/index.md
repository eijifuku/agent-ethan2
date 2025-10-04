# AgentEthan2 ドキュメント

AgentEthan2へようこそ！このガイドは、YAML設定を使用してAIエージェントを構築するのに役立ちます。

## 目次

### 1. はじめに
- [セットアップガイド](./setup.md) - インストール、設定、最初のステップ
- [クイックスタート](../README.ja.md#クイックスタート) - 5分で始める

### 2. 基本的な使い方
- [ノード](./nodes.md) - エージェントの構成要素を理解する
- [YAML定義リファレンス](./yaml_reference.md) - すべてのYAMLキーの完全な仕様
- [プロバイダ](./providers.md) - LLMプロバイダの設定（OpenAI、ローカルモデルなど）
- [プロバイダー（応用）](./providers-advanced.md) - カスタムファクトリーの実装と上書き方法
- [カスタムロジックノード](./custom_logic_node.md) - カスタムノードの作成
- [カスタムツール](./custom_tools.md) - カスタムツールの作成と使用
- [ワークフロー](./workflow.md) - YAMLから実行完了までのMVPパイプライン

### 3. 高度な機能
- [会話履歴](./chat_history.md) - マルチターン会話管理
- [ロギング & テレメトリ](./logging.md) - エージェントの監視とデバッグ
- [フックメソッド](./hook_methods.md) - 詳細な制御のためのライフサイクルフック
- [非同期実行](./async_execution.md) - async/awaitパターンの理解
- [ポリシー](./policies.md) - リトライ、レート制限、マスキング、権限、コスト管理
- [セキュリティガイド](./security.md) - 安全なエージェント開発のベストプラクティス
- [JSONPath出力抽出](./jsonpath-outputs.md) - ノード出力からの値抽出
- [ランタイム設定](./runtime-config.md) - エンジン、ファクトリー、エクスポーターの設定

### 4. 統合
- [LangChainツール](./using_langchain_tools.md) - LangChainエコシステムの統合
- [MCP統合](./using_mcp.md) - Model Context Protocolサポート

### 5. サンプル集
- [サンプル集の概要](./examples.md)
    - [01_basic_llm - 基本的なLLMの利用](../examples/01_basic_llm/README.md)
    - [02_llm_with_tool - ツールを使ったLLM](../examples/02_llm_with_tool/README.md)
    - [03_router - ルーターノードの利用](../examples/03_router/README.md)
    - [04_map_parallel - Map/Parallelノードの利用](../examples/04_map_parallel/README.md)
    - [05_retry_ratelimit - リトライとレート制限](../examples/05_retry_ratelimit/README.md)
    - [06_component - カスタムノードの利用](../examples/06_component/README.md)
    - [07_full_agent - フルエージェントの例](../examples/07_full_agent/README.md)
    - [08_telemetry_exporters - テレメトリエクスポーター](../examples/08_telemetry_exporters/README.md)
    - [09_hooks - フックの利用](../examples/09_hooks/README.md)
    - [10_conversation_history - 会話履歴の利用](../examples/10_conversation_history/README.md)

### 6. リファレンス & トラブルシューティング
- [YAML定義リファレンス](./yaml_reference.md) - すべてのYAMLキーの完全な仕様
- [エラーコード一覧](./errors.md) - 完全なエラーコードリファレンス
- [イベント一覧](./events.md) - テレメトリー用イベントリファレンス
- [トラブルシューティング](./troubleshooting.md) - よくある問題と解決策

## AgentEthan2とは？

AgentEthan2は、ワークフロー定義と実装を分離する**宣言的エージェントフレームワーク**です。エージェントの動作をYAMLで定義し、ビジネスロジックをPythonで実装します。

### 主な利点

1. **宣言的** - ワークフローをコードではなくYAMLで定義
2. **テスト可能** - ワークフローのテストと変更が容易
3. **保守しやすい** - 関心事の明確な分離
4. **拡張可能** - カスタムロジック用のプラグインアーキテクチャ
5. **本番環境対応** - リトライ、レート制限、ロギングの組み込み

## アーキテクチャ概要

```
┌─────────────────────────────────────────┐
│           YAML設定                      │
│  (meta, runtime, providers, components) │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│          正規化 & IR                     │
│    (YAMLを内部モデルに変換)              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           レジストリ & リゾルバ          │
│   (ファクトリーをロード、インスタンス作成)│
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           グラフビルダー                 │
│    (実行可能なグラフを構築)              │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           スケジューラ & ランタイム       │
│  (ノード実行、状態管理、イベント)         │
└─────────────────────────────────────────┘
```

## 次のステップ

1. [セットアップガイド](./setup.md)に従ってAgentEthan2をインストール
2. [クイックスタート](../README.ja.md#クイックスタート)の例を試す
3. [サンプル集](./examples.md)ディレクトリを探索
4. 最初のエージェントを構築！
