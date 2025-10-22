# Metadata Analytics

S3 から`.metadata.json`ファイルを収集し、動的なスキーマに対応した傾向分析を行い、**Strands Agents SDK**を使用して AI による統計解析と PDF レポート生成を実行する Lambda 関数。

## 機能

### データ収集

- S3 からメタデータファイルの収集（日付範囲指定）
- 完全動的スキーマ対応（任意のメタデータキーをサポート）
- 自動スキーマ発見
- メタデータフィールドの自動集計
- 並列ダウンロードによる高速処理

### AI 統計解析（Strands Agents SDK）

- **決定論的な図表生成**により常に同じデータから同じ結果を生成
- matplotlib/seaborn による可視化グラフの事前生成
- AI エージェントによるデータ解釈と洞察の提供
- エグゼクティブサマリーの自動生成
- 主要な発見事項の抽出

### レポート生成

- ReportLab による PDF レポートの自動生成
- 統計情報の表形式表示
- AI 分析結果の組み込み
- S3 への自動保存（レポートと図表）

### スケジュール実行

- CloudWatch Events による定期実行（デフォルト：毎日午前 1 時 UTC）

## プロジェクト構造

```
lambda/metadata-analytics/
├── src/
│   ├── handler.py                  # Lambda handler
│   ├── agents/
│   │   └── analytics_agent.py      # Strands AI統計解析エージェント
│   ├── collector/
│   │   ├── metadata_collector.py   # メインコレクター
│   │   └── models.py               # データモデル
│   └── utils/
│       ├── s3_operations.py        # S3操作ユーティリティ
│       └── pdf_generator.py        # PDFレポート生成
└── tests/
    ├── test_metadata_collector.py
    └── fixtures/
```

## CDK デプロイ

### スタックに含まれるリソース

1. **Lambda 関数**: `lake-metadata-analytics-{id}`

   - Runtime: Python 3.12
   - Memory: 1536MB（AI エージェント操作用に増量）
   - Timeout: 15 分
   - 前日 24 時間のメタデータを分析

2. **CloudWatch Events Rule**: 毎日午前 1 時 UTC に実行

3. **IAM Role**:
   - S3 読み取り・書き込み権限
   - Bedrock モデル呼び出し権限
   - Bedrock AgentCore 権限（CodeInterpreter ツール用）

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

METADATA ANALYTICS RESULTS
Total scanned: 150 files
Total collected: 120 files
Execution time: 5.23s
Data transfer: 0.50 MB

DISCOVERED SCHEMA

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

AGGREGATIONS

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

BY FILE TYPE
pdf: 85 files
csv: 10 files
txt: 15 files
md: 10 files

```
### 出力例

```

METADATA ANALYTICS RESULTS
Total scanned: 150 files
Total collected: 120 files
Execution time: 5.23s
Data transfer: 0.50 MB

DISCOVERED SCHEMA

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

AGGREGATIONS

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

BY FILE TYPE
pdf: 85 files
csv: 10 files
txt: 15 files
md: 10 files

AI-POWERED ANALYSIS WITH STRANDS AGENTS
Running AI analysis with CodeInterpreter tool...
Analysis completed in 12.45s

Executive Summary:
データ分析により、Sales 部門が最も活発に文書を生成しており（37.5%）、
レポート形式が全体の 50%を占めています。PDF ファイルが主流（70.8%）で、
過去 24 時間で 120 件のメタデータが生成されました。

Key Findings (5 items):

1. Sales 部門が最多の 45 件（37.5%）のドキュメントを作成
2. レポート形式が 60 件で最も一般的（50.0%）
3. PDF ファイルが 85 件で全体の 70.8%を占める
4. document_type フィールドの出現率は 100%で必須フィールドと判断
5. Engineering 部門と HR 部門で 38 件と 22 件を記録

Generated charts: department_distribution.png, document_type_distribution.png

GENERATING PDF REPORT
PDF report generated: /tmp/metadata_analytics_report_20251022.pdf

ANALYTICS COMPLETED SUCCESSFULLY
Report URL: s3://my-lake-bucket/analytics-reports/2025-10-22/metadata-analytics-report.pdf
Chart URLs: 2 files uploaded

```

### 生成されるレポート

- **PDF レポート**: `s3://{bucket}/analytics-reports/{date}/metadata-analytics-report.pdf`
  - エグゼクティブサマリー
  - 主要な発見事項
  - 統計情報テーブル
  - 収集サマリー

- **図表**: `s3://{bucket}/analytics-reports/{date}/charts/*.png`
  - AI が生成した matplotlib グラフ
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

### Lambda Handler のローカルテスト

完全なハンドラー（AI 分析 + PDF 生成 + S3 アップロード）をローカルでテストできます：

```bash
# 通常実行（S3にアップロード）
uv run python test_handler_local.py

# ドライランモード（S3アップロードをスキップ、ローカル保存のみ）
DRY_RUN=true uv run python test_handler_local.py
```

**機能:**

- CloudWatch Events イベントをシミュレート
- Lambda コンテキストをモック
- 完全な実行フロー（収集 → AI 分析 → PDF 生成 → S3 アップロード）
- DRY_RUN モードで S3 アップロードをスキップ可能

**必要な設定:**

- AWS 認証情報が設定済み（`aws configure`）
- Bedrock で Claude 3.5 Sonnet が有効化済み
- S3 バケットに `.metadata.json` ファイルが存在

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
┌─────────────────────────────────────────────────────────────┐
│ Lambda: metadata-analytics (Python 3.12, 1536MB)            │
│                                                             │
│  1. データ収集                                               │
│     ├─ 前日24時間のメタデータファイルをリスト                 │
│     ├─ 並列ダウンロード＆パース                              │
│     ├─ スキーマ自動発見                                      │
│     └─ 動的集計                                             │
│                                                             │
│  2. 決定論的図表生成（ChartGenerator）                       │
│     ├─ matplotlib/seabornで図表を生成                       │
│     │   ├─ カテゴリカルデータ：棒グラフ/円グラフ             │
│     │   └─ ファイルタイプ分布                                │
│     └─ 一時ファイルとして保存                                │
│                                                             │
│  3. AI解釈（Strands Agents SDK）                            │
│     ├─ Bedrock: Claude 3.5 Sonnet呼び出し                   │
│     ├─ 統計データと図表情報を解釈                            │
│     └─ 洞察とサマリーを生成                                  │
│                                                             │
│  4. レポート生成（PDFReportGenerator）                       │
│     ├─ ReportLabでPDF生成                                   │
│     ├─ 図表画像を埋め込み                                    │
│     └─ 統計情報・AI分析結果を含む                            │
│                                                             │
│  4. S3保存                                                  │
│     ├─ PDFレポート                                          │
│     └─ 図表ファイル                                          │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├──────────────────┐
               ▼                  ▼
         CloudWatch Logs    S3: analytics-reports/
                            ├─ {date}/metadata-analytics-report.pdf
                            └─ {date}/charts/*.png
```

## 主要コンポーネント

### ChartGenerator（図表生成）

決定論的な図表生成：

```python
from src.utils.chart_generator import ChartGenerator

generator = ChartGenerator()
chart_results = generator.generate_charts(aggregation)

# 各 ChartResult には以下の情報が含まれる:
# - chart_type: "bar" or "pie"
# - title: 図表のタイトル
# - file_path: 生成された画像ファイルパス
# - metadata_key: 対応するメタデータフィールド
# - description: 図表の説明
```

**特徴:**

- 決定論的：同じデータから常に同じ図表を生成
- カテゴリカルデータの自動可視化
- カテゴリ数に応じて棒グラフ/円グラフを選択
- プロフェッショナルなスタイリング

### MetadataAnalyticsAgent（AI 解釈）

Strands Agents SDK を使用した統計データの解釈エージェント：

```python
from src.agents.analytics_agent import MetadataAnalyticsAgent

agent = MetadataAnalyticsAgent(region="us-east-1")
analysis_result = agent.analyze(
    statistics=aggregation,
    chart_info=chart_info  # 事前生成された図表情報
)

# 出力:
# {
#   "executive_summary": "...",
#   "key_findings": [...],
#   "charts": ["/tmp/chart1.png", ...],
#   "execution_time": 3.2
# }
```

**機能:**

- Claude 3.5 Sonnet による高度なデータ解釈
- 事前生成された図表情報を活用
- ビジネス的な洞察の提供
- 構造化された分析結果の返却
- CodeInterpreter 不使用で高速・信頼性向上

### PDFReportGenerator（レポート生成）

ReportLab を使用した PDF レポート生成：

```python
from src.utils.pdf_generator import PDFReportGenerator

generator = PDFReportGenerator()
pdf_path = generator.generate_report(
    aggregation=aggregation,
    analysis=analysis_result,
    start_date=start_date,
    end_date=end_date
)
```

**出力:**

- プロフェッショナルなレイアウト
- カスタムスタイル（色・フォント）
- 統計情報の表形式表示
- AI 分析結果の統合

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

AI エージェント操作には十分なメモリが必要です：

```typescript
// CDK で調整（現在: 1536MB）
memorySize: 2048; // さらに増やす場合
```

### 並列ダウンロード数の調整

```python
# handler.py で調整
params = CollectionParams(
    ...
    parallel_downloads=30  # デフォルト: 20
)
```

### AI エージェントのタイムアウト

CodeInterpreter を使用した分析に時間がかかる場合：

```python
# src/agents/analytics_agent.py で調整
agent = Agent(
    ...
    inference_config={
        "maxTokens": 4096,
        "temperature": 0.3,
        "topP": 0.9,
        "stopSequences": []
    }
)
```

### Bedrock モデルアクセス

Bedrock でモデルへのアクセスを有効化する必要があります：

1. AWS Console → Bedrock → Model access
2. Claude 3.5 Sonnet を有効化
3. リージョン: `us-east-1` または環境変数 `AWS_REGION` で指定

## 依存関係

- **boto3**: AWS SDK
- **strands-agents**: Strands Agents SDK（AI エージェント）
- **reportlab**: PDF 生成
- **matplotlib**: グラフ作成
- **seaborn**: 高度なグラフ作成
- **pandas**: データ分析

## アーキテクチャの改善点

### v2.0: 決定論的図表生成

**変更内容:**

- AI エージェントが CodeInterpreter で図表を生成する方式から、事前に決定論的に図表を生成する方式に変更
- ChartGenerator モジュールを新規追加
- bedrock-agentcore 依存を削除

**メリット:**

1. **決定論的**: 同じデータから常に同じ図表が生成される
2. **信頼性向上**: AI の不確実性を排除
3. **パフォーマンス**: CodeInterpreter 実行が不要で高速化
4. **保守性**: 図表生成ロジックがコードとして管理される
5. **テスト容易性**: ユニットテストが可能
6. **コスト削減**: CodeInterpreter 実行コストを削減

**実行フロー:**

```
メタデータ収集 → 集約
    ↓
ChartGenerator（決定論的）
    ↓
図表ファイル生成
    ↓
AI Agent（解釈のみ）
    ↓
洞察・サマリー生成
    ↓
PDF生成（図表埋め込み）
```
