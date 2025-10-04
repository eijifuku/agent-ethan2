# AgentEthan2

LLM、ツール、カスタムロジックを使用してAIワークフローを構築するための、柔軟なYAMLベースのエージェントフレームワークです。

[English README](./README.md)

## 概要

AgentEthan2は、YAML設定を使用して複雑なAIワークフローを定義できる宣言的なエージェントフレームワークです。ワークフロー定義と実装を明確に分離することで、AIエージェントの構築、テスト、保守を容易にします。

## 特徴

- **📝 YAMLファースト設計** - エージェント全体をYAMLで定義
- **🔄 複数のノードタイプ** - LLM、ツール、ルーター、Map/Parallel、カスタムコンポーネント
- **💬 会話履歴** - マルチターン会話をサポート、プラグイン可能なバックエンド（メモリ、Redis）
- **🔧 ライフサイクルフック** - `before_execute`、`after_execute`、`on_error`による詳細な制御
- **🔁 リトライ & レート制限** - 堅牢な実行のための組み込みポリシー
- **📊 テレメトリ & ロギング** - 複数のエクスポーター（JSONL、Console、LangSmith、Prometheus）
- **🧩 拡張可能** - カスタムプロバイダ、ツール、コンポーネントの追加が簡単
- **⚡ 非同期ファースト** - asyncioベースの効率的な実行
- **🔌 ツール統合** - LangChainツールとカスタムツールのサポート
- **🌐 OpenAI互換** - OpenAI APIおよび互換性のあるローカルLLM（Ollamaなど）に対応

## 必要条件

- Python 3.10以上
- pip または uv

## インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd agent-ethan2

# 依存関係をインストール
pip install -e .

# 開発用
pip install -e ".[dev]"
```

## クイックスタート

### 1. YAMLでエージェントを定義

`config.yaml` を作成:

```yaml
meta:
  version: 2
  name: simple-agent
  description: シンプルなLLMエージェント

runtime:
  engine: lc.lcel
  graph_name: simple_run
  factories:
    providers:
      openai: my_agent.factories.provider_factory
    components:
      llm: my_agent.factories.llm_factory
  exporters:
    - type: jsonl
      path: run.jsonl

providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini

components:
  - id: assistant
    type: llm
    provider: openai
    inputs:
      prompt: graph.inputs.user_message
    outputs:
      response: $.choices[0].text

graph:
  entry: ask
  nodes:
    - id: ask
      type: llm
      component: assistant
  outputs:
    - key: final_response
      node: ask
      output: response
```

### 2. エージェントを実行

`run.py` を作成:

```python
from agent_ethan2.agent import AgentEthan

# エージェントを初期化
agent = AgentEthan("config.yaml")

# 実行
result = agent.run_sync({
    "user_message": "こんにちは！何を手伝えますか？"
})

print(result.outputs["final_response"])
```

```bash
export OPENAI_API_KEY=your-api-key
python run.py
```

## 超クイックスタート

[AIコードエディタにAgentEthan2の仕様を理解させるMCP](https://github.com/eijifuku/agent-ethan-guide-mcp)を公開しています。  
このMCPを設定して作りたいエージェントの仕様をAIに伝える。  

## ドキュメント

- **[English Documentation](./docs/en/index.md)** - Complete guide in English
- **[日本語ドキュメント](./docs/ja/index.md)** - 日本語の完全ガイド

### コア概念

- [セットアップガイド](./docs/ja/setup.md) - インストールと設定
- [ノード](./docs/ja/nodes.md) - ノードタイプの理解
- [YAMLリファレンス](./docs/ja/yaml_reference.md) - 完全なYAML仕様
- [プロバイダ](./docs/ja/providers.md) - LLMプロバイダの設定
- [会話履歴](./docs/ja/chat_history.md) - マルチターン会話
- [ロギング](./docs/ja/logging.md) - テレメトリと監視

### 高度なトピック

- [カスタムロジックノード](./docs/ja/custom_logic_node.md) - カスタムコンポーネントの構築
- [カスタムツール](./docs/ja/custom_tools.md) - ツールの作成
- [LangChainツール](./docs/ja/using_langchain_tools.md) - LangChainツールの使用
- [MCP統合](./docs/ja/using_mcp.md) - Model Context Protocol
- [非同期実行](./docs/ja/async_execution.md) - Async/awaitパターン
- [フックメソッド](./docs/ja/hook_methods.md) - ライフサイクルフック
- [サンプル集](./docs/ja/examples.md) - 実装例
- [トラブルシューティング](./docs/ja/troubleshooting.md) - よくある問題

## カスタムファクトリー

高度な用途でカスタムプロバイダー、コンポーネント、ツールが必要な場合は、以下を参照してください：

- [高度なプロバイダー](./docs/ja/providers-advanced.md) - カスタムプロバイダーファクトリー
- [カスタムツール](./docs/ja/custom_tools.md) - カスタムツール実装
- [カスタムロジックノード](./docs/ja/custom_logic_node.md) - カスタムコンポーネントロジック
- [ランタイム設定](./docs/ja/runtime-config.md) - ファクトリー登録

## サンプル

[examples](./examples/)ディレクトリには動作するサンプルが含まれています：

- `01_basic_llm` - シンプルなLLM呼び出し
- `02_llm_with_tool` - ツール統合を含むLLM
- `03_router` - 条件分岐ルーティング
- `04_map_parallel` - 並列実行
- `05_retry_ratelimit` - リトライとレート制限
- `06_component` - カスタムコンポーネント
- `07_full_agent` - 完全なエージェント例
- `08_telemetry_exporters` - ロギング/テレメトリ
- `09_hooks` - ライフサイクルフック
- `10_conversation_history` - マルチターン会話

## ライセンス

MIT License

Copyright (c) 2025 AgentEthan2

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.




