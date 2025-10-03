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
