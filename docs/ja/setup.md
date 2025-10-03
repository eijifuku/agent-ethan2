# セットアップガイド

AgentEthan2をシステムで動作させる。

> 詳細な英語版ドキュメント: [Setup Guide (English)](../en/setup.md)

## 前提条件

- **Python 3.10以上**
- **pip** または **uv** パッケージマネージャー
- **Git** (リポジトリクローン用)

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

## 環境変数

```bash
# OpenAI API（ほとんどのサンプルに必要）
export OPENAI_API_KEY=your-api-key-here

# オプション: その他のプロバイダ用
export ANTHROPIC_API_KEY=your-anthropic-key
export TAVILY_API_KEY=your-tavily-key
```

## サンプルの実行

```bash
cd examples/01_basic_llm
export OPENAI_API_KEY=your-key
python run.py
```

## 開発セットアップ

```bash
# 開発用依存関係をインストール
pip install -e ".[dev]"

# テスト実行
pytest

# 型チェック
mypy agent_ethan2

# リント
ruff check agent_ethan2
```

## トラブルシューティング

### ModuleNotFoundError

```bash
pip install -e .
```

### API Key エラー

```bash
export OPENAI_API_KEY=your-key
```

## 次のステップ

- [YAMLリファレンス](./yaml_reference.md)を読む
- [サンプル](./examples.md)を試す
- [ノード](./nodes.md)について学ぶ


