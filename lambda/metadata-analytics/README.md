# Metadata Analytics

S3 から`.metadata.json`ファイルを収集し、動的なスキーマに対応した傾向分析を行う Lambda 関数。

## 機能

- S3 からメタデータファイルの収集（日付範囲指定）
- 完全動的スキーマ対応（任意のメタデータキーをサポート）
- 自動スキーマ発見
- メタデータフィールドの自動集計
- 並列ダウンロードによる高速処理
- CloudWatch Events による定期実行（デフォルト：毎日午前 1 時 UTC）

## プロジェクト構造

```
lambda/metadata-analytics/
├── src/
│   ├── handler.py               # Lambda handler
│   ├── collector/
│   │   ├── metadata_collector.py  # メインコレクター
│   │   └── models.py              # データモデル
│   └── utils/
│       └── s3_operations.py       # S3操作ユーティリティ
└── tests/
    ├── test_metadata_collector.py
    └── fixtures/
```

## CDK デプロイ

### スタックに含まれるリソース

1. **Lambda 関数**: `lake-metadata-analytics-{id}`

   - Runtime: Python 3.12
   - Memory: 512MB
   - Timeout: 15 分
   - 前日 24 時間のメタデータを分析

2. **CloudWatch Events Rule**: 毎日午前 1 時 UTC に実行

3. **IAM Role**: S3 読み取り権限

### デプロイコマンド

```bash
# CDK のビルド
npm run build

# スタックの合成（テスト）
npx cdk synth

# デプロイ
npx cdk deploy
```

### 環境変数

- `BUCKET_NAME`: 分析対象の S3 バケット名（CDK が自動設定）

## 分析結果の確認

分析結果は CloudWatch Logs に出力されます：

```bash
# ログストリームの確認
aws logs tail /aws/lambda/lake-metadata-analytics-{id} --follow
```

### 出力例

```
================================================================================
METADATA ANALYTICS RESULTS
================================================================================
Total scanned: 150 files
Total collected: 120 files
Execution time: 5.23s
Data transfer: 0.50 MB

================================================================================
DISCOVERED SCHEMA
================================================================================

department:
  Occurrence rate: 95.8%
  Types: str
  Non-null count: 115
  Sample values: Sales, Engineering, HR

document_type:
  Occurrence rate: 100.0%
  Types: str
  Non-null count: 120
  Sample values: report, proposal, contract

================================================================================
AGGREGATIONS
================================================================================

department:
  Sales: 45
  Engineering: 38
  HR: 22
  Marketing: 10

document_type:
  report: 60
  proposal: 30
  contract: 20
  tabular_data: 10

================================================================================
BY FILE TYPE
================================================================================
pdf: 85 files
csv: 10 files
txt: 15 files
md: 10 files
```

## ローカル開発

### セットアップ

```bash
# 依存関係のインストール
make install

# テスト実行
make test

# コードフォーマット
make format
```

### 使用例（スタンドアロン）

```python
from datetime import datetime, timedelta
from src.collector import MetadataCollector, CollectionParams

# パラメータ設定
params = CollectionParams(
    bucket_name="my-lake-bucket",
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    prefix="reports/",
    metadata_filters={
        "department": ["Sales", "Engineering"],
        "document_type": ["report"]
    }
)

# 収集実行
collector = MetadataCollector()
result = collector.collect(params)

# 結果の集計
aggregation = result.aggregate()
print(aggregation)
```

## アーキテクチャ

```
┌─────────────────────────────────────────┐
│ CloudWatch Events (Schedule)            │
│ - Daily at 1:00 AM UTC                  │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ Lambda: metadata-analytics              │
│                                         │
│  1. 前日24時間のメタデータファイルをリスト │
│  2. 並列ダウンロード＆パース             │
│  3. スキーマ自動発見                     │
│  4. 動的集計                            │
│  5. CloudWatch Logsに結果出力           │
└──────────────┬──────────────────────────┘
               │
               ▼
         CloudWatch Logs
```

## テスト

```bash
# ユニットテスト
make test

# カバレッジレポート
make test
# Coverage: 72%
```

## トラブルシューティング

### Lambda タイムアウト

大量のメタデータファイルがある場合、タイムアウトが発生する可能性があります：

```typescript
// CDK で調整
timeout: cdk.Duration.minutes(15);
```

### メモリ不足

```typescript
// CDK で調整
memorySize: 1024; // デフォルト: 512MB
```

### 並列ダウンロード数の調整

```python
# handler.py で調整
params = CollectionParams(
    ...
    parallel_downloads=30  # デフォルト: 20
)
```
