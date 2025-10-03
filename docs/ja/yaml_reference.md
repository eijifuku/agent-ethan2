# YAML定義リファレンス

AgentEthan2はYAMLを使用してエージェントワークフローを定義します。YAMLファイルは、メタデータ、プロバイダ、コンポーネント、実行グラフを定義する複数のセクションで構成されます。

## トップレベルのセクション

- `meta`: メタデータ（バージョン、名前、説明など）
- `providers`: プロバイダ定義
- `components`: コンポーネント定義
- `graph`: 実行グラフ定義
- `policies`: ポリシー定義

---

## `meta` セクション

エージェントのメタデータを定義します。

```yaml
meta:
  version: 2.0
  name: MyAgent
  description: これは私の最初のAgentEthan2エージェントです。
```

### フィールド

- `version` (必須): YAMLスキーマのバージョン。現在 `2.0` をサポートしています。
- `name` (オプション): エージェントの名前。
- `description` (オプション): エージェントの説明。

---

## `providers` セクション

LLMやその他のサービスプロバイダを設定します。

```yaml
providers:
  - id: openai_gpt3
    type: openai
    config:
      model: gpt-3.5-turbo
      api_key: ${OPENAI_API_KEY}
  - id: local_llm
    type: local_llm
    config:
      model_path: /path/to/your/model
```

### フィールド

- `id` (必須): プロバイダの一意な識別子。
- `type` (必須): プロバイダのタイプ（例: `openai`, `local_llm`）。
- `config` (オプション): プロバイダ固有の設定。

詳細については、[プロバイダ](./providers.md)ドキュメントを参照してください。

---

## `components` セクション

ワークフローで利用可能なカスタムロジックや再利用可能なモジュールを定義します。

```yaml
components:
  - id: assistant
    type: llm
    provider: openai_gpt3
    outputs:
      response: $.choices[0].text
  - id: my_custom_logic
    type: custom_logic
    config:
      function_path: my_module.my_function
```

### フィールド

- `id` (必須): コンポーネントの一意な識別子。
- `type` (必須): コンポーネントのタイプ（例: `llm`, `tool`, `router`, `map`, `parallel`, `custom_logic`）。
- `provider` (オプション): このコンポーネントが使用するプロバイダのID。
- `tool` (オプション): `type: tool` の場合に、使用するツールのID。
- `inputs` (オプション): コンポーネントへの入力マッピング。
- `outputs` (オプション): コンポーネントからの出力マッピング（JSONPath）。
- `config` (オプション): コンポーネント固有の設定。
- `defaults` に定義した値はコンポーネント設定の既定値として適用され、`provider` を指定するとプロバイダー参照を省略できます（`agent_ethan2/ir/model.py:226-239`）。
- `factories` に登録したキーがコンポーネント/ツールの `type` と一致する必要があります。

---

## `graph` セクション

エージェントの実行フローを定義します。ノードの集合とそれらの接続を記述します。

```yaml
graph:
  id: main_workflow
  description: メインの会話フロー
  entry: start_node
  nodes:
    - id: start_node
      type: llm
      component: assistant
      next: process_output
    - id: process_output
      type: custom_logic
      component: my_custom_logic
```

### フィールド

- `id` (オプション): グラフの一意な識別子。
- `description` (オプション): グラフの説明。
- `entry` (オプション): グラフの開始ノードのID。指定しない場合、最初のノードが開始ノードとなります。
- `nodes` (必須): グラフ内のノードのリスト。

---

## `nodes` セクション (グラフ内)

個々のノードの定義。

```yaml
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
    next: next_node_id
```

### フィールド

- `id` (必須): ノードの一意な識別子。
- `type` (必須): ノードのタイプ（例: `llm`, `tool`, `router`, `map`, `parallel`, `component`）。
- `component` (必須): このノードが使用するコンポーネントのID。
- `inputs` (オプション): ノードへの入力マッピング。
- `outputs` (オプション): ノードからの出力マッピング（JSONPath）。
- `config` (オプション): ノード固有の設定。
- `next` (オプション): 次に実行するノードのID、またはルーターノードの場合は条件付きルーティング。

### `llm` ノードの `provider`

`llm` ノードは、`component` で指定されたコンポーネントが使用するプロバイダーの設定を継承します。
例えば、`openai` プロバイダーを使用する場合、`config` セクションで `model` や `temperature` などのプロバイダー固有のパラメータを設定できます。

利用可能なプロバイダーとその設定については、[プロバイダ](./providers.md)ドキュメントを参照してください。

---

## `policies` セクション

エージェントの実行ポリシーを定義します。

```yaml
policies:
  retry:
    default:
      max_attempts: 3
      delay: 1.0
      backoff: 2.0
    overrides:
      my_llm_node:
        max_attempts: 5
  ratelimit:
    default:
      rate: 10
      period: 1.0
```

### `retry` ポリシー

ノードの実行失敗時に再試行する動作を制御します。

#### フィールド

- `default` (オプション): すべてのノードに適用されるデフォルトのリトライ設定。
  - `max_attempts` (int, 必須): 最大再試行回数。
  - `delay` (float, オプション): 初回再試行までの遅延時間（秒）。デフォルトは `0.0`。
  - `backoff` (float, オプション): 再試行間の遅延に適用される指数バックオフ係数。デフォルトは `1.0`（遅延は一定）。
- `overrides` (オプション): 特定のノードに適用されるリトライ設定のオーバーライド。ノードIDをキーとします。

### `ratelimit` ポリシー

ノードの実行レートを制限します。

#### フィールド

- `default` (オプション): すべてのノードに適用されるデフォルトのレート制限設定。
  - `rate` (int, 必須): 許可されるリクエスト数。
  - `period` (float, 必須): レート制限の期間（秒）。

詳細については、[ポリシー](./policies.md)ドキュメントを参照してください。

---