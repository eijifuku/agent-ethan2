

---

# 00-README.md

# AgentEthan2 — 分割イシュー束（Codex向け）
LangChain（Runnable/LCEL）集中の YAML エージェント「AgentEthan2」の実装タスクを**ファイル単位**で分割。  
各ファイルをそのまま Codex に渡して実装を進められます（コード例なし）。

## 目次
- A: スキーマ / IR / DI（基盤） … A1/A2/A3
- B: 実行エンジン（Runnable/LCEL） … B1/B2/B3/B4
- C: 観測性 / セキュリティ … C1/C2/C3
- D: PythonComponent（関数注入の自然化） … D1
- E: 互換 / 移行 / ドキュメント … E1/E2
- F: 運用の磨き込み（Nice-to-have） … F1/F2

**共通ポリシー**
- DoR: スコープ/入出力/依存/エラー/テスト観点を明記
- DoD: テスト緑、イベント/例外が仕様どおり、Docs更新、CI通過
- CI: mypy, ruff, pytest, coverage≥85%, JSON Schema 検証, ドキュメントビルド


---

# A1-YamlSchemaV2.md

**Title**: [A1] YAML スキーマ v2 実装（検証＆エラーコード）

**Goal / 背景**
- ルート/プロバイダ/ツール/コンポーネント/ノード/グラフ/ポリシーの厳格検証を行う。

**Scope / I/O**
- 入力: YAML (v2)
- 出力: IR または 検証エラー（コード付）

**Specs**
- フィールド型/既定値/許容値のバリデーション。未知値・重複・参照不整合の検出。行/キー特定付きメッセージ。

**Error Codes / Warnings**
- ERR_META_VERSION_UNSUPPORTED, ERR_PROVIDER_DUP, ERR_TOOL_DUP, ERR_COMPONENT_DUP, ERR_NODE_DUP, ERR_RUNTIME_ENGINE_UNSUPPORTED, ERR_OUTPUT_KEY_COLLISION ほか

**Events**
- （なし：ビルド時検証）

**Dependencies**
- なし

**Acceptance (DoD)**
- 仕様表の全エラーコードを再現するテストスイートが緑。不正YAMLで正確な行/キーを含むメッセージ。

**Tests**
- 正常系: 代表的な正常YAMLがIR化される
- 異常系: 必須欠落/型不一致/重複/未知値/許容外の網羅

**Size**: M


---

# A2-IR-Normalization-Compat.md

**Title**: [A2] IR 正規化 / 互換警告

**Goal / 背景**
- 既定値充填、参照解決、v1→v2 非互換の警告生成。

**Scope / I/O**
- 入力: A1を通過したYAML
- 出力: 正規化IR + 警告リスト

**Specs**
- *_ref 解決・default provider 確定・未参照ノード警告。v1→v2非互換（ノード命名整理、inputs/outputs必須化、error_policy統一）の警告生成。

**Error Codes / Warnings**
- ERR_GRAPH_ENTRY_NOT_FOUND, ERR_EDGE_ENDPOINT_INVALID ほか

**Events**
- （なし）

**Dependencies**
- A1

**Acceptance (DoD)**
- サンプル v1 入力→ v2 IR + 警告が出力される。

**Tests**
- 正常系: 代表YAMLで既定値充填と参照解決が機能
- 異常系: 未定義参照/エントリ欠落/エッジ不整合

**Size**: M


---

# A3-Resolver-Registry.md

**Title**: [A3] Resolver/Registry（Provider/Tool/Component）

**Goal / 背景**
- import解決、シグネチャ検査、インスタンスキャッシュの実装。

**Scope / I/O**
- 入力: 正規化IR
- 出力: 実体化された Provider/Tool/Component

**Specs**
- 遅延ロードとキャッシュ。tool permissions の静的検査。component callable のシグネチャ検査（__call__(state, inputs, ctx)）。

**Error Codes / Warnings**
- ERR_TOOL_IMPORT, ERR_COMPONENT_IMPORT, ERR_COMPONENT_SIGNATURE, ERR_TOOL_PERM_TYPE

**Events**
- （初期化ログのみ任意）

**Dependencies**
- A2

**Acceptance (DoD)**
- import失敗/署名不一致で指定エラー。キャッシュがhitする。

**Tests**
- 正常系: 正しい定義で実体化できる
- 異常系: import失敗/不正署名/権限型不正

**Size**: M


---

# B1-GraphBuilder-Core.md

**Title**: [B1] GraphBuilder（直列/LLM/Tool/Router）

**Goal / 背景**
- 最小構成のグラフを Runnable に合成。

**Scope / I/O**
- 入力: IR + Resolver実体
- 出力: Runnableグラフ

**Specs**
- LLMNode/ToolNode/RouterNodeの合成と配線検証。outputsマップ/キー衝突検出。テンプレ/式の評価器を接続。

**Error Codes / Warnings**
- ERR_NODE_TYPE, ERR_TOOL_NOT_FOUND, ERR_PROVIDER_DEFAULT_MISSING, ERR_ROUTER_NO_MATCH

**Events**
- node.start/finish, llm.call, tool.call, error.raised

**Dependencies**
- A3

**Acceptance (DoD)**
- LLM→Tool→RouterのIRで期待のstate遷移・イベント発火。

**Tests**
- 正常系: 直列フローの正常系
- 異常系: 不明ノード/ルータ不一致/LLM JSONパース失敗

**Size**: L


---

# B2-Runtime-Scheduler.md

**Title**: [B2] Runtime/Scheduler（async/timeout/cancel）

**Goal / 背景**
- TaskGroupでキャンセル伝播/締切/例外処理を実装。

**Scope / I/O**
- 入力: Runnableグラフ
- 出力: 実行結果 + イベント

**Specs**
- 親キャンセル→子キャンセル、deadline超過でtimeoutイベント。cancel_on_error の実装。

**Error Codes / Warnings**
- TimeoutError 統一ハンドリング

**Events**
- graph.start/finish, node.start/finish, timeout, cancelled, error.raised

**Dependencies**
- B1

**Acceptance (DoD)**
- タイムアウト/キャンセル時に正しい順序でイベント発火。

**Tests**
- 正常系: 正常完了/手動キャンセル/期限超過
- 異常系: 子タスク暴走/例外未捕捉

**Size**: L


---

# B3-Map-Parallel.md

**Title**: [B3] Map/Parallel（ordered/merge_policy/部分失敗）

**Goal / 背景**
- 配列並列と複数子ノードの同時実行＋集約を提供。

**Scope / I/O**
- 入力: 配列/子ノード定義
- 出力: 集約結果（成功/失敗モードに従う）

**Specs**
- Map: concurrency, ordered, failure_mode(fail_fast/collect_errors/skip_failed)。Parallel: mode(all/first_success/any), merge_policy(overwrite/namespace/error)。

**Error Codes / Warnings**
- ERR_MAP_OVER_NOT_ARRAY, ERR_MAP_BODY_NOT_FOUND, ERR_PARALLEL_EMPTY

**Events**
- node.start/finish, error.raised

**Dependencies**
- B2

**Acceptance (DoD)**
- 3モードの部分失敗がテストで確認できる。

**Tests**
- 正常系: 全成功/一部失敗/全失敗（各モード）
- 異常系: 配列以外/子ノード未定義/キー衝突

**Size**: L


---

# B4-Retry-RateLimit.md

**Title**: [B4] Retry/RateLimit（戦略パターン）

**Goal / 背景**
- 固定/指数/ジッターのリトライと token_bucket/fixed_window の実装。

**Scope / I/O**
- 入力: ノード実行要求
- 出力: 再試行/待機を含む挙動

**Specs**
- retry.attempt と rate.limit.wait イベント。429/5xx/一時ネット障害の再試行。provider共有スコープは将来F1で拡張。

**Error Codes / Warnings**
- ERR_RETRY_PREDICATE, ERR_RL_POLICY_PARAM

**Events**
- retry.attempt, rate.limit.wait

**Dependencies**
- B2

**Acceptance (DoD)**
- 規定バックオフ/待機の実測がイベントに記録。

**Tests**
- 正常系: 429/5xx/ネット断の復帰
- 異常系: 未知述語/ポリシーパラメタ不足

**Size**: M


---

# C1-EventBus-Telemetry.md

**Title**: [C1] EventBus/Telemetry（JSONL/OTLP）

**Goal / 背景**
- 仕様のイベント全種を統一フォーマットで出力。

**Scope / I/O**
- 入力: ランタイムイベント
- 出力: JSONL/OTLP 出力

**Specs**
- 必須ペイロード（run_id,node_id,model,tokens,duration等）。マスキング適用後に出力。

**Error Codes / Warnings**
- 出力失敗時のローカルフォールバック

**Events**
- （すべて）

**Dependencies**
- B1

**Acceptance (DoD)**
- 必須ペイロードと順序保証が確認できる。

**Tests**
- 正常系: JSONL/OTLP双方のハーネスに出力
- 異常系: 欠損ペイロード/順序乱れ

**Size**: M


---

# C2-Masking-Permissions-Cost.md

**Title**: [C2] Masking/Permissions/Cost Limits

**Goal / 背景**
- ログ直前マスキング、ツール権限ゲート、トークン/回数上限を提供。

**Scope / I/O**
- 入力: 実行入出力/ツール呼出/LLM呼出
- 出力: マスク済みログ/拒否エラー/上限超過エラー

**Specs**
- FS/HTTP/exec デフォルト拒否、宣言的許可のみ。差分マスク、1-run/日次コスト上限。

**Error Codes / Warnings**
- 権限: ERR_TOOL_PERM_TYPE / 上限超過: 専用エラー

**Events**
- tool.call（masked）, error.raised

**Dependencies**
- A3,B1

**Acceptance (DoD)**
- 未許可操作の確実な拒否と差分マスク適用。

**Tests**
- 正常系: 許可/不許可の境界/上限前後
- 異常系: 権限型不正/マスク不適用

**Size**: M


---

# C3-ExecutionTree.md

**Title**: [C3] 実行ツリー（DAG＋タイムライン要約）

**Goal / 背景**
- デバッグ用に実行ツリー JSON を生成。

**Scope / I/O**
- 入力: イベントストリーム
- 出力: 実行ツリー JSON

**Specs**
- 開始/終了/再試行/所要/親子関係を可視化。任意実行でエクスポート可能に。

**Error Codes / Warnings**
- 生成失敗時のフォールバック

**Events**
- graph.start/finish, node.*, retry.*, timeout, cancelled

**Dependencies**
- C1

**Acceptance (DoD)**
- 代表実行でツリーJSONが出力される。

**Tests**
- 正常系: 単純/並列/失敗含むケースで構造が妥当
- 異常系: 欠損イベント時の復元

**Size**: M


---

# D1-PythonComponent.md

**Title**: [D1] PythonComponent IF/ctx/ライフサイクル

**Goal / 背景**
- __call__(state, inputs, ctx) と close() 契約の実装。

**Scope / I/O**
- 入力: component 定義 + ノード
- 出力: 呼出結果 + リソース解放

**Specs**
- ctx: logger, cancel_token, deadlines, registries, config。async対応、close任意。シグネチャ検査。

**Error Codes / Warnings**
- ERR_COMPONENT_SIGNATURE

**Events**
- node.start/finish, error.raised

**Dependencies**
- A3,B1

**Acceptance (DoD)**
- 非同期/close 有の解放テストが緑。

**Tests**
- 正常系: 正常/async/closeあり
- 異常系: シグネチャ不一致

**Size**: M


---

# E1-Converter-V1toV2.md

**Title**: [E1] v1→v2 コンバータ（最小）

**Goal / 背景**
- 主要フィールドを機械変換し、非互換を警告出力。

**Scope / I/O**
- 入力: v1 YAML
- 出力: v2 IR + 警告

**Specs**
- ノード名/inputs-outputs/error_policy の主な写像。停止せず警告で誘導。

**Error Codes / Warnings**
- —

**Events**
- —

**Dependencies**
- A2

**Acceptance (DoD)**
- 代表 v1→v2 変換＋警告が確認できる。

**Tests**
- 正常系: 主要フィールドの自動変換
- 異常系: 非対応フィールドの扱い（警告）

**Size**: M


---

# E2-Docs.md

**Title**: [E2] ドキュメント（仕様/運用/チューニング）

**Goal / 背景**
- 仕様書の章立てを Markdown 化し、運用ガイドを整備。

**Scope / I/O**
- 入力: 仕様（本ファイル群）
- 出力: docs/*.md

**Specs**
- はじめに / MVP ワークフロー / トラブルシュート。エラーコード一覧とイベント一覧。

**Error Codes / Warnings**
- —

**Events**
- —

**Dependencies**
- 全体

**Acceptance (DoD)**
- 新規参加者が30分で実行デモ到達。

**Tests**
- 正常系: —
- 異常系: —

**Size**: M


---

# F1-Provider-SharedRateLimit.md

**Title**: [F1] Provider 単位の共有 RateLimit スコープ

**Goal / 背景**
- 複数 LLM ノードで同一 provider_ref のスロットを共有。

**Scope / I/O**
- 入力: RateLimit 設定 + provider_ref
- 出力: 共有バケツでの待機制御

**Specs**
- B4実装のスコープ拡張。メトリクス集計。

**Error Codes / Warnings**
- —

**Events**
- rate.limit.wait（scope=provider）

**Dependencies**
- B4

**Acceptance (DoD)**
- 同一 provider のノードがバケツを共有する。

**Tests**
- 正常系: 並列呼出で待機が発生
- 異常系: 異providerが誤って共有しない

**Size**: S


---

# F2-StrictJSON-Validation.md

**Title**: [F2] JSON/Struct 厳格バリデーション拡張

**Goal / 背景**
- より丁寧なスキーマエラー表示と修正提案。

**Scope / I/O**
- 入力: LLM 応答(JSON/struct)
- 出力: 詳細な検証エラー

**Specs**
- 不一致箇所・期待型・例示を含むエラー整形。

**Error Codes / Warnings**
- ERR_LLM_JSON_PARSE（詳細版）

**Events**
- llm.call（失敗詳細は masked message）

**Dependencies**
- B1

**Acceptance (DoD)**
- パース失敗時に簡易修正ガイドが提示される。

**Tests**
- 正常系: 軽微なズレの報告
- 異常系: 巨大JSON時の性能劣化

**Size**: S


---

# 01-Tech-Baseline.md

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


---

# 02-Repo-Layout.md

# 02. リポジトリ構成 / エントリポイント

## 期待ディレクトリ
```
agent_ethan2/
  loader/yaml_loader.py
  ir/model.py
  graph/builder.py
  runtime/scheduler.py
  registry/
    providers.py
    tools.py
    components.py
  policy/
    retry.py
    ratelimit.py
    error.py
    masking.py
  telemetry/
    event_bus.py
    exporters/
      jsonl.py
      otlp.py
schemas/
  yaml_v2.json
  events.schema.json
docs/
  errors.md
  spec/
tests/
examples/
pyproject.toml
```

## パッケージ/CLI
- PyPI 名: **agent-ethan2**
- Python パッケージ: `agent_ethan2`
- CLI（想定）: `python -m agent_ethan2.cli run --yaml examples/mvp.yaml`

## 命名/配置ガイド
- **YamlLoader**: `loader/yaml_loader.py`
- **IR**: `ir/model.py`（pydantic v2）
- **GraphBuilder**: `graph/builder.py`
- **Runtime/Scheduler**: `runtime/scheduler.py`
- **Registry**: `registry/{providers,tools,components}.py`
- **Policy**: `policy/{retry,ratelimit,error,masking}.py`
- **Telemetry**: `telemetry/event_bus.py`, `telemetry/exporters/*`


---

# 03-Identifiers-Schemas.md

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
