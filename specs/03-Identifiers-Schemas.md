# 03. 固定識別子 / スキーマ配置

## エラーコード（Source of Truth）
- 仕様で定義した全エラーコードは **`docs/errors.md`** に一覧化
- 実装は共通例外クラスで **コード必須**（例: `ERR_MAP_OVER_NOT_ARRAY`）

## イベントスキーマ
- スキーマ: **`schemas/events.schema.json`**
- 必須フィールド（抜粋）:
  - `run_id`, `graph_name`, `node_id`
  - `event`（例: `graph.start`, `node.finish`, `llm.call`）
  - `ts` / `duration_ms`
  - （llm.call）`provider_id`, `model`, `tokens_in`, `tokens_out`

## YAML v2 スキーマ
- スキーマ: **`schemas/yaml_v2.json`**
- A1 の実装対象。検証はここを単一の正とする。

## 環境変数（型名のみ、値は不要）
- `OPENAI_API_KEY: str?`
- `ANTHROPIC_API_KEY: str?`
- `GOOGLE_API_KEY: str?`
- `AGENT_ETHAN2_LOG_DIR: str?`（JSONL 出力先）

## ルール
- すべてのログは **マスキング適用後** にエクスポート
- スキーマの breaking change は `schemas/` の **バージョン隣置き**で行う
