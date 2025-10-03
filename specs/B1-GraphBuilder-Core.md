**Title**: [B1] GraphBuilder（直列/LLM/Tool/Router）

**Goal / 背景**
- 最小構成のグラフを Runnable に合成。

**Scope / I/O**
- 入力: IR + Resolver実体
- 出力: Runnableグラフ

**Specs**
- LLMNode/ToolNode/RouterNodeの合成と配線検証。outputsマップ/キー衝突検出。テンプレ/式の評価器を接続。

**Error Codes / Warnings**
- ERR_NODE_TYPE, ERR_TOOL_NOT_FOUND, ERR_PROVIDER_DEFAULT_MISSING, ERR_ROUTER_NO_MATCH

**Events**
- node.start/finish, llm.call, tool.call, error.raised

**Dependencies**
- A3

**Acceptance (DoD)**
- LLM→Tool→RouterのIRで期待のstate遷移・イベント発火。

**Tests**
- 正常系: 直列フローの正常系
- 異常系: 不明ノード/ルータ不一致/LLM JSONパース失敗

**Size**: L
