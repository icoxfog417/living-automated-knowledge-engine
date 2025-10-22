# Metadata Generator for LAKE

S3 にアップロードされたファイルから自動的にメタデータを生成する Lambda 関数です。

## アーキテクチャ

```
EventBridge (S3 Object Created)
  ↓
Lambda Handler (handler.py)
  ↓
EventParser (event_parser.py) - イベント解析
  ↓
MetadataGenerator (metadata_generator.py)
  ├─ RuleMatcher (rule_matcher.py) - ルール特定
  ├─ PromptBuilder (prompt_builder.py) - プロンプト生成
  ├─ BedrockClient (bedrock_client.py)
  │   └─ JsonExtractor (json_extractor.py) - JSON抽出
  └─ S3Operations (s3_operations.py) - ファイル読み書き
  ↓
{file}.metadata.json が S3 に保存される
```

## ディレクトリ構造

```
src/
├── handler.py              # Lambda ハンドラー
├── core/                   # コアロジック
│   ├── schema.py          # データモデル
│   ├── config_loader.py   # 設定ファイル読み込み
│   └── metadata_generator.py  # メタデータ生成オーケストレーション
├── services/              # ビジネスロジック
│   ├── event_parser.py    # EventBridgeイベント解析
│   ├── rule_matcher.py    # ファイルパターンマッチング
│   ├── prompt_builder.py  # JSON SchemaからAIプロンプト生成
│   └── json_extractor.py  # Bedrock応答からJSON抽出
├── clients/               # 外部サービスクライアント
│   ├── s3_operations.py   # S3 操作
│   └── bedrock_client.py  # Bedrock API
└── config/
    └── config.yaml        # メタデータルール定義
```

## 主要コンポーネント

### 1. コアロジック (`core/`)

#### `schema.py` - データモデル

- `FileInfo`: S3 ファイル情報（bucket, key, content）
- `MetadataRule`: メタデータ生成ルール（pattern, schema）
- `Config`: アプリケーション設定
- `GeneratedMetadata`: 生成結果

#### `config_loader.py` - 設定読み込み

- YAML ファイルから設定を読み込み、バリデーション

#### `metadata_generator.py` - メタデータ生成オーケストレーション

- 各サービスを統合してメタデータ生成プロセスを管理

### 2. ビジネスロジック (`services/`)

#### `event_parser.py` - イベント解析

- EventBridge から受け取る S3 イベントを解析
- ファイル情報（bucket, key）を抽出

#### `rule_matcher.py` - ルールマッチング

- ファイルパスに合致するメタデータルールを検索
- `pathlib.PurePosixPath.match()`を使用したパターンマッチング

#### `prompt_builder.py` - プロンプト生成

- JSON Schema から自然言語プロンプトを自動生成
- ファイル内容とスキーマを組み合わせて AI 用のプロンプトを作成

#### `json_extractor.py` - JSON 抽出

- Bedrock の応答から JSON を抽出・パース
- マークダウンコードブロック内の JSON を検出

### 3. 外部サービスクライアント (`clients/`)

#### `bedrock_client.py` - Bedrock API

- AWS Bedrock との通信
- Converse API を使用したメタデータ生成
- 構造化出力（Structured Output）のサポート

#### `s3_operations.py` - S3 操作

- S3 からのファイル読み込み
- メタデータファイルの保存

### 4. 設定ファイル (`config/config.yaml`)

ファイルパターンごとに JSON Schema を定義:

```yaml
rules:
  file_patterns:
    - pattern: "/**/*.pdf"
      schema:
        type: "object"
        properties:
          department:
            type: "string"
            description: "部署名"
        required: ["department"]
```

### 5. メタデータ生成フロー

1. **ファイル読み込み**: S3 からファイル内容を取得
2. **ルール特定**: ファイルパスに合致するルールを検索
3. **プロンプト生成**: JSON Schema からプロンプトを自動生成
4. **AI 生成**: Bedrock でメタデータ生成
5. **バリデーション**: JSON Schema で検証
6. **保存**: `.metadata.json`として S3 に保存

## Lambda Handler との分離

各モジュールは独立しており、Lambda Handler に依存していません:

- `MetadataGenerator`: ファイル情報を受け取り、メタデータを返す
- `BedrockClient`: プロンプトを受け取り、JSON を返す
- `S3Operations`: bucket/key を受け取り、ファイル内容を返す

## メタデータファイルの命名規則

元のファイルに `.metadata.json` サフィックスを追加:

```
docs/report.pdf
  → docs/report.pdf.metadata.json

reports/2024Q1.csv
  → reports/2024Q1.csv.metadata.json
```

## 設定のカスタマイズ

`src/config/config.yaml`を編集して、新しいファイルパターンやメタデータフィールドを追加できます:

```yaml
rules:
  file_patterns:
    - pattern: "custom/**/*.xml"
      schema:
        type: "object"
        properties:
          custom_field:
            type: "string"
            description: "カスタムフィールド"
        required: ["custom_field"]
```

## Bedrock 設定

`config.yaml` の `bedrock` セクションでは、AI モデルの動作を制御するパラメータを設定できます。

### 設定パラメータ

```yaml
bedrock:
  model_id: "global.anthropic.claude-haiku-4-5-20251001-v1:0"
  max_tokens: 640000
  input_context_window: 200000
  temperature: 0.1
```

#### `model_id`

使用する Bedrock モデルの ID を指定します。

- **例**: `global.anthropic.claude-haiku-4-5-20251001-v1:0`
- **デフォルト**: `global.anthropic.claude-haiku-4-5-20251001-v1:0`

#### `max_tokens`

モデルが生成する**出力**の最大トークン数を指定します。

#### `input_context_window`

モデルが読み込める**入力**の最大トークン数を指定します。このパラメータは、ファイル内容をどれだけプロンプトに含めるかを決定します。

#### `temperature`

生成の多様性を制御するパラメータです。

### input_context_window による影響

このパラメータは、ファイル内容をプロンプトに含める際の文字数制限に直接影響します：

| input_context_window  | 最大文字数（概算） | 用途                                    |
| --------------------- | ------------------ | --------------------------------------- |
| 100,000（デフォルト） | 約 232,800 文字    | 一般的なドキュメント                    |
| 200,000               | 約 472,800 文字    | 大規模ドキュメント（Claude 3/3.5 推奨） |
| 50,000                | 約 112,800 文字    | 短いドキュメント、コスト削減            |

**注意**:

- 非常に大きなファイルの場合、この制限を超える部分は切り捨てられ、"... (truncated)" メッセージが追加されます
- `input_context_window` を未指定の場合、デフォルト値（100,000 トークン）が使用されます
- モデルの実際のコンテキストウィンドウサイズを超える値を設定しないでください

## パターンマッチングの制約と注意事項

本システムは Python の `pathlib.PurePosixPath.match()` を使用してファイルパターンマッチングを行います。この動作には以下の特徴と制約があります。

### 1. 部分マッチの動作

**重要**: パターンはパスの**末尾部分**とマッチします。

```yaml
# この設定の場合...
- pattern: "*.txt"
  schema: ...
# 以下のすべてにマッチします：
# ✓ report.txt          （ルートレベル）
# ✓ docs/report.txt     （1階層下）
# ✓ deep/path/file.txt  （深い階層）
```

```yaml
# この設定の場合...
- pattern: "README.md"
  schema: ...
# 以下のすべてにマッチします：
# ✓ README.md           （ルートレベル）
# ✓ docs/README.md      （サブディレクトリ内）
```

### 2. 推奨されるパターン記法

より明確で予測可能な動作のために、`**` を明示的に使用することを推奨します：

```yaml
rules:
  file_patterns:
    # ✓ 推奨: すべての階層を明示的に指定
    - pattern: "**/*.txt"
      schema: ...

    # ✓ 推奨: 特定ディレクトリ配下を明示
    - pattern: "reports/**/*.csv"
      schema: ...

    # ✓ 推奨: 特定ディレクトリ直下のみ
    - pattern: "docs/*.md"
      schema: ...
      # 注意: これも "deep/docs/file.md" にマッチします

    # ⚠️ 注意: 意図しないマッチが起こる可能性
    - pattern: "*.txt"
      schema: ...
      # すべての階層の .txt ファイルにマッチ
```

### 3. 深いネスト構造の制限

非常に深い階層（4 階層以上）では、パターンマッチングが不安定になる場合があります：

```yaml
# この設定で...
- pattern: "reports/**/*.csv"
  schema: ...
# マッチする例：
# ✓ reports/data.csv
# ✓ reports/2024/data.csv
# ✓ reports/2024/Q1/data.csv

# マッチしない可能性がある例：
# ? reports/very/deep/nested/path/data.csv  （4階層以上）
```

**対処法**: 通常の使用では問題ありませんが、極端に深い階層構造が予想される場合は、より一般的なパターン `**/*.csv` の使用を検討してください。

### 4. 複数拡張子の記法は非サポート

Bash スタイルの `{md,txt}` のようなブレース展開は使用できません：

```yaml
# ❌ 動作しません
- pattern: "**/*.{md,txt}"
  schema: ...

# ✓ 正しい方法: 個別のルールとして定義
- pattern: "**/*.md"
  schema:
    type: "object"
    properties:
      title: { type: "string" }
    required: ["title"]

- pattern: "**/*.txt"
  schema:
    type: "object"
    properties:
      title: { type: "string" }
    required: ["title"]
```

### 5. ルールの優先順位

複数のルールがマッチする場合、**最初にマッチしたルール**が適用されます：

```yaml
rules:
  file_patterns:
    # この順序が重要
    - pattern: "docs/**/*.md" # より具体的なルール
      schema: { ... } # ← docs 配下はこちらが適用される

    - pattern: "**/*.md" # より一般的なルール
      schema: { ... } # ← それ以外はこちらが適用される
```

## テスト

プロジェクトには Makefile が用意されており、簡単にテストを実行できます。

```bash
# テストディレクトリに移動
cd lambda/metadata-generator

# すべてのテストを実行
make test
```
