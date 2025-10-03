# LangChainツールの使用

AgentEthan2とLangChainツールの統合方法。

## 概要

LangChainは豊富なツールエコシステムを提供しています。アダプターファクトリーを作成することで、AgentEthan2で使用できます。

## 基本的な統合

### 1. LangChainツールのインストール

```bash
pip install langchain-community
```

### 2. アダプターファクトリーの作成

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

### 3. YAMLに登録

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

## 一般的なLangChainツール

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

## 参照

- [カスタムツール](./custom_tools.md)
- [サンプル](./examples.md)
