"""Integration test for metadata generation."""

import json

from src.clients.bedrock_client import BedrockClient
from src.core.metadata_generator import MetadataGenerator
from src.core.schema import Config, FileInfo, MetadataField, PathRule, FileTypeRule
from src.services.rule_matcher import RuleMatcher

# テスト用の設定を直接定義
TEST_CONFIG = Config(
    metadata_fields={
        "department": MetadataField(type="STRING", description="department"),
        "document_type": MetadataField(
            type="STRING", 
            options=["memo", "minutes", "manual", "others"],
            description="document type"
        ),
        "sensitivity_level": MetadataField(
            type="STRING",
            options=["public", "internal", "confidential", "restricted"],
            description="sensitivity level"
        ),
        "keywords": MetadataField(type="STRING", description="keywords (3-5 words)")
    },
    path_rules=[
        PathRule(
            pattern="**/*.txt",
            extractions={
                "document_type": "memo",
                "sensitivity_level": "internal"
            }
        ),
        PathRule(
            pattern="**/*.md", 
            extractions={
                "document_type": "document",
                "sensitivity_level": "public"
            }
        )
    ],
    file_type_rules={
        "text_files": [
            FileTypeRule(extensions=[".txt", ".md"], use_columns_for_metadata=False)
        ]
    },
    bedrock_model_id="anthropic.claude-3-haiku-20240307-v1:0",
    bedrock_max_tokens=1000,
    bedrock_input_context_window=2000,
    bedrock_temperature=0.1
)


# テストデータを直接定義
SAMPLE_REPORT_TXT = """営業部 月次報告書

2024年10月の営業活動報告

本月の主な成果:
- 新規顧客獲得: 5社
- 契約更新: 12社
- 売上目標達成率: 105%

主要な商談:
1. A社との新規契約締結（年間500万円）
2. B社の契約更新（年間1,200万円）
3. C社への新サービス提案（見積額800万円）

次月の重点施策:
- 既存顧客へのフォローアップ強化
- 新規リード発掘のためのWebセミナー開催
- 営業プロセスの効率化施策の実施

担当: 営業部 田中太郎
作成日: 2024年10月31日

詳細は別紙の通りです。
"""

SAMPLE_DOCUMENT_MD = """# プロジェクト開発ガイド

## 概要

本ドキュメントは、新規プロジェクトの開発手順をまとめたものです。
技術部門向けの開発標準プロセスとして活用してください。

## 環境構築

### 必要なツール

1. Node.js (v18以上)
2. Python (v3.12以上)
3. Docker Desktop
4. Visual Studio Code

### セットアップ手順

```bash
# リポジトリのクローン
git clone https://github.com/example/project.git
cd project

# 依存パッケージのインストール
npm install

# 環境変数の設定
cp .env.example .env
```

## 開発フロー

### ブランチ戦略

- `main`: 本番環境用ブランチ
- `develop`: 開発環境用ブランチ
- `feature/*`: 機能開発用ブランチ

### 開発手順

1. developブランチから新しいfeatureブランチを作成
2. コードを実装
3. ユニットテストを作成・実行
4. コードレビュー用のプルリクエストを作成
5. レビュー承認後、developにマージ

## コーディング規約

- TypeScript: ESLintとPrettierを使用
- Python: Black、Flake8、mypyを使用
- コミットメッセージ: Conventional Commits形式

## テスト戦略

- ユニットテスト: Jest (TypeScript) / pytest (Python)
- 統合テスト: 主要な機能フロー
- E2Eテスト: Playwrightを使用

## デプロイ

CI/CDパイプラインによる自動デプロイを使用します。

---

最終更新: 2024年10月
作成者: 技術部 開発チーム
"""


def test_metadata_generation_for_text_file():
    """Test metadata generation for a text file."""

    bedrock = BedrockClient(
        model_id=TEST_CONFIG.bedrock_model_id,
        max_tokens=TEST_CONFIG.bedrock_max_tokens,
        temperature=TEST_CONFIG.bedrock_temperature,
    )

    # RuleMatcher初期化
    rule_matcher = RuleMatcher(TEST_CONFIG.path_rules)

    # メタデータ生成器初期化
    generator = MetadataGenerator(TEST_CONFIG, bedrock, rule_matcher)

    # テストデータ
    file_info = FileInfo(bucket="test-bucket", key="docs/report.txt", content=SAMPLE_REPORT_TXT)

    # メタデータ生成
    result = generator.generate_metadata(file_info)

    # 生成されたメタデータをログ出力
    print("\n[Text File Test] Generated metadata:")
    print(json.dumps(result.metadata, ensure_ascii=False, indent=2))

    # 検証
    assert result.metadata is not None, "Metadata should not be None"
    assert result.file_key == "docs/report.txt", "File key should match"
    assert "department" in result.metadata, "Should have department field"
    assert "document_type" in result.metadata, "Should have document_type field"
    assert "sensitivity_level" in result.metadata, "Should have sensitivity_level field"
    assert "keywords" in result.metadata, "Should have keywords field"


def test_metadata_generation_for_markdown():
    """Test metadata generation for a markdown file."""
    bedrock = BedrockClient(
        model_id=TEST_CONFIG.bedrock_model_id,
        max_tokens=TEST_CONFIG.bedrock_max_tokens,
        temperature=TEST_CONFIG.bedrock_temperature,
    )

    # RuleMatcher初期化
    rule_matcher = RuleMatcher(TEST_CONFIG.path_rules)

    generator = MetadataGenerator(TEST_CONFIG, bedrock, rule_matcher)

    # テストデータ
    file_info = FileInfo(bucket="test-bucket", key="docs/guide.md", content=SAMPLE_DOCUMENT_MD)

    result = generator.generate_metadata(file_info)

    # 生成されたメタデータをログ出力
    print("\n[Markdown File Test] Generated metadata:")
    print(json.dumps(result.metadata, ensure_ascii=False, indent=2))

    # 検証
    assert result.metadata is not None, "Metadata should not be None"
    assert result.file_key == "docs/guide.md", "File key should match"
    assert "department" in result.metadata, "Should have department field"
    assert "document_type" in result.metadata, "Should have document_type field"
    assert "sensitivity_level" in result.metadata, "Should have sensitivity_level field"
    assert "keywords" in result.metadata, "Should have keywords field"
