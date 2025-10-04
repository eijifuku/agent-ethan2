# プロバイダー

AgentEthan2 で LLM プロバイダーを設定・利用する方法です。

## デフォルトファクトリー

AgentEthan2 には主要プロバイダーのファクトリーが同梱されています。追加設定なしで YAML から直接利用できます。

| プロバイダー種別 | ファクトリーパス | 主な設定キー |
| ---------------- | ---------------- | ------------- |
| `openai`         | `agent_ethan2.providers.openai.create_openai_provider` | `api_key`, `model`, `base_url`, `organization`, `timeout`, `max_retries`, `temperature` |
| `anthropic`      | `agent_ethan2.providers.anthropic.create_anthropic_provider` | `api_key`, `model`, `max_tokens`, `temperature` |

ファクトリーは `providers[].config` を参照し、未指定の場合は既定の環境変数から値を補完します。

## 基本的な使い方

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      # api_key は config または OPENAI_API_KEY から解決される

components:
  - id: answer_llm
    type: llm
    provider: openai
    inputs:
      prompt: graph.inputs.user_prompt
    outputs:
      text: $.choices[0].text
```

デフォルトの OpenAI ファクトリーが自動的にクライアントを生成し、コンポーネントへ渡します。

## 環境変数

| プロバイダー | 環境変数 | 役割 |
| ------------ | -------- | ---- |
| OpenAI | `OPENAI_API_KEY` | API キー |
| OpenAI | `OPENAI_MODEL` | デフォルトモデル |
| OpenAI | `OPENAI_BASE_URL` | OpenAI 互換エンドポイントのベース URL |
| OpenAI | `OPENAI_ORGANIZATION` | 組織 ID |
| OpenAI | `OPENAI_TIMEOUT` | タイムアウト（秒） |
| OpenAI | `OPENAI_MAX_RETRIES` | リトライ回数 |
| OpenAI | `OPENAI_TEMPERATURE` | サンプリング温度 |
| Anthropic | `ANTHROPIC_API_KEY` | API キー |
| Anthropic | `ANTHROPIC_MODEL` | デフォルトモデル |
| Anthropic | `ANTHROPIC_MAX_TOKENS` | トークン上限 |
| Anthropic | `ANTHROPIC_TEMPERATURE` | サンプリング温度 |

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

## ローカル／セルフホスト LLM

OpenAI ファクトリーは OpenAI 互換 API を提供するエンドポイント（Ollama、LM Studio、vLLM など）に対応しています。`base_url` を指定すると API キーは任意になります。

```yaml
providers:
  - id: local_llm
    type: openai
    config:
      model: llama3
      base_url: http://localhost:11434/v1
      api_key: dummy  # Ollama では任意
```

## 複数プロバイダーの併用

複数のプロバイダーを同一プロジェクトで併用できます。

```yaml
providers:
  - id: openai_fast
    type: openai
    config:
      model: gpt-4o-mini

  - id: claude
    type: anthropic
    config:
      model: claude-3-5-sonnet-latest
      max_tokens: 2048

components:
  - id: classifier
    type: llm
    provider: openai_fast
  - id: writer
    type: llm
    provider: claude
```

## プロバイダーコンテキスト

ファクトリーはコンポーネントファクトリーへ渡されるマッピングを返します。組み込みファクトリーでは以下の情報を提供します。

```python
{
    "client": <SDK クライアント>,
    "model": "...",            # 解決済みモデル名
    "config": {...},             # providers[].config のコピー
    # OpenAI 専用:
    "base_url": "..." or None,
    "organization": "..." or None,
    "timeout": float | None,
    "max_retries": int | None,
    "temperature": float | None,
    # Anthropic 専用:
    "max_tokens": int | None,
    "temperature": float | None,
}
```

コンポーネントは必要に応じてこの情報を参照できます。

## ファクトリーの上書き順序

`AgentEthan` は次の優先順位でファクトリーをマージします（後勝ち）。

1. `AgentEthan` コンストラクタ引数 (`provider_factories`)
2. YAML の `runtime.factories.providers`
3. 組み込みのデフォルト (`DEFAULT_PROVIDER_FACTORIES`)

独自の処理へ置き換えたい場合は、カスタムファクトリーを登録してください。詳細な手順は [プロバイダー（応用）](./providers-advanced.md) を参照してください。

## ベストプラクティス

- 秘匿情報は YAML ではなく環境変数で管理する
- タイムアウトとリトライを明示的に設定する
- 同一プロバイダー ID を共有してクライアント生成を抑制する
- 開発環境では可能な限りローカルモデルを活用する
- 複雑な初期化が必要な場合はカスタムファクトリーに切り出す

## 参考資料

- [ランタイム設定](./runtime-config.md)
- [プロバイダー（応用）](./providers-advanced.md)
- [サンプルコード](../examples/)
