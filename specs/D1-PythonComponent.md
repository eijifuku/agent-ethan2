**Title**: [D1] PythonComponent IF/ctx/ライフサイクル

**Goal / 背景**
- __call__(state, inputs, ctx) と close() 契約の実装。

**Scope / I/O**
- 入力: component 定義 + ノード
- 出力: 呼出結果 + リソース解放

**Specs**
- ctx: logger, cancel_token, deadlines, registries, config。async対応、close任意。シグネチャ検査。

**Error Codes / Warnings**
- ERR_COMPONENT_SIGNATURE

**Events**
- node.start/finish, error.raised

**Dependencies**
- A3,B1

**Acceptance (DoD)**
- 非同期/close 有の解放テストが緑。

**Tests**
- 正常系: 正常/async/closeあり
- 異常系: シグネチャ不一致

**Size**: M
