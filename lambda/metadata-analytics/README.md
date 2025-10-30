# Metadata Analytics

S3 からメタデータファイルを収集し、AI 統計解析と PDF レポートを生成する Lambda 関数。

## 主な機能

- S3 メタデータファイルの自動収集（日付範囲指定）
- 動的スキーマ対応（任意のメタデータキーをサポート）
- matplotlib/seaborn による決定論的な図表生成
- Strands Agents SDK による AI 解析
- PDF レポート自動生成・S3 保存
- CloudWatch Events で定期実行（毎日午前 1 時 UTC）

## アーキテクチャ

```
CloudWatch Events (毎日1:00 UTC)
    ↓
Lambda (Python 3.12, 1536MB)
    ↓
1. メタデータ収集（S3から前日24時間分）
2. 決定論的図表生成（matplotlib/seaborn）
3. AI解析（Strands Agents + Claude 3.5）
4. PDFレポート生成（ReportLab）
5. S3保存
    ↓
S3: analytics-reports/{date}/
    ├─ metadata-analytics-report.pdf
    └─ charts/*.png
```

## 出力

- **PDF レポート**: エグゼクティブサマリー、主要発見事項、統計情報
- **図表**: カテゴリカルデータの棒グラフ/円グラフ
