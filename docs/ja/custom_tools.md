# カスタムツール

エージェント用のカスタムツールの作成方法。

## 概要

ツールはノードが呼び出せる再利用可能な関数です。例：
- Web検索
- 計算機
- データベースクエリ
- API呼び出し
- ファイル操作

## クイックスタート

### 1. ツールの定義

```yaml
tools:
  - id: calculator
    type: calculator
    provider: openai          # 任意: プロバイダーを共有
    config:
      precision: 2
```

`provider` を指定すると、ツールファクトリーに解決済みのプロバイダーインスタンスが渡されます（`agent_ethan2/ir/model.py:291-303`）。

### 2. ファクトリーの実装

ツールファクトリーは `(state, inputs, ctx)` を受け取るコール可能オブジェクトを返す必要があります。Scheduler がグラフ状態と実行コンテキストを渡すためです（`agent_ethan2/registry/resolver.py:63-83`）。

#### 関数ベースのツールファクトリー

```python
def calculator_tool_factory(tool, provider_instance):
    """シンプルな計算ツールを作成。"""
    precision = tool.config.get("precision", 2)
    client = provider_instance["client"] if provider_instance else None

    async def call(state, inputs, ctx):
        operation = inputs.get("operation")
        operands = inputs.get("operands", [])

        if operation == "add":
            result = sum(operands)
        elif operation == "multiply":
            result = 1
            for value in operands:
                result *= value
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return {
            "result": round(result, precision),
            "operation": operation,
            "used_client": bool(client),
        }

    return call
```

#### クラスベースのツールファクトリー (推奨)

より複雑なツールや、状態を持つツールを定義する場合、クラスベースのファクトリーが推奨されます。`agent_ethan2.agent.Tool` を継承し、`call` メソッドを実装します。

```python
from agent_ethan2.agent import Tool
from pydantic import BaseModel, Field
from typing import List, Literal

# 入力スキーマの定義
class CalculatorInput(BaseModel):
    operation: Literal["add", "multiply"] = Field(..., description="実行する操作")
    operands: List[float] = Field(..., description="操作対象の数値リスト")

# 出力スキーマの定義
class CalculatorOutput(BaseModel):
    result: float = Field(..., description="計算結果")
    operation: str = Field(..., description="実行された操作")
    used_client: bool = Field(False, description="クライアントが使用されたか")

class CalculatorTool(Tool):
    def __init__(self, tool_config: dict, provider_instance: dict = None):
        super().__init__(tool_config, provider_instance)
        self.precision = tool_config.get("config", {}).get("precision", 2)
        self.client = provider_instance.get("client") if provider_instance else None

    async def call(self, state: dict, inputs: CalculatorInput, ctx: dict) -> CalculatorOutput:
        # Pydanticモデルでバリデーションされた入力を直接使用
        operation = inputs.operation
        operands = inputs.operands

        if operation == "add":
            result = sum(operands)
        elif operation == "multiply":
            result = 1
            for value in operands:
                result *= value
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return CalculatorOutput(
            result=round(result, self.precision),
            operation=operation,
            used_client=bool(self.client),
        )

# ファクトリー関数はクラスのインスタンスを返す
def calculator_tool_factory(tool, provider_instance):
    return CalculatorTool(tool, provider_instance)
```

### 3. ノードでの使用

```yaml
components:
  - id: calc_component
    type: tool
    tool: calculator
    inputs:
      operation: graph.inputs.op
      operands: graph.inputs.nums
    outputs:
      result: $.result
      operation: $.operation
```

対応するファクトリーを `runtime.factories.tools.calculator` に登録することを忘れないでください。

## 入力/出力スキーマの定義 (Pydantic)

ツールやカスタムノードの入力と出力には、Pydanticモデルを使用してスキーマを定義することを強く推奨します。これにより、以下の利点が得られます。

-   **自動バリデーション**: 入力データがスキーマに準拠しているか自動的にチェックされます。
-   **型ヒント**: コードの可読性と保守性が向上します。
-   **ドキュメント生成**: スキーマから自動的にドキュメントを生成できます。

上記のクラスベースのツールファクトリーの例では、`CalculatorInput` と `CalculatorOutput` というPydanticモデルを使用して、ツールの入力と出力の構造を定義しています。

## サンプル

### Web検索ツール

```python
import aiohttp
from pydantic import BaseModel, Field
from typing import List, Dict, Any

class SearchInput(BaseModel):
    query: str = Field(..., description="検索クエリ")
    max_results: int = Field(5, description="最大検索結果数")

class SearchResultItem(BaseModel):
    title: str
    url: str
    snippet: str

class SearchOutput(BaseModel):
    results: List[SearchResultItem]
    count: int

class SearchTool(Tool):
    def __init__(self, tool_config: dict, provider_instance: dict = None):
        super().__init__(tool_config, provider_instance)
        self.api_key = tool_config.get("config", {}).get("api_key")

    async def call(self, state: dict, inputs: SearchInput, ctx: dict) -> SearchOutput:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.search.com/search?q={inputs.query}&limit={inputs.max_results}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with session.get(url, headers=headers) as response:
                data = await response.json()
        
        results = [SearchResultItem(**item) for item in data.get("results", [])]
        return SearchOutput(results=results, count=len(results))

def search_tool_factory(tool, provider_instance):
    return SearchTool(tool, provider_instance)
```

### データベースツール

```python
import asyncpg
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DBInput(BaseModel):
    sql: str = Field(..., description="実行するSQLクエリ")
    params: Optional[List[Any]] = Field(None, description="SQLクエリのパラメータ")

class DBOutput(BaseModel):
    rows: List[Dict[str, Any]]
    count: int

class DBTool(Tool):
    def __init__(self, tool_config: dict, provider_instance: dict = None):
        super().__init__(tool_config, provider_instance)
        self.connection_string = tool_config.get("config", {}).get("connection_string")

    async def call(self, state: dict, inputs: DBInput, ctx: dict) -> DBOutput:
        async with asyncpg.connect(self.connection_string) as conn:
            rows = await conn.fetch(inputs.sql, *(inputs.params or []))
        
        return DBOutput(rows=[dict(row) for row in rows], count=len(rows))

def db_tool_factory(tool, provider_instance):
    return DBTool(tool, provider_instance)
```

## 参照

- [LangChainツール](./using_langchain_tools.md)
- [カスタムロジックノード](./custom_logic_node.md)
- [サンプル](./examples.md)