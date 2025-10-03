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
