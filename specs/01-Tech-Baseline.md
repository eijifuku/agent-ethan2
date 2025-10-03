# 01. 技術ベースライン（Codex前提）

## ランタイム / 言語
- Python: **3.10+**（3.10〜3.12で動作）
- OS: Linux（Ubuntu系を想定）

## 主要ライブラリ（バージョン固定の指針）
- langchain: **latest stable**（実装時点での安定版で固定）
- pydantic: v2 系
- pyyaml
- jsonschema（YAML v2 スキーマ検証用）
- pytest / pytest-asyncio
- mypy（strict 推奨）
- ruff（lint）

## コマンド（Make ターゲットの期待名のみ）
- `make test` … pytest 一式
- `make type` … mypy 実行
- `make lint` … ruff 実行
- `make docs` … docs ビルド（mkdocs/sphinx は後決めでOK）

## 開発規約（抜粋）
- 型注釈必須（public API）
- 例外は**仕様のエラーコード**にマッピング
- ログは**イベント経由**（直接 print/logging.basicConfig は禁止）
