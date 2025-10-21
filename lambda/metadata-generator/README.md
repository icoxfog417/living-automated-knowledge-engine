# Metadata Generator for LAKE

S3 にアップロードされたファイルから自動的にメタデータを生成する Lambda 関数です。

## アーキテクチャ

```
EventBridge (S3 Object Created)
  ↓
Lambda Handler (handler.py)
  ↓
MetadataGenerator (metadata_generator.py)
  ├─ ConfigLoader (config_loader.py) - 設定読み込み
  ├─ BedrockClient (bedrock_client.py) - AI生成
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
│   └── metadata_generator.py  # メタデータ生成
├── clients/               # 外部サービスクライアント
│   ├── s3_operations.py   # S3 操作
│   └── bedrock_client.py  # Bedrock API
└── config/
    └── config.yaml        # メタデータルール定義
```

## 主要コンポーネント

### 1. データモデル (`core/schema.py`)

- `FileInfo`: S3 ファイル情報
- `MetadataRule`: メタデータ生成ルール
- `Config`: アプリケーション設定
- `GeneratedMetadata`: 生成結果

### 2. 設定ファイル (`config/config.yaml`)

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

### 3. メタデータ生成フロー

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

### 独立してテストする例

```python
from core.config_loader import ConfigLoader
from core.metadata_generator import MetadataGenerator
from core.schema import FileInfo
from clients.bedrock_client import BedrockClient

# 設定読み込み
config = ConfigLoader.load('src/config/config.yaml')

# Bedrockクライアント初期化
bedrock = BedrockClient(
    model_id=config.bedrock_model_id,
    max_tokens=config.bedrock_max_tokens,
    temperature=config.bedrock_temperature
)

# メタデータ生成器初期化
generator = MetadataGenerator(config, bedrock)

# テストデータ
file_info = FileInfo(
    bucket='test-bucket',
    key='docs/report.pdf',
    content='これは営業報告書です...'
)

# メタデータ生成
result = generator.generate_metadata(file_info)
print(result.metadata)
```

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

## 依存関係

```toml
dependencies = [
    "boto3>=1.34.0",      # AWS SDK
    "pyyaml>=6.0",        # YAML設定ファイル
    "jsonschema>=4.20.0", # JSON Schemaバリデーション
]
```

## デプロイ

CDK を使用してデプロイ:

```bash
npm run build
cdk deploy
```

デプロイされるリソース:

- Lambda 関数（Bedrock アクセス権限付き）
- S3 バケット（EventBridge 有効化）
- EventBridge ルール（S3 オブジェクト作成イベント）

## テスト

### 統合テストの実行

実際の Bedrock API を使用した統合テストが用意されています。テストコードは完全に自己完結しており、外部ファイルに依存しません。

```bash
# テストディレクトリに移動
cd lambda/metadata-generator

# テスト実行（AWS 認証情報が必要）
python tests/test_integration.py
```

### テストの特徴

- **自己完結**: 設定とテストデータはすべてコード内に定義
- **実用的**: 実際の Bedrock API を使用した統合テスト
- **シンプル**: 外部ファイル依存なし

テストの内容：

- テキストファイル（`.txt`）のメタデータ生成
- Markdown ファイル（`.md`）のメタデータ生成
- JSON Schema に基づくバリデーション

### テストコードの構造

```python
# 設定を直接定義
TEST_CONFIG = Config(
    rules=[...],
    bedrock_model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    ...
)

# テストデータを定義
SAMPLE_REPORT_TXT = """営業部 月次報告書..."""

# テスト実行
generator = MetadataGenerator(TEST_CONFIG, bedrock)
result = generator.generate_metadata(file_info)
```

## デプロイ後の動作確認

1. S3 バケットにファイルをアップロード
2. Lambda 関数が自動実行される
3. CloudWatch Logs でログ確認
4. S3 に`.metadata.json`が生成される

```bash
# ファイルアップロード
aws s3 cp test.pdf s3://lake-data-{account}-{region}/docs/test.pdf

# ログ確認
aws logs tail /aws/lambda/lake-metadata-generator --follow

# メタデータ確認
aws s3 cp s3://lake-data-{account}-{region}/docs/test.pdf.metadata.json -
```

## トラブルシューティング

### メタデータが生成されない

- CloudWatch Logs でエラーを確認
- ファイルパスがルールに合致しているか確認
- Bedrock モデルへのアクセス権限を確認

### JSON Schema バリデーションエラー

- ログに出力される詳細なエラーメッセージを確認
- `config.yaml`のスキーマ定義を見直す
- 必須フィールドが適切に定義されているか確認

### タイムアウト

- Lambda 関数のタイムアウトを延長（現在 60 秒）
- ファイルサイズが大きい場合は、読み込みサイズを制限（現在 1MB）
