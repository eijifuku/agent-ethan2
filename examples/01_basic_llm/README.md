# 01_basic_llm — Minimal LLM Call

## 1. 目的
単一の LLM ノードでユーザー入力に応答する最小構成の例です。AgentEthan2 の YAML v2、GraphBuilder、Scheduler の流れを体験できます。

## 2. 使用機能
- YAML v2 スキーマによる設定
- OpenAI provider を利用した `llm` コンポーネント
- Runtime デフォルトでの provider 指定
- Telemetry 出力（EventBus を設定すれば JSONL/OTLP へ記録可能）

## 3. ファイル構成
```
examples/01_basic_llm/
  ├─ config.yaml   # LLM ノードのみで構成された YAML
  └─ README.md     # このファイル
```

## 4. 実行方法
```bash
export OPENAI_API_KEY="sk-..."          # 必須
export OPENAI_MODEL="gpt-4o-mini"       # 任意（既定: gpt-4o-mini）
pip install openai

cd examples/01_basic_llm
python -m agent_ethan2.cli config.yaml \
  --inputs '{"user_prompt": "Please summarize the latest AI news."}'

# 付属スクリプトでの実行（簡易デモ）
python run.py
```

実行すると `run.jsonl` に Telemetry が追記され、標準出力には `final_response` が表示されます。

> **補足**: CLI 実装は今後追加予定の場合があります。現時点ではサンプルとして、付属スクリプトが YAML→IR→Graph→Scheduler の流れを実行します。

## 5. config.yaml のポイント
- `meta.version`: 2 … YAML v2 スキーマを明示。
- `runtime.defaults.provider`: `openai` … グラフ全体で既定の provider を設定。
- `providers[0].config.model`: `${OPENAI_MODEL:-gpt-4o-mini}` … 環境変数でモデルを切り替え。
- `components.llm_basic.inputs.prompt`: グラフ入力 `user_prompt` を LLM に渡します。
- `graph.outputs[0].key`: `final_response` … 実行結果として呼び出し側に返すキー。

## 6. カスタマイズ例
### モデルの変更
```bash
export OPENAI_MODEL="gpt-4.1-mini"
```

### プロンプトの調整
ユーザー入力にシステム指示を含めたい場合は、`--inputs` でまとめて渡します。
```bash
python -m agent_ethan2.cli config.yaml \
  --inputs '{"user_prompt": "You are a friendly assistant. Answer in Japanese."}'
```

## 7. 期待される出力
```
{
  "final_response": "最新のAIニュースの要約を返すテキスト..."
}
```

OpenAI のレスポンスに依存しますが、短い要約が `final_response` に格納されます。

---
その他の例やランナーの詳細は `examples/README.md` やプロジェクトドキュメントを参照してください。
