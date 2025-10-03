# イベント一覧

| Event | Payload (抜粋) | 説明 |
| ----- | --------------- | ---- |
| `graph.start` | `run_id`, `graph_name`, `entrypoint`, `ts` | グラフ実行開始 |
| `graph.finish` | `status`, `outputs`, `ts` | グラフ終了 (success/timeout/error/cancelled) |
| `node.start` | `node_id`, `kind`, `started_at`, `graph_name`, `ts` | ノード開始 |
| `node.finish` | `node_id`, `status`, `duration_ms`, `outputs` | ノード終了 |
| `llm.call` | `provider_id`, `model`, `tokens_in/out`, `inputs`, `outputs` | LLM 呼出結果 |
| `tool.call` | `tool_id`, `component_id`, `required_permissions`, `inputs`, `outputs` | ツール呼出結果 |
| `retry.attempt` | `node_id`, `attempt`, `delay`, `error` | リトライ発生 |
| `timeout` | `graph_name`, `timeout`, `ts` | スケジューラのタイムアウト |
| `cancelled` | `graph_name`, `ts` | 実行がキャンセルされた |
| `rate.limit.wait` | `scope`, `target`, `wait_time` | レート制限の待機が発生 |
| `error.raised` | `node_id`, `kind`, `message` | 例外検知 (実行・クローズ時含む) |

EventBus では `sequence` を付与し、マスキング後にエクスポーターへ転送します。各イベントに `run_id` と `ts` が含まれるため、外部システムでの相関も容易です。
