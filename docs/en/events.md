# Event Reference

| Event | Payload (excerpt) | Description |
| ----- | ----------------- | ----------- |
| `graph.start` | `run_id`, `graph_name`, `entrypoint`, `ts` | Graph execution started |
| `graph.finish` | `status`, `outputs`, `ts` | Graph finished (success/timeout/error/cancelled) |
| `node.start` | `node_id`, `kind`, `started_at`, `graph_name`, `ts` | Node started |
| `node.finish` | `node_id`, `status`, `duration_ms`, `outputs` | Node finished |
| `llm.call` | `provider_id`, `model`, `tokens_in/out`, `inputs`, `outputs` | LLM call result |
| `tool.call` | `tool_id`, `component_id`, `required_permissions`, `inputs`, `outputs` | Tool call result |
| `retry.attempt` | `node_id`, `attempt`, `delay`, `error` | Retry occurred |
| `timeout` | `graph_name`, `timeout`, `ts` | Scheduler timeout |
| `cancelled` | `graph_name`, `ts` | Execution was cancelled |
| `rate.limit.wait` | `scope`, `target`, `wait_time` | Rate limit wait occurred |
| `error.raised` | `node_id`, `kind`, `message` | Exception detected (including execution and close) |

EventBus adds a `sequence` number and forwards events to exporters after masking. Since each event includes `run_id` and `ts`, correlation in external systems is easy.

