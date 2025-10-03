# AgentEthan2 — 分割イシュー束（Codex向け）
LangChain（Runnable/LCEL）集中の YAML エージェント「AgentEthan2」の実装タスクを**ファイル単位**で分割。  
各ファイルをそのまま Codex に渡して実装を進められます（コード例なし）。

## 目次
- A: スキーマ / IR / DI（基盤） … A1/A2/A3
- B: 実行エンジン（Runnable/LCEL） … B1/B2/B3/B4
- C: 観測性 / セキュリティ … C1/C2/C3
- D: PythonComponent（関数注入の自然化） … D1
- E: 互換 / 移行 / ドキュメント … E1/E2
- F: 運用の磨き込み（Nice-to-have） … F1/F2

**共通ポリシー**
- DoR: スコープ/入出力/依存/エラー/テスト観点を明記
- DoD: テスト緑、イベント/例外が仕様どおり、Docs更新、CI通過
- CI: mypy, ruff, pytest, coverage≥85%, JSON Schema 検証, ドキュメントビルド
