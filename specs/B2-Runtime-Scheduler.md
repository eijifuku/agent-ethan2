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
