# セキュリティガイド

AgentEthan2アプリケーションを保護するためのベストプラクティス。

## 概要

このガイドでは以下を説明します：
- APIキーとシークレット管理
- 安全なカスタムノード開発
- 権限管理
- データマスキング
- 入力検証
- 安全なデプロイ

---

## シークレット管理

### シークレットをハードコードしない

**❌ 悪い例**:
```yaml
providers:
  - id: openai
    type: openai
    config:
      api_key: "sk-abc123..."  # 絶対にこうしないこと
```

**✅ 良い例**:
```yaml
providers:
  - id: openai
    type: openai
    # ファクトリーで環境変数から読み込む
```

### 環境変数を使用

```python
# factories.py
import os

def openai_provider_factory(provider):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return {
        "client": OpenAI(api_key=api_key),
        "model": provider.config.get("model", "gpt-4"),
    }
```

### 環境ファイル

`.env`ファイルを使用（gitにコミットしないこと）：

```bash
# .env
OPENAI_API_KEY=sk-abc123...
ANTHROPIC_API_KEY=sk-ant-abc123...
DATABASE_URL=postgresql://...
```

**`.gitignore`**:
```
.env
.env.*
*.key
secrets/
```

### シークレット管理サービス

本番環境では専用サービスを使用：

-   **AWS Secrets Manager**
-   **HashiCorp Vault**
-   **Azure Key Vault**
-   **Google Secret Manager**

これらのサービスは、シークレットの安全な保存、アクセス制御、ローテーション機能を提供します。AgentEthan2のプロバイダファクトリー内で、これらのサービスからシークレットを動的に取得するように実装できます。

**例: AWS Secrets Managerからシークレットを取得**
```python
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

def openai_provider_factory(provider):
    api_key = get_secret("openai-api-key")
    return {"client": OpenAI(api_key=api_key)}
```

---

## 安全なカスタムノード

### 入力検証

カスタムノードでは常に入力を検証：

```python
async def search_component(state, inputs, ctx):
    # 入力を検証
    query = inputs.get("query")
    if not query or not isinstance(query, str):
        raise ValueError("Invalid query: must be non-empty string")
    
    if len(query) > 1000:
        raise ValueError("Query too long: max 1000 characters")
    
    # クエリをサニタイズ
    query = query.strip()
    
    # 検索を実行
    results = await search_api.search(query)
    return {"results": results}
```

### コード実行を避ける

**❌ 危険**:
```python
# 絶対にこうしないこと
async def eval_component(state, inputs, ctx):
    code = inputs.get("code")
    result = eval(code)  # 危険！
    return {"result": result}
```

**✅ 安全**:
```python
# サンドボックス化された実行または事前定義された操作を使用
async def calc_component(state, inputs, ctx):
    operation = inputs.get("operation")
    a = inputs.get("a")
    b = inputs.get("b")
    
    allowed_ops = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
    }
    
    if operation not in allowed_ops:
        raise ValueError(f"Operation not allowed: {operation}")
    
    return {"result": allowed_ops[operation](a, b)}
```

### ファイルシステムアクセス

権限と検証を使用：

```python
async def read_file_component(state, inputs, ctx):
    filepath = inputs.get("filepath")
    
    # パスを検証
    import os
    from pathlib import Path
    
    # ディレクトリトラバーサルを防止
    filepath = Path(filepath).resolve()
    allowed_dir = Path("/app/data").resolve()
    
    if not filepath.is_relative_to(allowed_dir):
        raise ValueError(f"Access denied: {filepath}")
    
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    # ファイルを読み込み
    with open(filepath, 'r') as f:
        content = f.read()
    
    return {"content": content}

# 権限を宣言
read_file_component.permissions = ["fs:read"]
```

### SQLインジェクション防止

**❌ 脆弱**:
```python
async def query_db(state, inputs, ctx):
    user_id = inputs.get("user_id")
    query = f"SELECT * FROM users WHERE id = {user_id}"  # 脆弱！
    result = await db.execute(query)
    return {"result": result}
```

**✅ 安全**:
```python
async def query_db(state, inputs, ctx):
    user_id = inputs.get("user_id")
    
    # パラメータ化されたクエリを使用
    query = "SELECT * FROM users WHERE id = ?"
    result = await db.execute(query, (user_id,))
    
    return {"result": result}
```

### HTTPリクエストの安全性

```python
async def api_call_component(state, inputs, ctx):
    url = inputs.get("url")
    
    # 許可されたドメインをホワイトリスト化
    from urllib.parse import urlparse
    
    allowed_domains = ["api.example.com", "data.example.com"]
    parsed = urlparse(url)
    
    if parsed.hostname not in allowed_domains:
        raise ValueError(f"Domain not allowed: {parsed.hostname}")
    
    # タイムアウトを設定
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return {"data": response.json()}

api_call_component.permissions = ["http:get"]
```

---

## 権限管理

### 最小権限の原則

必要な権限のみを付与：

```yaml
policies:
  permissions:
    default_allow: []  # デフォルトですべて拒否
    allow:
      # 特定のツールに特定の権限を付与
      file_reader:
        - fs:read
      web_scraper:
        - http:get
      admin_tool:
        - fs:read
        - fs:write
        - exec:shell  # これには十分注意！
```

### 標準権限

明確な権限名前空間を定義：

```
fs:read          - ファイルシステム読み取り
fs:write         - ファイルシステム書き込み
http:get         - HTTP GETリクエスト
http:post        - HTTP POSTリクエスト
db:read          - データベース読み取り
db:write         - データベース書き込み
exec:shell       - シェルコマンド実行
external:api     - 外部API呼び出し
```

### ノード権限宣言

```python
def tool_factory(tool, provider):
    instance = MyTool(config=tool.config)
    
    # 必要な権限を宣言
    instance.permissions = ["http:get", "fs:read"]
    
    return instance
```

### ランタイム権限チェック

AgentEthan2はツール実行前に自動的に権限をチェック：

1. ツールが`permissions`属性を宣言
2. ランタイムが`policies.permissions`と照合
3. 未承認の場合`ERR_TOOL_PERMISSION_DENIED`を発生

---

## データマスキング

### 機密データ

ログ内の機密データを常にマスク：

```yaml
policies:
  masking:
    fields:
      # 認証情報
      - inputs.api_key
      - inputs.password
      - inputs.auth_token
      - outputs.session_token
      
      # 個人データ
      - inputs.ssn
      - inputs.credit_card
      - outputs.user_email
      - outputs.phone_number
      
      # ビジネス機密
      - inputs.api_secret
      - outputs.private_key
    
    mask_value: "***REDACTED***"
```

### PII（個人識別情報）

```yaml
masking:
  fields:
    - inputs.user.email
    - inputs.user.phone
    - inputs.user.address
    - outputs.customer.ssn
    - state.session.user_id
```

### セッションデータの差分マスキング

```yaml
masking:
  diff_fields:
    - state.session_token
    - state.csrf_token
  # 値が変更されたときにマスク（トークン漏洩を防止）
```

---

## 入力検証

### すべての入力を検証

```python
from typing import Any, Mapping

def validate_inputs(inputs: Mapping[str, Any]) -> None:
    """ノード入力を検証"""
    if "user_id" not in inputs:
        raise ValueError("user_id is required")
    # ... その他の検証ロジック
    
    # 型検証
    prompt = inputs.get("prompt")
    if not isinstance(prompt, str):
        raise TypeError("prompt must be a string")
    
    # 長さ検証
    if len(prompt) > 10000:
        raise ValueError("prompt exceeds maximum length (10000)")
    
    # 内容検証（例：悪意のあるパターンなし）
    forbidden_patterns = ["<script>", "javascript:", "data:"]
    prompt_lower = prompt.lower()
    for pattern in forbidden_patterns:
        if pattern in prompt_lower:
            raise ValueError(f"Forbidden pattern detected: {pattern}")

async def my_component(state, inputs, ctx):
    validate_inputs(inputs)
    # ... 残りのコンポーネントロジック
```

### スキーマ検証

Pydanticのようなライブラリを使用：

```python
from pydantic import BaseModel, Field, validator

class ComponentInputs(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    max_results: int = Field(10, ge=1, le=100)
    filters: dict = Field(default_factory=dict)
    
    @validator('query')
    def validate_query(cls, v):
        if '<script>' in v.lower():
            raise ValueError('Invalid query content')
        return v

async def search_component(state, inputs, ctx):
    # 入力を検証・解析
    validated = ComponentInputs(**inputs)
    
    # 検証済み入力を使用
    results = await search_api.query(
        query=validated.query,
        limit=validated.max_results,
        filters=validated.filters,
    )
    return {"results": results}
```

### 厳格なJSON検証 (`strict_json`)

AgentEthan2は、`agent_ethan2.validation.strict_json` モジュールを通じて、LLMの出力が特定のJSONスキーマに厳密に準拠していることを検証する機能を提供します。これにより、LLMからの不正な形式のJSON出力によるダウンストリーム処理のエラーを防ぎ、エージェントの堅牢性を高めます。

**ユースケース**:
-   LLMが特定の構造を持つJSONオブジェクトを生成する必要がある場合。
-   LLMの出力が、後続のノードやツールへの入力として使用される場合。

**設定例**:
```yaml
# componentsセクションでLLMコンポーネントを定義
components:
  - id: json_generator_llm
    type: llm
    provider: openai
    config:
      model: gpt-4
      # strict_json_schema を指定
      strict_json_schema:
        type: object
        properties:
          name: {type: string}
          age: {type: integer}
          isStudent: {type: boolean}
        required: [name, age]
```

この設定により、`json_generator_llm` コンポーネントの出力は、指定されたJSONスキーマに対して自動的に検証されます。検証に失敗した場合、エラーが報告されます。

---

## 安全なデプロイ

### コンテナセキュリティ

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

# 非rootユーザーとして実行
RUN useradd -m -u 1000 agent
USER agent

# 依存関係をインストール
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションをコピー
COPY --chown=agent:agent . .

# アプリケーションを実行
CMD ["python", "main.py"]
```

### ネットワークセキュリティ

ネットワークアクセスを制限：

```yaml
# docker-compose.yml
services:
  agent:
    networks:
      - internal
    # 必要でない限り外部ネットワークアクセスなし

networks:
  internal:
    internal: true
```

### 環境の分離

```bash
# 別々の環境を使用
export ENV=production
export LOG_LEVEL=warning
export ENABLE_DEBUG=false
```

### レート制限

悪用を防止：

```yaml
policies:
  rate_limit:
    providers:
      - target: openai
        type: token_bucket
        capacity: 60
        refill_rate: 1.0  # 1リクエスト/秒
```

### 監視

セキュリティ問題を監視：

```yaml
runtime:
  exporters:
    - type: jsonl
      path: /var/log/agent/security.jsonl
```

以下を監視：
- `ERR_TOOL_PERMISSION_DENIED`
- `rate.limit.wait`イベント
- 異常な入力パターン
- 認証失敗の試行

---

## インシデント対応

### ロギング

調査のための包括的なロギング：

```yaml
runtime:
  exporters:
    - type: jsonl
      path: /var/log/agent/audit.jsonl

policies:
  masking:
    fields:
      - inputs.password  # 機密データをマスク
    # ただし調査に十分なログを記録
```

### アラート

セキュリティイベントのアラートを設定：

```python
from agent_ethan2.telemetry import EventBus

class SecurityAlertExporter:
    def export(self, event: str, payload: dict) -> None:
        if event == "error.raised":
            if "PERMISSION_DENIED" in payload.get("message", ""):
                self.send_alert("Permission denied", payload)
        
        if event == "rate.limit.wait":
            if payload.get("wait_time", 0) > 5.0:
                self.send_alert("Excessive rate limiting", payload)
    
    def send_alert(self, message: str, payload: dict):
        # 監視サービスに送信
        pass
```

### 失効

侵害された認証情報を迅速に失効：

```python
# 緊急認証情報ローテーション
def rotate_credentials():
    # 1. 新しい認証情報を生成
    # 2. シークレットマネージャーを更新
    # 3. サービスを再起動
    # 4. 古い認証情報を失効
    pass
```

---

## セキュリティチェックリスト

### 開発
- [ ] シークレットをgitにコミットしない
- [ ] シークレットには環境変数を使用
- [ ] すべてのユーザー入力を検証
- [ ] 出力をサニタイズ
- [ ] パラメータ化されたクエリを使用
- [ ] ノード権限を宣言

### 設定
- [ ] データマスキングを有効化
- [ ] 権限ポリシーを設定
- [ ] レート制限を設定
- [ ] コスト制限を設定
- [ ] 最小権限の原則を使用

### デプロイ
- [ ] 非rootユーザーとして実行
- [ ] コンテナ分離を使用
- [ ] 監査ロギングを有効化
- [ ] 監視アラートを設定
- [ ] 定期的なセキュリティ更新
- [ ] インシデント対応計画

---

## 関連ドキュメント

- [ポリシー](./policies.md) - ポリシー設定
- [カスタムツール](./custom_tools.md) - 安全なツール開発
- [カスタムロジックノード](./custom_logic_node.md) - 安全なノード開発
- [ランタイム設定](./runtime-config.md) - ファクトリーのセキュリティ