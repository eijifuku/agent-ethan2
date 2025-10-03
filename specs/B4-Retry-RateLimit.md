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
