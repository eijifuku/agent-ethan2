# Using LangChain Tools

Integrate LangChain tools with AgentEthan2.

## Overview

LangChain provides a rich ecosystem of tools. You can use them in AgentEthan2 by creating adapter factories.

## Basic Integration

### 1. Install LangChain Tools

```bash
pip install langchain-community
```

### 2. Create Adapter Factory

```python
from langchain_community.tools import DuckDuckGoSearchRun

def langchain_search_factory(tool, provider_instance):
    """Adapter for LangChain DuckDuckGo search."""
    search_tool = DuckDuckGoSearchRun()
    
    async def search(query):
        # LangChain tools are sync, run in executor
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, search_tool.run, query)
        
        return {"results": result}
    
    return search
```

### 3. Register in YAML

```yaml
runtime:
  factories:
    tools:
      web_search: my_agent.tools.langchain_search_factory

tools:
  - id: search
    type: web_search

components:
  - id: searcher
    type: tool
    tool: search
    outputs:
      results: $.results
```

## Common LangChain Tools

### Wikipedia

```python
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

def wikipedia_factory(tool, provider_instance):
    api_wrapper = WikipediaAPIWrapper()
    wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)
    
    async def search(query):
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, wiki_tool.run, query)
        return {"content": result}
    
    return search
```

### Python REPL

```python
from langchain_community.tools import PythonREPLTool

def python_repl_factory(tool, provider_instance):
    repl = PythonREPLTool()
    
    async def execute(code):
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, repl.run, code)
        return {"output": result}
    
    return execute
```

## See Also

- [Custom Tools](./custom_tools.md)
- [Examples](./examples.md)




