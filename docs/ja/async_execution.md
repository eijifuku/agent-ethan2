# 非同期実行

AgentEthan2における async/await の理解。

## 概要

AgentEthan2は効率的な並行実行のために asyncio をベースに構築されています。

## 主要な概念

### 非同期ノード

すべてのノードは非同期である必要があります：

```python
async def my_component(state, inputs, ctx):
    # Your async code
    result = await some_async_call()
    return {"result": result}
```

### 結果の待機

非同期呼び出しには必ず `await` を使用してください：

```python
# 正しい
result = await client.chat.completions.create(...)

# 間違い
result = client.chat.completions.create(...)  # coroutineを返す
```

## 並列実行

並行実行には `parallel` ノードタイプを使用します：

```yaml
graph:
  nodes:
    - id: parallel_step
      type: parallel
      next: [task1, task2, task3]  # すべて同時に実行される
```

## エージェントの実行

### 同期API

```python
agent = AgentEthan("config.yaml")
result = agent.run_sync({"input": "..."})
```

### 非同期API

```python
agent = AgentEthan("config.yaml")
result = await agent.run({"input": "..."})
```

## ベストプラクティス

1. **ノードでは常に async/await を使用する**
2. **独立したタスクには parallel ノードを使用する**
3. **イベントループをブロックしない** - 非同期ライブラリを使用する
4. **タイムアウトを処理する** - asyncio.timeout を使用

## サンプル

非同期パターンについてはすべてのサンプルを参照してください。
