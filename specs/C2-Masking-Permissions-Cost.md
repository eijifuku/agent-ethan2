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
