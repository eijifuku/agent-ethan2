# MVP Workflow

This chapter explains the pipeline from v2 YAML to execution completion.

## 1. YAML Loading

```python
from agent_ethan2.loader import YamlLoaderV2
from agent_ethan2.ir import normalize_document

loader = YamlLoaderV2()
document = loader.load_file("examples/mvp.yaml")
result = normalize_document(document)
ir = result.ir
```

- After passing A1 validation, `NormalizationResult` stores IR and compatibility warnings.

## 2. Materialization

```python
from agent_ethan2.registry import Registry
from agent_ethan2.graph import GraphBuilder

registry = Registry(...)
resolved = registry.materialize(ir)
definition = GraphBuilder().build(ir, resolved)
```

- Provider/Tool/Component imports are delegated to Registry.
- GraphBuilder revalidates node types and dependencies.

## 3. Scheduler with Monitoring

```python
from agent_ethan2.runtime.scheduler import Scheduler
from agent_ethan2.telemetry import EventBus
from agent_ethan2.telemetry.exporters.jsonl import JsonlExporter

bus = EventBus(exporters=[JsonlExporter(path="run.jsonl")])
scheduler = Scheduler()
result = await scheduler.run(
    definition,
    inputs={"prompt": "hello"},
    event_emitter=bus,
)
print(result.outputs)
```

- ctx provides `logger`, `cancel_token`, `deadline`, `registries`, `config`, and calls `close()` after execution if available.
- EventBus applies permissions, cost, and masking before outputting to JSONL / Console / LangSmith / Prometheus exporters.

## 4. Execution Tree Export

```python
from agent_ethan2.telemetry import ExecutionTreeBuilder

builder = ExecutionTreeBuilder()
bus.register(builder)
...  # run scheduler
print(builder.build())
```

- Uses `graph.start/finish`, `node.*`, `retry.attempt`, `timeout`, `cancelled` events to reconstruct DAG + timeline.

## Notes

- For v1 YAML, use `agent_ethan2.converters.v1_to_v2.convert_v1_to_v2` for minimal conversion.
- `Scheduler.run`'s `timeout` and `deadline` are independent, and `cancel_token` is set on error/timeout/cancellation.

