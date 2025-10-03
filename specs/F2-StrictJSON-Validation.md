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
