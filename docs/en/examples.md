# Examples

Walkthrough of included examples.

## Overview

The `examples/` directory contains 10 working examples demonstrating key features:

1. **01_basic_llm** - Simple LLM call
2. **02_llm_with_tool** - LLM + Tool integration
3. **03_router** - Conditional routing
4. **04_map_parallel** - Map/Parallel execution
5. **05_retry_ratelimit** - Retry & Rate limiting
6. **06_component** - Custom components
7. **07_full_agent** - Complete agent
8. **08_telemetry_exporters** - Logging/Telemetry
9. **09_hooks** - Lifecycle hooks
10. **10_conversation_history** - Multi-turn conversations

## Example 01: Basic LLM

**Location**: `examples/01_basic_llm/`

**What it demonstrates**:
- Simple LLM call
- Provider configuration
- Factory functions
- YAML configuration

**Run**:
```bash
cd examples/01_basic_llm
export OPENAI_API_KEY=your-key
python run.py
```

## Example 02: LLM with Tool

**Location**: `examples/02_llm_with_tool/`

**What it demonstrates**:
- Tool integration
- Calculator tool
- LLM + Tool workflow
- Output formatting

**Run**:
```bash
cd examples/02_llm_with_tool
export OPENAI_API_KEY=your-key
python run.py
```

## Example 03: Router

**Location**: `examples/03_router/`

**What it demonstrates**:
- Conditional routing
- Intent classification
- Router node type
- Multi-branch workflows

**Run**:
```bash
cd examples/03_router
export OPENAI_API_KEY=your-key
python run.py
```

## Example 04: Map/Parallel

**Location**: `examples/04_map_parallel/`

**What it demonstrates**:
- Map over collections
- Parallel processing
- Batch operations
- Failure handling

**Run**:
```bash
cd examples/04_map_parallel
export OPENAI_API_KEY=your-key
python run.py
```

## Example 05: Retry & Rate Limit

**Location**: `examples/05_retry_ratelimit/`

**What it demonstrates**:
- Retry policies
- Rate limiting (token bucket, fixed window)
- Error handling
- Resilient execution

**Run**:
```bash
cd examples/05_retry_ratelimit
export OPENAI_API_KEY=your-key
python run.py
```

## Example 06: Custom Components

**Location**: `examples/06_component/`

**What it demonstrates**:
- Custom Python functions
- Data transformation
- Business logic
- Dynamic component loading

**Run**:
```bash
cd examples/06_component
export OPENAI_API_KEY=your-key
python run.py
```

## Example 07: Full Agent

**Location**: `examples/07_full_agent/`

**What it demonstrates**:
- Complete agent workflow
- Router + Tools + LLM
- Intent classification
- Multi-step processing

**Run**:
```bash
cd examples/07_full_agent
export OPENAI_API_KEY=your-key
python run.py
```

## Example 08: Telemetry Exporters

**Location**: `examples/08_telemetry_exporters/`

**What it demonstrates**:
- JSONL exporter
- Console exporter
- LangSmith integration
- Prometheus metrics
- Multiple exporters

**Run**:
```bash
cd examples/08_telemetry_exporters
export OPENAI_API_KEY=your-key
python run_console.py
python run_multiple.py
python run_yaml_config.py
```

## Example 09: Lifecycle Hooks

**Location**: `examples/09_hooks/`

**What it demonstrates**:
- before_execute hook
- after_execute hook
- on_error hook
- Logging and caching use cases

**Run**:
```bash
cd examples/09_hooks
export OPENAI_API_KEY=your-key
python run.py         # Normal execution
python run_error.py   # Error handling
```

## Example 10: Conversation History

**Location**: `examples/10_conversation_history/`

**What it demonstrates**:
- Multi-turn conversations
- Memory backend
- Redis backend
- Multiple history instances
- Session management

**Run**:
```bash
cd examples/10_conversation_history
export OPENAI_API_KEY=your-key
python run.py
```

## Running All Examples

```bash
export OPENAI_API_KEY=your-key

for dir in examples/*/; do
    if [ -f "$dir/run.py" ]; then
        echo "Running $dir"
        (cd "$dir" && python run.py)
    fi
done
```

## Next Steps

- Read [Troubleshooting](./troubleshooting.md) for common issues
- See [YAML Reference](./yaml_reference.md) for complete spec
- Learn about [Custom Logic Nodes](./custom_logic_node.md)

