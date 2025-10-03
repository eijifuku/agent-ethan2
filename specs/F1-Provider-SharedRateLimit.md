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
