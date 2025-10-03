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
