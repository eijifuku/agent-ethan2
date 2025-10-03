# 02. リポジトリ構成 / エントリポイント

## 期待ディレクトリ
```
agent_ethan2/
  loader/yaml_loader.py
  ir/model.py
  graph/builder.py
  runtime/scheduler.py
  registry/
    providers.py
    tools.py
    components.py
  policy/
    retry.py
    ratelimit.py
    error.py
    masking.py
  telemetry/
    event_bus.py
    exporters/
      jsonl.py
      otlp.py
schemas/
  yaml_v2.json
  events.schema.json
docs/
  errors.md
  spec/
tests/
examples/
pyproject.toml
```

## パッケージ/CLI
- PyPI 名: **agent-ethan2**
- Python パッケージ: `agent_ethan2`
- CLI（想定）: `python -m agent_ethan2.cli run --yaml examples/mvp.yaml`

## 命名/配置ガイド
- **YamlLoader**: `loader/yaml_loader.py`
- **IR**: `ir/model.py`（pydantic v2）
- **GraphBuilder**: `graph/builder.py`
- **Runtime/Scheduler**: `runtime/scheduler.py`
- **Registry**: `registry/{providers,tools,components}.py`
- **Policy**: `policy/{retry,ratelimit,error,masking}.py`
- **Telemetry**: `telemetry/event_bus.py`, `telemetry/exporters/*`
