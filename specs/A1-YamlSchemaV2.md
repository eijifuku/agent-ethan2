**Title**: [A1] YAML スキーマ v2 実装（検証＆エラーコード）

**Goal / 背景**
- ルート/プロバイダ/ツール/コンポーネント/ノード/グラフ/ポリシーの厳格検証を行う。

**Scope / I/O**
- 入力: YAML (v2)
- 出力: IR または 検証エラー（コード付）

**Specs**
- フィールド型/既定値/許容値のバリデーション。未知値・重複・参照不整合の検出。行/キー特定付きメッセージ。

**Error Codes / Warnings**
- ERR_META_VERSION_UNSUPPORTED, ERR_PROVIDER_DUP, ERR_TOOL_DUP, ERR_COMPONENT_DUP, ERR_NODE_DUP, ERR_RUNTIME_ENGINE_UNSUPPORTED, ERR_OUTPUT_KEY_COLLISION ほか

**Events**
- （なし：ビルド時検証）

**Dependencies**
- なし

**Acceptance (DoD)**
- 仕様表の全エラーコードを再現するテストスイートが緑。不正YAMLで正確な行/キーを含むメッセージ。

**Tests**
- 正常系: 代表的な正常YAMLがIR化される
- 異常系: 必須欠落/型不一致/重複/未知値/許容外の網羅

**Size**: M
