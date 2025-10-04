# AgentEthan2 Documentation

Welcome to the AgentEthan2 documentation! This guide will help you build AI agents using YAML configuration.

## Table of Contents

### Getting Started
- [Setup Guide](./setup.md) - Installation, configuration, and first steps
- [Quick Start](../README.md#quick-start) - Get running in 5 minutes

### Core Concepts
- [Nodes](./nodes.md) - Understanding the building blocks of your agent
- [YAML Definition Reference](./yaml_reference.md) - Complete specification of all YAML keys
- [Providers](./providers.md) - Configuring LLM providers (OpenAI, local models, etc.)
- [Providers (Advanced)](./providers-advanced.md) - Building custom provider factories and overrides
- [Custom Logic Nodes](./custom_logic_node.md) - Creating custom components
- [Runtime Configuration](./runtime-config.md) - Engine, factories, and exporters configuration
- [JSONPath Output Extraction](./jsonpath-outputs.md) - Extracting values from component outputs

### API & Architecture
- [Facade API](./facade-api.md) - High-level AgentEthan class usage
- [Workflow](./workflow.md) - MVP pipeline from YAML to execution
- [Events](./events.md) - Event reference for telemetry
- [Error Codes](./errors.md) - Complete error code reference

### Features
- [Chat History](./chat_history.md) - Multi-turn conversation management
- [Logging & Telemetry](./logging.md) - Monitoring and debugging your agents
- [Hook Methods](./hook_methods.md) - Lifecycle hooks for fine-grained control
- [Async Execution](./async_execution.md) - Understanding async/await patterns

### Policies & Security
- [Policies](./policies.md) - Retry, rate limiting, masking, permissions, and cost management
- [Security Guide](./security.md) - Best practices for secure agent development

### Integrations
- [Custom Tools](./custom_tools.md) - Creating and using custom tools
- [LangChain Tools](./using_langchain_tools.md) - Integrating LangChain ecosystem
- [MCP Integration](./using_mcp.md) - Model Context Protocol support

### Learning
- [Examples](./examples.md) - Walkthrough of included examples
- [Troubleshooting](./troubleshooting.md) - Common issues and solutions
- [Troubleshoot](./troubleshoot.md) - Quick reference for common errors

## What is AgentEthan2?

AgentEthan2 is a **declarative agent framework** that separates workflow definition from implementation. You define your agent's behavior in YAML, and implement the business logic in Python.

### Key Benefits

1. **Declarative** - Define workflows in YAML, not code
2. **Testable** - Easy to test and modify workflows
3. **Maintainable** - Clear separation of concerns
4. **Extensible** - Plugin architecture for custom logic
5. **Production-Ready** - Built-in retry, rate limiting, logging

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           YAML Configuration            │
│  (meta, runtime, providers, components) │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│          Normalization & IR             │
│    (Convert YAML to internal model)     │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           Registry & Resolver           │
│   (Load factories, create instances)    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           Graph Builder                 │
│    (Build executable graph)             │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│           Scheduler & Runtime           │
│  (Execute nodes, manage state, events)  │
└─────────────────────────────────────────┘
```

## Quick Links

- **[Setup Guide](./setup.md)** - Start here
- **[YAML Reference](./yaml_reference.md)** - Complete spec
- **[Examples](./examples.md)** - Learn by example
- **[Troubleshooting](./troubleshooting.md)** - Get help

## Need Help?

- Check the [Troubleshooting Guide](./troubleshooting.md)
- Review the [Examples](./examples.md)
- Read the [YAML Reference](./yaml_reference.md)

## Next Steps

1. Follow the [Setup Guide](./setup.md) to install AgentEthan2
2. Try the [Quick Start](../README.md#quick-start) example
3. Explore the [Examples](./examples.md) directory
4. Build your first agent!
