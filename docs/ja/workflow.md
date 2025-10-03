# ワークフロー

AgentEthan2におけるワークフローは、エージェントの動作を定義する一連のノードとそれらの接続です。YAMLファイルで宣言的に定義され、AgentEthan2ランタイムによって実行されます。

## ワークフローのライフサイクル

AgentEthan2のワークフローは、以下の主要なステップを経て実行されます。

1.  **定義 (YAML)**:
    -   ユーザーはYAMLファイルを使用して、エージェントのメタデータ、プロバイダ、コンポーネント、そして実行グラフ（ノードとその接続）を定義します。
    -   これはエージェントの「設計図」となります。

2.  **構築 (Graph Builder)**:
    -   AgentEthan2ランタイムは、定義されたYAMLファイルを読み込み、内部的なグラフ構造に変換します。
    -   この段階で、ノード間の依存関係が解決され、実行可能なグラフが構築されます。

3.  **実行 (Scheduler & Runtime)**:
    -   構築されたグラフは、スケジューラによって実行されます。
    -   スケジューラはノードの依存関係に基づいて実行順序を決定し、各ノードを非同期的に実行します。
    -   ノードの実行中、状態管理、イベント発行、ポリシー適用などが行われます。

## ワークフローの概念

ワークフローは、データがノード間をどのように流れるかを示す有向非巡回グラフ（DAG）として考えることができます。各ノードは特定のタスク（LLM呼び出し、ツール実行、カスタムロジックなど）を実行し、その結果を次のノードに渡します。

### データの流れ

-   **入力**: ワークフロー全体への入力は `graph.inputs` を通じてアクセスできます。
-   **ノード出力**: 各ノードの出力は、他のノードの入力として参照できます（例: `node.node_id.output_key`）。
-   **状態**: ワークフロー全体で共有される状態オブジェクトがあり、ノード間でデータを永続化するために使用できます。

## 高度な実行フロー

AgentEthan2は、基本的なシーケンシャルな実行だけでなく、より複雑なワークフローパターンをサポートしています。

### Mapノード

`map` ノードは、コレクション（リストなど）の各アイテムに対して、指定されたサブワークフロー（または単一ノード）を並行して実行するために使用されます。これは、データ処理のバッチ処理や、複数の独立したタスクを同時に処理する場合に非常に便利です。

**ユースケース**:
-   ユーザーが提供した複数の質問に対して、それぞれLLMを呼び出す。
-   複数のドキュメントを並行して要約する。

**例**:
```yaml
graph:
  nodes:
    - id: process_items
      type: map
      component: item_processor # 各アイテムを処理するコンポーネント
      config:
        collection: graph.inputs.items # 処理対象のコレクション
        result_key: processed_results  # 結果を格納するキー
```
詳細については、[サンプル集の04_map_parallel](../examples/04_map_parallel/README.md)を参照してください。

### Parallelノード

`parallel` ノードは、複数のノードを同時に実行するために使用されます。これらのノードは互いに依存せず、並行して実行を完了します。すべての並行ノードが完了すると、ワークフローは次のステップに進みます。

**ユースケース**:
-   複数の情報源からデータを同時に取得する。
-   異なるLLMモデルに同じプロンプトを送り、結果を比較する。

**例**:
```yaml
graph:
  nodes:
    - id: parallel_tasks
      type: parallel
      next: [fetch_data_a, fetch_data_b, analyze_data] # これら3つのノードが並行して実行される
    - id: fetch_data_a
      type: tool
      component: data_fetcher_a
      next: merge_results
    - id: fetch_data_b
      type: tool
      component: data_fetcher_b
      next: merge_results
    - id: analyze_data
      type: llm
      component: analyzer
      next: merge_results
    - id: merge_results
      type: custom_logic
      component: result_merger
```
詳細については、[サンプル集の04_map_parallel](../examples/04_map_parallel/README.md)を参照してください。

---

## 次のステップ

-   [ノード](./nodes.md)についてさらに深く学ぶ
-   [YAML定義リファレンス](./yaml_reference.md)で完全な仕様を確認する
-   [サンプル集](./examples.md)で実際のワークフロー例を見る