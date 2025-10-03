# Setup Guide

Get AgentEthan2 up and running on your system.

## Prerequisites

- **Python 3.10 or higher**
- **pip** or **uv** package manager
- **Git** (for cloning the repository)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd agent-ethan2
```

### 2. Install Dependencies

**Using pip**:
```bash
# Install in editable mode
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

**Using uv** (faster):
```bash
uv pip install -e .
```

### 3. Verify Installation

```bash
python -c "import agent_ethan2; print('Installation successful!')"
```

## Docker Setup (Optional)

For isolated development environment:

```bash
# Start development container
docker-compose --profile dev up -d agent-ethan2-dev

# Enter container
docker-compose exec agent-ethan2-dev bash

# Inside container
pip install -e ".[dev]"
pytest
```

## Environment Variables

Set up required environment variables:

```bash
# OpenAI API (required for most examples)
export OPENAI_API_KEY=your-api-key-here

# Optional: for other providers
export ANTHROPIC_API_KEY=your-anthropic-key
export TAVILY_API_KEY=your-tavily-key

# Optional: for LangSmith telemetry
export LANGSMITH_API_KEY=your-langsmith-key
export LANGSMITH_PROJECT=my-agent-project
```

**Recommended**: Create a `.env` file:

```bash
# .env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=agent-ethan2
```

Load it in your code:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Project Structure

```
agent-ethan2/
├── agent_ethan2/          # Core framework
│   ├── graph/             # Graph building
│   ├── ir/                # Intermediate representation
│   ├── loader/            # YAML loading
│   ├── policy/            # Retry, rate limiting
│   ├── registry/          # Component registry
│   ├── runtime/           # Execution runtime
│   ├── telemetry/         # Logging & monitoring
│   └── validation/        # Input validation
├── examples/              # Working examples
├── tests/                 # Unit tests
├── docs/                  # Documentation
├── schemas/               # YAML schema
└── pyproject.toml         # Project config
```

## Running Examples

```bash
cd examples/01_basic_llm
export OPENAI_API_KEY=your-key
python run.py
```

## Development Setup

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `mypy` - Type checking
- `ruff` - Linting

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=agent_ethan2

# Specific test file
pytest tests/test_runtime_scheduler.py

# Specific test
pytest tests/test_runtime_scheduler.py::test_simple_llm_node
```

### Type Checking

```bash
mypy agent_ethan2
```

### Linting

```bash
# Check
ruff check agent_ethan2

# Auto-fix
ruff check --fix agent_ethan2
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- YAML

`.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true,
  "python.formatting.provider": "black"
}
```

### PyCharm

1. Mark `agent_ethan2` as Sources Root
2. Enable pytest as test runner
3. Configure mypy external tool

## Troubleshooting

### Import Error

```
ModuleNotFoundError: No module named 'agent_ethan2'
```

**Solution**: Install in editable mode:
```bash
pip install -e .
```

### OpenAI API Error

```
openai.AuthenticationError: No API key provided
```

**Solution**: Set the `OPENAI_API_KEY` environment variable before running examples:
```bash
export OPENAI_API_KEY=your-key
```

### YAML Validation Error

```
YamlValidationError: 'meta' is a required property
```

**Solution**: Check YAML structure matches [schema](./yaml_reference.md)

## Next Steps

- Read the [YAML Reference](./yaml_reference.md)
- Try [Examples](./examples.md)
- Learn about [Nodes](./nodes.md)
