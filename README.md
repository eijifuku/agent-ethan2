# AgentEthan2

A flexible, YAML-based agent framework for building AI workflows with LLMs, tools, and custom logic.

[日本語版 README](./README.ja.md)

## Overview

AgentEthan2 is a declarative agent framework that allows you to define complex AI workflows using YAML configuration. It provides a clean separation between workflow definition and implementation, making it easy to build, test, and maintain AI agents.

## Features

- **📝 YAML-First Design** - Define your entire agent workflow in YAML
- **🔄 Multiple Node Types** - LLM, Tool, Router, Map/Parallel, Custom components
- **💬 Conversation History** - Built-in multi-turn conversation support with pluggable backends (Memory, Redis)
- **🔧 Lifecycle Hooks** - `before_execute`, `after_execute`, `on_error` hooks for fine-grained control
- **🔁 Retry & Rate Limiting** - Built-in policies for resilient execution
- **📊 Telemetry & Logging** - Multiple exporters (JSONL, Console, LangSmith, Prometheus)
- **🧩 Extensible** - Easy to add custom providers, tools, and components
- **⚡ Async-First** - Built on asyncio for efficient execution
- **🔌 Tool Integration** - Support for LangChain tools and custom tools
- **🌐 OpenAI-Compatible** - Works with OpenAI API and compatible local LLMs (Ollama, etc.)

## Requirements

- Python 3.10+
- pip or uv

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd agent-ethan2

# Install dependencies
pip install -e .

# For development
pip install -e ".[dev]"
```

## Quick Start

### 1. Define Your Agent in YAML

Create `config.yaml`:

```yaml
meta:
  version: 2
  name: simple-agent
  description: A simple LLM agent

runtime:
  engine: lc.lcel
  graph_name: simple_run
  factories:
    providers:
      openai: my_agent.factories.provider_factory
    components:
      llm: my_agent.factories.llm_factory
  exporters:
    - type: jsonl
      path: run.jsonl

providers:
  - id: openai
    type: openai
    config:
      model: gpt-4o-mini

components:
  - id: assistant
    type: llm
    provider: openai
    inputs:
      prompt: graph.inputs.user_message
    outputs:
      response: $.choices[0].text

graph:
  entry: ask
  nodes:
    - id: ask
      type: llm
      component: assistant
  outputs:
    - key: final_response
      node: ask
      output: response
```

### 2. Run Your Agent

Create `run.py`:

```python
from agent_ethan2.agent import AgentEthan

# Initialize agent
agent = AgentEthan("config.yaml")

# Run
result = agent.run_sync({
    "user_message": "Hello! What can you help me with?"
})

print(result.outputs["final_response"])
```

```bash
export OPENAI_API_KEY=your-api-key
python run.py
```

## Super Quick Start

We've published an [AgentEthan2 specification MCP for AI code editors](https://github.com/eijifuku/agent-ethan-guide-mcp).  
Set up this MCP and describe the agent specification you want to create to AI.

## Documentation

- **[English Documentation](./docs/en/index.md)** - Complete guide in English
- **[日本語ドキュメント](./docs/ja/index.md)** - 日本語の完全ガイド

### Core Concepts

- [Setup Guide](./docs/en/setup.md) - Installation and configuration
- [Nodes](./docs/en/nodes.md) - Understanding node types
- [YAML Reference](./docs/en/yaml_reference.md) - Complete YAML specification
- [Providers](./docs/en/providers.md) - Configuring LLM providers
- [Chat History](./docs/en/chat_history.md) - Multi-turn conversations
- [Logging](./docs/en/logging.md) - Telemetry and monitoring

### Advanced Topics

- [Custom Logic Nodes](./docs/en/custom_logic_node.md) - Building custom components
- [Custom Tools](./docs/en/custom_tools.md) - Creating tools
- [LangChain Tools](./docs/en/using_langchain_tools.md) - Using LangChain tools
- [MCP Integration](./docs/en/using_mcp.md) - Model Context Protocol
- [Async Execution](./docs/en/async_execution.md) - Async/await patterns
- [Hook Methods](./docs/en/hook_methods.md) - Lifecycle hooks
- [Examples](./docs/en/examples.md) - Sample implementations
- [Troubleshooting](./docs/en/troubleshooting.md) - Common issues

## Custom Factories

For advanced use cases requiring custom providers, components, or tools, see:

- [Advanced Providers](./docs/en/providers-advanced.md) - Custom provider factories
- [Custom Tools](./docs/en/custom_tools.md) - Custom tool implementations  
- [Custom Logic Nodes](./docs/en/custom_logic_node.md) - Custom component logic
- [Runtime Configuration](./docs/en/runtime-config.md) - Factory registration

## Examples

The [examples](./examples/) directory contains working examples:

- `01_basic_llm` - Simple LLM call
- `02_llm_with_tool` - LLM with tool integration
- `03_router` - Conditional routing
- `04_map_parallel` - Parallel execution
- `05_retry_ratelimit` - Retry and rate limiting
- `06_component` - Custom components
- `07_full_agent` - Complete agent example
- `08_telemetry_exporters` - Logging/telemetry
- `09_hooks` - Lifecycle hooks
- `10_conversation_history` - Multi-turn conversations

## License

MIT License

Copyright (c) 2025 AgentEthan2

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
