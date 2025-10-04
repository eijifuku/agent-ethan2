# プロバイダー（応用）

組み込み以外のプロバイダーを追加したり、既定のファクトリーを拡張・置き換えるためのガイドです。

## カスタムファクトリーが必要になるケース

- AgentEthan2 に含まれていないプロバイダー（Azure OpenAI、Bedrock、自前 API など）を扱う
- 追加のバリデーションやメトリクス収集など、デフォルト処理にフックしたい
- 複数プロバイダー間で高コストなクライアントを共有したい

## `ProviderFactoryBase` の活用

共通のバリデーションとエラーハンドリングを再利用するため、`ProviderFactoryBase` から継承すると便利です。

```python
from __future__ import annotations

import os
from typing import Mapping

from agent_ethan2.graph.errors import GraphExecutionError
from agent_ethan2.ir import NormalizedProvider
from agent_ethan2.providers.base import ProviderFactoryBase


class AzureOpenAIProviderFactory(ProviderFactoryBase):
    error_code = "ERR_PROVIDER_AZURE_OPENAI"

    def build(self, provider: NormalizedProvider) -> Mapping[str, object]:
        try:
            from openai import AzureOpenAI  # azure-openai SDK
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise GraphExecutionError(
                self.error_code,
                "Azure OpenAI を利用するには azure-openai パッケージをインストールしてください。",
                pointer=self._pointer(provider),
            ) from exc

        api_key = self.require_config_value(
            provider,
            "api_key",
            env_var="AZURE_OPENAI_API_KEY",
        )
        endpoint = self.require_config_value(
            provider,
            "endpoint",
            env_var="AZURE_OPENAI_ENDPOINT",
        )
        deployment = self.require_config_value(provider, "deployment")

        api_version = self.get_config_value(
            provider,
            "api_version",
            env_var="AZURE_OPENAI_API_VERSION",
            default="2024-05-01",
        )

        client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint,
        )

        return {
            "client": client,
            "deployment": deployment,
            "api_version": api_version,
            "config": dict(provider.config),
        }


def create_azure_openai_provider(provider: NormalizedProvider) -> Mapping[str, object]:
    return AzureOpenAIProviderFactory()(provider)
```

## ファクトリーの登録方法

### YAML で登録

```yaml
runtime:
  factories:
    providers:
      azure_openai: my_project.factories.azure.create_azure_openai_provider
```

### `AgentEthan` コンストラクタで登録

```python
agent = AgentEthan(
    "agent.yaml",
    provider_factories={
        "azure_openai": "my_project.factories.azure.create_azure_openai_provider",
    },
)
```

コンストラクタ引数 > YAML > 組み込みデフォルト の順に上書きされます。

## デフォルトの上書き

OpenAI の既定ファクトリーを置き換える場合、`openai` キーに自作ファクトリーを指定します。

```yaml
runtime:
  factories:
    providers:
      openai: my_project.factories.openai_logging_provider
```

デフォルトに小さな調整だけを加えたい場合は、既定ファクトリーをラップする方法もあります。

```python
from agent_ethan2.providers.openai import create_openai_provider


def create_openai_with_logging(provider: NormalizedProvider):
    context = create_openai_provider(provider)
    context["client"].responses.stream = True  # 例: ストリーミングを有効化
    return context
```

## バリデーションとエラーコード

- 必須設定には `require_config_value` を用いて、分かりやすい `GraphExecutionError` を発生させる
- 独自の `error_code` を指定してトラブルシューティングを容易にする
- ユーザーが取るべきアクション（不足している環境変数など）をメッセージに含める

## テストのヒント

- SDK クライアントを monkeypatch してネットワーク呼び出しを防ぐ
- ファクトリーが返すマッピングと、クライアント生成時の引数を検証する
- 認証情報の欠如や不正な数値などの異常系もカバーする

## 関連ドキュメント

- [プロバイダー概要](./providers.md)
- [ランタイム設定](./runtime-config.md)
