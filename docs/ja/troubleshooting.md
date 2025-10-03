# トラブルシューティング

AgentEthan2を使用する際によく発生する問題とその解決策をまとめました。

## 目次

- [1. インストールとセットアップ](#1-インストールとセットアップ)
- [2. APIキーと認証](#2-apiキーと認証)
- [3. YAML設定](#3-yaml設定)
- [4. ファクトリーとプロバイダ](#4-ファクトリーとプロバイダ)
- [5. ノードとグラフの実行](#5-ノードとグラフの実行)
- [6. Docker関連](#6-docker関連)
- [7. パフォーマンス](#7-パフォーマンス)
- [8. テスト](#8-テスト)
- [9. デバッグのヒント](#9-デバッグのヒント)
- [10. よくある質問](#10-よくある質問)
- [11. ヘルプを得る](#11-ヘルプを得る)

---

## 1. インストールとセットアップ

### Q: `ModuleNotFoundError: No module named 'agent_ethan2'` が発生します。

**原因**: パッケージがインストールされていないか、編集可能モードでないためPython環境から認識されていません。

**解決策**: プロジェクトのルートディレクトリで以下のコマンドを実行し、編集可能モードでインストールしてください。
```bash
cd agent-ethan2
pip install -e .
```

### Q: `ModuleNotFoundError: No module named 'openai'` など、特定のライブラリが見つかりません。

**原因**: 必要な依存関係がインストールされていません。

**解決策**: `pip install -e .` でプロジェクトの依存関係をすべてインストールするか、不足しているライブラリを個別にインストールしてください。
```bash
pip install -e .
# または
pip install openai langchain-core langchain-openai
```

---

## 2. APIキーと認証

### Q: APIキーが未設定で `openai.AuthenticationError` が発生します。

**原因**: OpenAIクライアントが有効なAPIキーを取得できていません。

**解決策**: 環境変数 `OPENAI_API_KEY` を設定してください。
```bash
export OPENAI_API_KEY=your-api-key-here
```
または、コード内で設定することも可能です（非推奨）。
```python
import os
os.environ["OPENAI_API_KEY"] = "your-key"
```

### Q: `openai.AuthenticationError: Invalid API key` が発生します。

**原因**: 設定されたAPIキーの形式が無効であるか、期限切れです。

**解決策**:
-   APIキーが正しい文字列であるか確認してください。
-   キーが失効していないか、プロバイダの管理画面で確認してください。
-   APIキーの前後や途中に余分なスペースや改行文字が含まれていないか確認してください。

---

## 3. YAML設定

### Q: `YamlValidationError: 'meta' is a required property` など、必須プロパティに関するエラーが発生します。

**原因**: YAML設定ファイルに必須のセクションやフィールドが欠落しています。

**解決策**: YAMLファイルに以下の必須セクションがすべて含まれていることを確認してください。
```yaml
meta:
  version: 2
runtime:
  engine: lc.lcel
  factories:
    # ...
providers:
  # ...
graph:
  # ...
```
詳細については、[YAML定義リファレンス](./yaml_reference.md)を参照してください。

### Q: `YamlValidationError: Additional properties are not allowed` が発生します。

**原因**: YAML設定ファイルに、スキーマで定義されていない無効なフィールド名が含まれています。

**解決策**: 有効なフィールド名については、[YAML定義リファレンス](./yaml_reference.md)を確認してください。タイプミスがないか注意深く確認してください。

### Q: `jsonschema.exceptions.ValidationError` が発生します。

**原因**: YAML設定ファイルがAgentEthan2のスキーマ定義と一致していません。フィールドの型が間違っている、必須フィールドが欠落している、値の範囲が不正などの可能性があります。

**解決策**:
-   `schemas/yaml_v2.json` に対してYAMLファイルを検証し、エラー箇所を特定してください。
-   フィールドの型（例: `string` と `integer`）が正しいか確認してください。
-   すべての必須フィールドが存在し、正しい値が設定されているか確認してください。
-   [YAML定義リファレンス](./yaml_reference.md)を参考に、設定を見直してください。

---

## 4. ファクトリーとプロバイダ

### Q: `GraphBuilderError [ERR_PROVIDER_DEFAULT_MISSING]` が発生します。

**原因**: ノードがプロバイダを必要としているにもかかわらず、解決できませんでした。例えば、`Node 'ask' requires a provider but none was resolved` のようなメッセージが表示されます。

**解決策**:
-   `providers` セクションに該当するプロバイダIDが存在し、正しく定義されているか確認してください。
-   `runtime.defaults.provider` を使用している場合、そのIDが正しいプロバイダを参照しているか確認してください。
-   `runtime.factories.providers` でプロバイダファクトリーが正しく登録されているか確認してください。

### Q: `ImportError: cannot import name 'provider_factory'` など、ファクトリー関数のインポートエラーが発生します。

**原因**: ファクトリー関数が存在しないか、YAMLで指定されたパスが間違っています。

**解決策**:
-   ファクトリー関数がPythonモジュール内に存在することを確認してください。
-   YAML設定ファイル内のインポートパス（例: `my_module.my_factory_function`）が正しいか確認してください。
-   該当するモジュールがPythonの検索パス（`PYTHONPATH`）に含まれていることを確認してください。

---

## 5. ノードとグラフの実行

### Q: `KeyError: 'client'` が発生します。

**原因**: プロバイダファクトリーが、ノードが期待するキー（例: `client`）を含む辞書を返していません。

**解決策**: プロバイダファクトリーが、必要なキー（例: `client`, `model`, `config` など）を含む辞書を返すことを確認してください。
```python
def provider_factory(provider):
    return {
        "client": client_instance,
        "model": "model-name",
        "config": dict(provider.config)
    }
```

### Q: `GraphBuilderError [ERR_NODE_TYPE]: Component 'xxx' referenced by node 'yyy' is undefined` が発生します。

**原因**: ノードが、YAMLの `components` セクションで定義されていないコンポーネントIDを参照しています。

**解決策**: 参照されているコンポーネントID (`xxx`) が、`components` セクションで正しく定義されているか確認してください。
```yaml
components:
  - id: xxx
    type: llm
    provider: openai
```

### Q: `GraphBuilderError [ERR_GRAPH_ENTRY_NOT_FOUND]` が発生します。

**原因**: `graph.entry` で指定されたノードIDが存在しません。エラーメッセージ例: `Graph entry 'xxx' does not exist`。

**解決策**: エントリーノード (`xxx`) が `graph.nodes` セクションで正しく定義されていることを確認してください。
```yaml
graph:
  entry: my_node
  nodes:
    - id: my_node
      # ...
```

### Q: `Circular dependency detected` が発生します。

**原因**: ワークフロー内のノードチェーンが自身にループバックしており、循環依存が発生しています。

**解決策**: ノード間の接続（`next` フィールドなど）を確認し、循環がないことを確認してください。ワークフローは有向非巡回グラフ（DAG）である必要があります。

### Q: `asyncio.TimeoutError` が発生します。

**原因**: 外部APIへのリクエストやノードの処理に時間がかかりすぎ、タイムアウトしました。

**解決策**: プロバイダ設定の `config` セクションでタイムアウト値を増やしてください。
```yaml
providers:
  - id: openai
    type: openai
    config:
      timeout: 60  # 秒単位
```

### Q: `RateLimitError: Rate limit exceeded` が発生します。

**原因**: 外部APIへのリクエストが多すぎ、レート制限を超過しました。

**解決策**: `policies` セクションでレート制限ポリシーを設定し、APIへのリクエストレートを制御してください。
```yaml
policies:
  ratelimit:
    default:
      rate: 5
      period: 1.0 # 1秒あたり5リクエストに制限
```
詳細については、[ポリシー](./policies.md)ドキュメントを参照してください。

---

## 6. Docker関連

### Q: `docker-compose: command not found` が発生します。

**解決策**: Docker Composeがシステムにインストールされているか確認してください。または、新しいバージョンのDockerでは `docker compose` (スペースあり) コマンドを使用します。

### Q: `Permission denied (docker)` が発生します。

**解決策**: 現在のユーザーが `docker` グループに属しているか確認してください。属していない場合、以下のコマンドでユーザーを `docker` グループに追加し、再ログインまたは `newgrp docker` を実行してください。
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Q: コンテナがすぐに終了してしまいます。

**原因**: 環境変数が欠落している、依存関係が正しくインストールされていない、またはアプリケーションの起動スクリプトに問題がある可能性があります。

**解決策**:
-   `docker-compose logs <サービス名>` (例: `docker-compose logs agent-ethan2-dev`) を実行し、コンテナのログを確認してエラーメッセージを特定してください。
-   必要な環境変数を含む `.env` ファイルが正しく配置され、読み込まれていることを確認してください。
-   Dockerfileが正常にビルドされ、すべての依存関係がインストールされていることを確認してください。

---

## 7. パフォーマンス

### Q: ワークフローの実行が遅いです。

**考えられる原因**:
-   LLMへの入力が大きすぎる（大きなコンテキストウィンドウ）。
-   会話履歴のターン数が多すぎる。
-   外部APIのレスポンスが遅い。
-   シーケンシャルな処理が多く、並列化されていない。

**解決策**:
-   会話履歴の `max_turns` を減らすか、関連性の低い履歴をフィルタリングしてください。
-   より高速なLLMモデル（例: `gpt-4o-mini`）の使用を検討してください。
-   キャッシングを実装し、頻繁にアクセスされるデータを再利用してください。
-   独立したタスクには [Parallelノード](./workflow.md#parallelノード) を使用し、並列実行を活用してください。

### Q: メモリ使用量が高いです。

**原因**: メモリ内に大きな会話履歴が保持されている可能性があります。

**解決策**: TTL（Time-To-Live）付きのRedisバックエンドなど、外部の履歴バックエンドを使用してください。
```yaml
histories:
  - id: chat
    backend:
      type: redis
      url: redis://localhost:6379
      max_turns: 50
      ttl: 3600 # 3600秒 (1時間) で履歴を自動削除
```

---

## 8. テスト

### Q: `pytest: No module named 'agent_ethan2'` が発生します。

**解決策**: プロジェクトを編集可能モードでインストールしていない可能性があります。以下のコマンドを実行してください。
```bash
pip install -e .
pytest
```

### Q: テストがAPIエラーで失敗します。

**原因**: テストが実際の外部APIを呼び出そうとしている可能性があります。

**解決策**:
-   テスト中に外部API呼び出しをモック（模擬）するように設定してください。
-   統合テストをスキップして、ユニットテストのみを実行してください。
```bash
pytest -m "not integration"
```

---

## 9. デバッグのヒント

### デバッグロギングを有効化する

Pythonの `logging` モジュールを使用して、詳細なログ出力を有効にできます。
```python
import logging
logging.basicConfig(level=logging.DEBUG) # DEBUGレベルでログを出力
```
または、YAML設定でログレベルを調整することも可能です。詳細については、[ロギング](./logging.md)ドキュメントを参照してください。

### テレメトリを確認する

AgentEthan2は、ワークフローの実行イベントをテレメトリとして出力できます。これを活用することで、実行フローやノードの状態変化を詳細に追跡できます。

JSONL形式でイベントをエクスポートするには、`runtime` 設定にエクスポーターを追加します。
```yaml
runtime:
  exporters:
    - type: jsonl
      path: debug.jsonl
```
その後、エクスポートされたファイルを確認します。
```bash
cat debug.jsonl | jq '.'
```

### コンソールエクスポーターを使用する

開発中にリアルタイムでイベントを確認するには、コンソールエクスポーターが便利です。
```yaml
runtime:
  exporters:
    - type: console
      color: true
      verbose: true
      filter_events:
        - graph.start
        - graph.finish
```

### YAML設定を検証する

YAML設定ファイルがスキーマに準拠しているか、手動で検証できます。
```bash
python -c "
import yaml
import json
from jsonschema import validate

with open('config.yaml') as f:
    config = yaml.safe_load(f)
with open('schemas/yaml_v2.json') as f:
    schema = json.load(f)

validate(config, schema)
print('YAML is valid')
"
```

---

## 10. よくある質問

### Q: 「サンプルでは動作したが自分のコードでは動作しない」

**確認事項**:
-   YAMLの構造がサンプルと完全に一致しているか。
-   ファクトリー関数がサンプルと同じパターンに従って実装されているか。
-   必要な環境変数がすべて設定されているか。
-   Pythonのインポートパスが正しいか。

### Q: 「Connection refused」または「Network error」

**確認事項**:
-   外部APIのエンドポイントURLが正しいか。
-   ファイアウォールやプロキシの設定が通信をブロックしていないか。
-   ローカルLLMを使用している場合、LLMサービスが実行中であるか。

### Q: 「Unexpected output format」

**確認事項**:
-   LLMやツールの出力が期待するJSONPath式と一致しているか。
-   ノードの戻り値の形式が正しいか。
-   YAMLの出力マッピングが正しく設定されているか。

---

## 11. ヘルプを得る

問題が解決しない場合は、以下のリソースを参照してください。

1.  動作するコードについては [サンプル集](./examples.md) を確認
2.  [YAML定義リファレンス](./yaml_reference.md) で完全な仕様を確認
3.  [セットアップガイド](./setup.md) を読み、インストールと設定が正しいか確認
4.  GitHub Issues を確認し、同様の問題が報告されていないか検索
5.  コミュニティチャンネル（もしあれば）で質問する

---