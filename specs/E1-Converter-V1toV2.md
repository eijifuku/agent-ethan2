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
