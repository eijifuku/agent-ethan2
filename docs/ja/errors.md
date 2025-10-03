# エラーコード一覧

AgentEthan2 のバリデーションと実行で使用される主要なエラーコードをモジュール別に整理しています。コードの定義はレポジトリ内のコメントと例外メッセージで確認できます。

## YAML Loader (`agent_ethan2/loader/yaml_loader.py`)

| Code | 説明 |
| ---- | ---- |
| `ERR_YAML_PARSE` | YAML の構文解析に失敗 |
| `ERR_YAML_EMPTY` | ドキュメントが空 |
| `ERR_ROOT_NOT_MAPPING` | ルート要素がマッピングではない |
| `ERR_YAML_DUPLICATE_KEY` | 同一レベルでキーが重複 |
| `ERR_YAML_COMPLEX_KEY` | 複合キーが使用された |
| `ERR_YAML_SCALAR` | サポート外のスカラ型が出現 |
| `ERR_YAML_NODE_UNSUPPORTED` | 未対応の YAML ノード種別 |
| `ERR_META_VERSION_UNSUPPORTED` | `meta.version` が v2 以外 |
| `ERR_RUNTIME_ENGINE_UNSUPPORTED` | `runtime.engine` が未サポート |
| `ERR_PROVIDER_DUP` / `ERR_TOOL_DUP` / `ERR_COMPONENT_DUP` / `ERR_NODE_DUP` | ID が重複 |
| `ERR_OUTPUT_KEY_COLLISION` | `graph.outputs` のキーが重複 |
| `ERR_SCHEMA_VALIDATION` | JSON Schema 検証エラー |

## IR Normalizer (`agent_ethan2/ir/model.py`)

### 全般
| Code | 説明 |
| ---- | ---- |
| `ERR_IR_INPUT_TYPE` | 正規化対象がマッピングではない |
| `ERR_META_TYPE` | `meta` がマッピングでない |
| `ERR_RUNTIME_TYPE` | `runtime` がマッピングでない |
| `ERR_RUNTIME_ENGINE` | `runtime.engine` が文字列でない |
| `ERR_RUNTIME_DEFAULT_PROVIDER` | `defaults.provider` に未定義のプロバイダーを指定 |

### プロバイダー / ツール
| Code | 説明 |
| ---- | ---- |
| `ERR_PROVIDERS_TYPE` | `providers` が配列でない |
| `ERR_PROVIDER_ID` / `ERR_PROVIDER_TYPE` / `ERR_PROVIDER_TYPE_FIELD` | プロバイダー定義の必須フィールドが無効 |
| `ERR_TOOLS_TYPE` | `tools` が配列でない |
| `ERR_TOOL_ID` / `ERR_TOOL_TYPE` / `ERR_TOOL_TYPE_FIELD` | ツール定義の必須フィールドが無効 |
| `ERR_TOOL_PROVIDER_NOT_FOUND` | ツールが存在しないプロバイダーを参照 |

### コンポーネント
| Code | 説明 |
| ---- | ---- |
| `ERR_COMPONENTS_TYPE` | `components` が配列でない |
| `ERR_COMPONENT_ID` / `ERR_COMPONENT_TYPE` / `ERR_COMPONENT_TYPE_FIELD` | コンポーネント定義の必須フィールドが無効 |
| `ERR_COMPONENT_PROVIDER_NOT_FOUND` | コンポーネントが未定義のプロバイダーを参照 |
| `ERR_COMPONENT_TOOL_NOT_FOUND` | コンポーネントが未定義のツールを参照 |
| `ERR_NODE_COMPONENT_NOT_FOUND` | ノードが存在しないノードを参照 |

### グラフ / 出力
| Code | 説明 |
| ---- | ---- |
| `ERR_GRAPH_TYPE` | `graph` がマッピングでない |
| `ERR_GRAPH_ENTRY_NOT_FOUND` | `graph.entry` がノードと一致しない |
| `ERR_GRAPH_NODES` / `ERR_GRAPH_NODE_TYPE` | ノード定義が配列でない、または構造が無効 |
| `ERR_GRAPH_OUTPUTS_TYPE` | `graph.outputs` が配列でない |
| `ERR_GRAPH_OUTPUT_KEY` / `ERR_GRAPH_OUTPUT_NAME` / `ERR_GRAPH_OUTPUT_NODE` / `ERR_GRAPH_OUTPUT_TYPE` | 出力マッピングの必須フィールドが無効 |
| `ERR_EDGE_ENDPOINT_INVALID` | ノードの遷移先/出力が未定義 |

### 会話履歴 / ポリシー
| Code | 説明 |
| ---- | ---- |
| `ERR_HISTORY_TYPE` / `ERR_HISTORY_ID` / `ERR_HISTORY_BACKEND_TYPE` | `histories` セクションの構造が無効 |
| `ERR_HISTORY_DUPLICATE` | 履歴IDが重複 |
| `ERR_POLICIES_TYPE` | `policies` がマッピングでない |

## Graph Builder (`agent_ethan2/graph/builder.py`)

| Code | 説明 |
| ---- | ---- |
| `ERR_GRAPH_ENTRY_NOT_FOUND` | エントリノードが存在しない |
| `ERR_COMPONENT_IMPORT` | コンポーネントファクトリーがマテリアライズされていない |
| `ERR_NODE_TYPE` | 未サポートのノード種別（または必須設定が欠落） |
| `ERR_PROVIDER_DEFAULT_MISSING` | LLM/ツールノード用プロバイダーが解決できない |
| `ERR_TOOL_NOT_FOUND` | ツールノードが未マテリアライズ |
| `ERR_ROUTER_NO_MATCH` | ルーターノードのルートが定義されていない |
| `ERR_MAP_BODY_NOT_FOUND` | map ノードにノードが設定されていない |

## Runtime Scheduler (`agent_ethan2/runtime/scheduler.py`)

| Code | 説明 |
| ---- | ---- |
| `ERR_NODE_RUNTIME` | ノード実行中に例外発生 |
| `ERR_EDGE_ENDPOINT_INVALID` | 実行中に未定義ノードへ遷移しようとした |
| `ERR_ROUTER_NO_MATCH` | ルーターノードがルートを返さない |
| `ERR_MAP_BODY_NOT_FOUND` / `ERR_MAP_OVER_NOT_ARRAY` | map ノード設定が無効 |
| `ERR_PARALLEL_EMPTY` | parallel ノードのブランチが空 |
| `ERR_NODE_TYPE` | 実行時に未サポートノードに遭遇 |

## Registry (`agent_ethan2/registry/resolver.py`)

| Code | 説明 |
| ---- | ---- |
| `ERR_COMPONENT_IMPORT` | コンポーネントファクトリーのインポート失敗 |
| `ERR_COMPONENT_SIGNATURE` | コンポーネントの呼び出しシグネチャが `(state, inputs, ctx)` でない |
| `ERR_TOOL_IMPORT` | ツールファクトリーのインポート失敗 |
| `ERR_TOOL_PERM_TYPE` | ツールの `permissions` 属性がシーケンスではない |

## ポリシー / コスト管理

| Code | 説明 |
| ---- | ---- |
| `ERR_RETRY_PREDICATE` (`policy/retry.py`) | リトライ設定が無効 |
| `ERR_RL_POLICY_PARAM` (`policy/ratelimit.py`) | レートリミット設定が無効 |
| `ERR_TOOL_PERMISSION_DENIED` (`policy/permissions.py`) | ポリシーで許可されていない権限を要求 |
| `ERR_COST_LIMIT_EXCEEDED` (`policy/cost.py`) | 設定したコスト上限を超過 |

## その他

| Code | 説明 |
| ---- | ---- |
| `ERR_LLM_JSON_PARSE` (`validation/strict_json.py`) | LLM 出力の JSON パースに失敗 |

> **Note:** 実装にはここで列挙したコード以外にもテスト専用または内部用のコードが含まれる場合があります。最新情報は各モジュールの例外クラス定義を参照してください。
