# プロバイダー

エージェントのLLMプロバイダーの設定方法。

## 概要

プロバイダーはLLMサービスへの接続です（OpenAI、Anthropic、ローカルモデルなど）。各プロバイダーは：
- 一意のIDを持つ
- タイプを指定する
- プロバイダー固有の設定を含む
- ファクトリー関数によってインスタンス化される

## 設定

### YAML定義

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
```

### ファクトリー実装

```python
import os
from openai import OpenAI

def provider_factory(provider):
    """Create OpenAI client from provider config."""
    api_key = provider.config.get("api_key") or os.getenv("OPENAI_API_KEY")
    model = provider.config.get("model", "gpt-4o-mini")
    
    client = OpenAI(api_key=api_key)
    
    return {
        "client": client,
        "model": model,
        "config": dict(provider.config)
    }
```

## OpenAIプロバイダー

### 基本設定

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
```

### 高度な設定

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
      organization: org-xxx
      timeout: 30
      max_retries: 3
      temperature: 0.7
```

## ローカルLLM（OpenAI互換）

Ollama、LM Studioなどのローカルモデルには `base_url` を使用します。

### Ollama

```yaml
providers:
  - id: ollama
    type: openai
    config:
      model: llama2
      base_url: http://localhost:11434/v1
      api_key: dummy  # Ollama doesn't need a real key
```

### LM Studio

```yaml
providers:
  - id: lmstudio
    type: openai
    config:
      model: local-model
      base_url: http://localhost:1234/v1
      api_key: dummy
```

### base_url対応ファクトリー

```python
def provider_factory(provider):
    api_key = provider.config.get("api_key") or os.getenv("OPENAI_API_KEY")
    model = provider.config.get("model", "gpt-4o-mini")
    
    # Support for local LLMs
    client_kwargs = {"api_key": api_key}
    if "base_url" in provider.config:
        client_kwargs["base_url"] = provider.config["base_url"]
    
    client = OpenAI(**client_kwargs)
    
    return {"client": client, "model": model}
```

## 複数プロバイダー

異なるタスクに異なるプロバイダーを使用：

```yaml
providers:
  - id: openai_fast
    type: openai
    config:
      model: gpt-4o-mini
  
  - id: openai_smart
    type: openai
    config:
      model: gpt-4o
  
  - id: local_llm
    type: openai
    config:
      model: llama2
      base_url: http://localhost:11434/v1

components:
  - id: classifier
    type: llm
    provider: openai_fast  # Fast model for classification
  
  - id: writer
    type: llm
    provider: openai_smart  # Smart model for generation
  
  - id: summarizer
    type: llm
    provider: local_llm  # Local model for summarization
```

## プロバイダーの戻り値形式

ファクトリー関数は以下を含むdictを返す必要があります：

```python
{
    "client": client_instance,    # LLM client
    "model": "model-name",         # Model identifier
    "config": dict(provider.config)  # Original config
}
```

これによりノードは以下にアクセスできます：
- `provider_instance["client"]` - LLMクライアント
- `provider_instance["model"]` - モデル名
- `provider_instance["config"]` - プロバイダー設定

## 環境変数

機密データには環境変数を使用します：

```yaml
providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini
      api_key: ${OPENAI_API_KEY}
```

```bash
export OPENAI_API_KEY=sk-...
```

## ベストプラクティス

1. **環境変数を使用** - APIキーをハードコードしない
2. **適切なタイムアウトを設定** - リクエストがハングするのを防ぐ
3. **リトライを設定** - 一時的な障害に対処
4. **開発にはローカルLLMを使用** - コストを削減
5. **高速/高性能モデルを分離** - コストとレイテンシを最適化

## サンプル

動作するコードについては [examples/01_basic_llm/](../../examples/01_basic_llm/) を参照してください。

## 次のステップ

- [カスタムロジックノード](./custom_logic_node.md) について学ぶ
- 会話管理については [チャット履歴](./chat_history.md) を参照
- 完全な仕様については [YAMLリファレンス](./yaml_reference.md) を参照
