**Title**: [Z1] Examples（実行可能なYAML例とREADME）

**Goal / 背景**
- AgentEthan2の機能を実証する実行可能なYAML例を作成し、新規ユーザーが機能を理解・試用できるようにする。
- モックではなく実際のLLM/ツールを使用し、実用的な動作を確認できるようにする。

**Scope / I/O**
- 入力: 実装済みのagent_ethan2コード、YAMLスキーマv2、仕様書
- 出力: examples/配下のYAMLファイル群、examples/README.md、実行スクリプト、必要なツール実装

**Specs**

## 作成するExample一覧

各Exampleは独立したサブディレクトリに配置し、以下を含む:
- `config.yaml`: YAML設定ファイル
- `README.md`: Exampleの説明、実行方法、カスタマイズ方法
- `components/`: Example固有のツール・コンポーネント（必要に応じて）

### 1. examples/01_basic_llm/
- **目的**: 最小構成のLLM呼び出し
- **内容**:
  - 単一のLLMノードによるシンプルな応答生成
  - 実際のLLMプロバイダ設定（OpenAI/Anthropic等、環境変数で切り替え可能）
  - 基本的なプロンプトテンプレート
  - entry/endノードの基本構成
- **ファイル**:
  - `config.yaml`
  - `README.md`

### 2. examples/02_llm_with_tool/
- **目的**: LLM + Tool連携
- **内容**:
  - LLMがToolを呼び出して結果を利用
  - 実際に動作するTool定義（例: calculator, file_read等）
  - LLMからToolへの遷移
  - Toolの出力をLLMに返す
- **ファイル**:
  - `config.yaml`
  - `README.md`
  - `components/tools.py`: calculator, file_read等のツール実装

### 3. examples/03_router/
- **目的**: Router機能のデモ
- **内容**:
  - 条件分岐によるノード選択
  - 複数ルート（例: ユーザー入力の種類に応じた処理分岐）
  - default経路の設定
  - Router評価式の例
- **ファイル**:
  - `config.yaml`
  - `README.md`

### 4. examples/04_map_parallel/
- **目的**: Map/Parallel実行のデモ
- **内容**:
  - 配列要素に対するMap処理
  - Parallel実行による複数ノードの並行処理
  - namespace設定による出力のマージ
  - 結果の集約
- **ファイル**:
  - `config.yaml`
  - `README.md`

### 5. examples/05_retry_ratelimit/
- **目的**: エラーハンドリングとポリシー
- **内容**:
  - Retry policy（再試行設定）
  - Rate limit設定
  - エラー発生時の挙動
  - バックオフ戦略
- **ファイル**:
  - `config.yaml`
  - `README.md`

### 6. examples/06_component/
- **目的**: Component（カスタムロジック）の利用
- **内容**:
  - Python関数をComponentとして登録
  - 入力/出力の定義
  - LLMとComponentの連携
- **ファイル**:
  - `config.yaml`
  - `README.md`
  - `components/custom.py`: カスタムコンポーネント実装

### 7. examples/07_full_agent/
- **目的**: 統合的なエージェント例
- **内容**:
  - 上記機能を組み合わせた実用的なエージェント
  - LLM → Tool → Router → Component の複合フロー
  - エラーハンドリング、テレメトリ設定
  - 実際のユースケース（例: Q&Aエージェント、タスク自動化等）
- **ファイル**:
  - `config.yaml`
  - `README.md`
  - `components/`: 必要なツール・コンポーネント

## examples/README.md（トップレベル）

以下を含むREADMEを作成:

1. **概要**: AgentEthan2のExamples集の説明
2. **前提条件**: 
   - Python 3.10+
   - 依存パッケージのインストール（langchain, openai, anthropic等）
   - LLM APIキーの設定（環境変数）
   - Docker環境（推奨）
3. **環境変数設定**:
   ```bash
   export OPENAI_API_KEY="your-key"
   # または
   export ANTHROPIC_API_KEY="your-key"
   ```
4. **Examples一覧**: 
   - ディレクトリ名、目的、学べる機能、必要なAPIキー
   - 各Exampleへのリンク
5. **基本的な実行方法**:
   ```bash
   # コンテナ内で実行
   cd examples/01_basic_llm
   python -m agent_ethan2.cli config.yaml
   
   # またはスクリプト経由
   python examples/run_example.py 01_basic_llm
   ```
6. **カスタマイズ方法**: 
   - プロバイダの変更（OpenAI ⇔ Anthropic等）
   - モデルの変更（gpt-4, claude-3等）
   - プロンプトの調整
   - ノードの追加・削除
7. **トラブルシューティング**: よくあるエラーと対処法（APIキーエラー、レート制限等）

## 各Example配下のREADME.md

各Example（01_basic_llm等）のREADME.mdには以下を含む:

1. **タイトルと目的**: このExampleで学べること
2. **機能**: 使用している機能の説明
3. **ファイル構成**: config.yaml、components/等の説明
4. **実行方法**:
   ```bash
   cd examples/01_basic_llm
   python -m agent_ethan2.cli config.yaml
   ```
5. **設定の説明**: config.yamlの主要セクションの解説
6. **カスタマイズ例**: プロンプト変更、モデル変更等の具体例
7. **期待される出力**: 実行結果のサンプル

## examples/run_example.py

実行補助スクリプト:
- Example名（ディレクトリ名）を引数に取り、対応するconfig.yamlを実行
- 使用例: `python examples/run_example.py 01_basic_llm`
- テレメトリをコンソール/ファイルに出力
- 実行結果をわかりやすく表示
- デバッグモード対応（`--debug`フラグ）
- Example一覧表示（`--list`フラグ）

## 共通ツール・コンポーネント

examples/shared_components/ 配下に共通ツールを配置:
- `__init__.py`
- `tools.py`: 複数のExampleで使用可能なツール実装
  - calculator: 数式計算
  - file_operations: ファイル読み書き
  - datetime_tool: 日時取得

各Example固有のコンポーネントは各Example配下のcomponents/に配置

## YAML共通要件

全てのYAMLは以下を満たす:
- スキーマv2準拠
- YamlLoaderV2でバリデーション成功
- コメントによる説明付き（日本語・英語併記推奨）
- 実際のLLM/ツールで実行可能
- 適切なAPIキーがあればエラーなく完了する
- プロバイダは環境変数で切り替え可能な設計

**Error Codes / Warnings**
- （Exampleファイル自体はエラーを起こさない設計）

**Events**
- 各Exampleの実行でイベントが適切に発火されることを確認

**Dependencies**
- 全モジュール（A1〜F2）
- docs/workflow.md

**Acceptance (DoD)**
- 全てのYAMLファイルが文法的に正しい（YamlLoaderV2成功）
- 全てのExampleが実際のLLM/ツールで実行完了する
- examples/README.mdが完備（環境変数設定含む）
- run_example.pyが動作
- examples/components/のツールが実際に機能する
- 新規ユーザーがREADMEを読んでAPIキー設定後10分以内に最初のExampleを実行できる

**Tests**
- 正常系: 
  - 各YAMLファイルのロード成功
  - 各Exampleの実行完了（実LLM環境、CI時はAPIキーモック化も検討）
  - run_example.pyの動作確認
  - ツールの単体動作確認
- 異常系:
  - 存在しないExample名でのエラーハンドリング
  - APIキー未設定時の適切なエラーメッセージ

**Size**: L

---

## 実装ガイドライン

### YAMLファイル構造
```yaml
meta:
  version: 2
  name: "Example Name"
  description: "What this example demonstrates"

runtime:
  engine: "langchain"
  graph_name: "main"

providers:
  - id: main_llm
    type: openai  # または anthropic, azure等
    config:
      model: gpt-4  # 実際のモデル名
      temperature: 0.7

# tools, components, graph等は各Exampleの目的に応じて定義
```

### コメント規約
- 各セクションに日本語/英語の説明コメント
- 重要な設定項目には補足説明（APIキー、モデル選択等）
- 初心者が理解しやすい表現
- プロバイダ/モデルの切り替え方法を明記

### 実装の方針
- 実際のLLM APIを使用（OpenAI, Anthropic等）
- ツールは実際に機能する実装（calculator, file操作, web検索等）
- 環境変数でAPIキーを管理
- エラーハンドリングを適切に実装
- プロバイダ切り替えのための設定例をコメントで併記

### ファイル配置
```
examples/
├── README.md                    # トップレベルREADME（全体の説明）
├── .env.example                 # 環境変数テンプレート
├── run_example.py               # 実行補助スクリプト
├── shared_components/           # 複数Exampleで共有するツール
│   ├── __init__.py
│   └── tools.py                 # calculator, file_operations等
├── 01_basic_llm/
│   ├── config.yaml              # YAML設定ファイル
│   └── README.md                # このExampleの説明
├── 02_llm_with_tool/
│   ├── config.yaml
│   ├── README.md
│   └── components/              # Example固有のツール
│       ├── __init__.py
│       └── tools.py
├── 03_router/
│   ├── config.yaml
│   └── README.md
├── 04_map_parallel/
│   ├── config.yaml
│   └── README.md
├── 05_retry_ratelimit/
│   ├── config.yaml
│   └── README.md
├── 06_component/
│   ├── config.yaml
│   ├── README.md
│   └── components/
│       ├── __init__.py
│       └── custom.py            # カスタムコンポーネント
└── 07_full_agent/
    ├── config.yaml
    ├── README.md
    └── components/
        ├── __init__.py
        ├── tools.py
        └── custom.py
```

### 追加要件
- 各Exampleディレクトリは独立して実行可能
- 共有ツールは`shared_components/`に配置し、各Exampleから参照
- `.env.example`に必要な環境変数のテンプレートを記載
- README.md（トップレベル）に各プロバイダの設定方法を詳述
- 各ExampleのREADME.mdにそのExampleの詳細な説明を記載
- ツール実装は依存パッケージを最小限に（標準ライブラリ優先、requests等必要最低限）

