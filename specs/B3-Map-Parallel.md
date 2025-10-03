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
