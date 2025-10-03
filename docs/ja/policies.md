# ポリシー

AgentEthan2は、エージェントの動作を制御するための様々なポリシーをサポートしています。これらのポリシーは、信頼性、パフォーマンス、セキュリティ、コスト管理を向上させるのに役立ちます。

## ポリシーの適用

ポリシーは、YAML設定のトップレベルの `policies` セクションで定義されます。

```yaml
policies:
  retry:
    default:
      max_attempts: 3
    overrides:
      my_llm_node:
        max_attempts: 5
  ratelimit:
    default:
      rate: 10
      period: 1.0
  cost:
    default:
      max_cost: 0.10 # 最大コスト $0.10
  masking:
    default:
      patterns:
        - "api_key: (sk-[a-zA-Z0-9]{32})"
```

## 利用可能なポリシー

### リトライポリシー

ノードの実行失敗時に再試行する動作を制御します。一時的なエラー（ネットワークの問題、レート制限など）からの回復に役立ちます。

#### 設定

-   `default`: すべてのノードに適用されるデフォルトのリトライ設定。
    -   `max_attempts` (int, 必須): 最大再試行回数。
    -   `delay` (float, オプション): 初回再試行までの遅延時間（秒）。デフォルトは `0.0`。
    -   `backoff` (float, オプション): 再試行間の遅延に適用される指数バックオフ係数。デフォルトは `1.0`（遅延は一定）。
-   `overrides`: 特定のノードに適用されるリトライ設定のオーバーライド。ノードIDをキーとします。

詳細については、[YAML定義リファレンス](./yaml_reference.md#retry-ポリシー)を参照してください。

### レート制限ポリシー

ノードの実行レートを制限します。これにより、外部APIのレート制限を超過するのを防ぎ、安定した動作を保証します。

#### 設定

-   `default`: すべてのノードに適用されるデフォルトのレート制限設定。
    -   `rate` (int, 必須): 許可されるリクエスト数。
    -   `period` (float, 必須): レート制限の期間（秒）。

詳細については、[YAML定義リファレンス](./yaml_reference.md#ratelimit-ポリシー)を参照してください。

### コストポリシー

エージェントの実行コストを監視および制限します。特にLLMの利用において、予期せぬ高額な請求を防ぐために重要です。

#### 設定

-   `default`: すべてのノードに適用されるデフォルトのコスト制限設定。
    -   `max_cost` (float, 必須): ワークフロー全体の最大許容コスト。この値を超えると、ワークフローは停止します。
-   `overrides`: 特定のノードに適用されるコスト制限のオーバーライド。ノードIDをキーとします。

**例**:
```yaml
policies:
  cost:
    default:
      max_cost: 0.05 # ワークフロー全体の最大コストを$0.05に設定
    overrides:
      expensive_llm_call:
        max_cost: 0.01 # 特定のLLM呼び出しの最大コストを$0.01に設定
```

### マスキングポリシー

ログやテレメトリデータから機密情報を自動的にマスキング（匿名化）します。これにより、セキュリティとプライバシーを向上させます。

#### 設定

-   `default`: すべてのノードに適用されるデフォルトのマスキング設定。
    -   `patterns` (リスト, 必須): マスキングする正規表現パターンのリスト。マッチした文字列は `[MASKED]` に置き換えられます。
-   `overrides`: 特定のノードに適用されるマスキング設定のオーバーライド。ノードIDをキーとします。

**例**:
```yaml
policies:
  masking:
    default:
      patterns:
        - "Bearer [a-zA-Z0-9-_.]+" # JWTトークンをマスキング
        - "password: \"([^\"]+)\"" # パスワードフィールドの値をマスキング
```
詳細については、[セキュリティガイド](./security.md#マスキングポリシー)も参照してください。

### 権限ポリシー

ノードがアクセスできるリソース（ツール、プロバイダなど）を制限します。これにより、エージェントの動作をより細かく制御し、セキュリティリスクを軽減します。

#### 設定

-   `default`: すべてのノードに適用されるデフォルトの権限設定。
    -   `allow`: ツール固有の権限付与（ツール/ノードIDでキー付け）
    -   `deny`: ツール固有の権限拒否
-   `overrides`: 特定のノードに適用される権限設定のオーバーライド。ノードIDをキーとします。

**例**:
```yaml
policies:
  permissions:
    default:
      allow:
        - tool_id: web_search
          actions: ["search"]
      deny:
        - tool_id: file_system
          actions: ["delete"]
    overrides:
      sensitive_node:
        allow:
          - tool_id: internal_db
            actions: ["read_only"]
```
詳細については、[セキュリティガイド](./security.md#権限ポリシー)も参照してください。

---