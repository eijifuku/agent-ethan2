# Logging & Telemetry

Monitoring and debugging your agent with telemetry exporters.

## Overview

AgentEthan2 provides multiple telemetry exporters for logging and monitoring:

- **JSONL** - JSON Lines file output
- **Console** - Terminal output with colors
- **LangSmith** - LangSmith integration
- **Prometheus** - Metrics export

## Configuration

### YAML Definition

```yaml
runtime:
  exporters:
    - type: jsonl
      path: run.jsonl
    - type: console
      verbose: false
      color: true
```

## JSONL Exporter

Write events to JSON Lines file.

```yaml
runtime:
  exporters:
    - type: jsonl
      path: logs/agent.jsonl
```

**Output**:
```json
{"event":"graph.start","graph_name":"my_agent","run_id":"abc123","timestamp":"2024-01-01T00:00:00Z"}
{"event":"node.start","node_id":"step1","timestamp":"2024-01-01T00:00:01Z"}
{"event":"node.finish","node_id":"step1","duration":1.5,"timestamp":"2024-01-01T00:00:02Z"}
```

## Console Exporter

Print events to console.

```yaml
runtime:
  exporters:
    - type: console
      color: true
      verbose: true      # true = full payloads / false = compact
      filter_events:     # optional whitelist, e.g. ["graph.start", "graph.finish"]
        - graph.start
        - graph.finish
```

## LangSmith Exporter

Send traces to LangSmith.

```yaml
runtime:
  exporters:
    - type: langsmith
      api_key: ${LANGSMITH_API_KEY}
      project_name: my-agent-project
```

## Prometheus Exporter

Expose metrics for Prometheus.

```yaml
runtime:
  exporters:
    - type: prometheus
      port: 9090
```

## Multiple Exporters

Combine multiple exporters:

```yaml
runtime:
  exporters:
    - type: jsonl
      path: logs/agent.jsonl
    - type: console
      color: true
      verbose: false
    - type: langsmith
      api_key: ${LANGSMITH_API_KEY}
      project_name: production
    - type: prometheus
      port: 9090
```

## Examples

See [Example 08: Telemetry Exporters](../../examples/08_telemetry_exporters/) for working code.

## Next Steps

- See [Hook Methods](./hook_methods.md) for custom logging
- Learn about [Examples](./examples.md)
