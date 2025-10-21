"""Integration test for metadata generation."""
import json

from src.core.metadata_generator import MetadataGenerator
from src.core.schema import FileInfo, Config, MetadataRule
from src.clients.bedrock_client import BedrockClient


# テスト用の設定を直接定義
TEST_CONFIG = Config(
    rules=[
        MetadataRule(
            pattern="**/*.txt",
            schema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "department"
                    },
                    "document_type": {
                        "type": "string",
                        "enum": ["memo", "minutes", "manual", "others"],
                        "description": "document type"
                    },
                    "sensitivity_level": {
                        "type": "string",
                        "enum": ["public", "internal", "confidential", "restricted"],
                        "description": "sensitivity level"
                    },                    
                },
                "required": ["department", "document_type", "sensitivity_level", "keywords"]
            }
        ),
        MetadataRule(
            pattern="**/*.md",
            schema={
                "type": "object",
                "properties": {
                    "department": {
                        "type": "string",
                        "description": "department"
                    },
                    "document_type": {
                        "type": "string",
                        "enum": ["document", "README", "others"],
                        "description": "document type"
                    },
                    "keywords": {
                        "type": "string",
                        "description": "keywords（3-5 words）",
                    },
                    "summary": {
                        "type": "string",
                        "description": "document's summary (-100 words)"
                    }
                },
                "required": ["department", "document_type", "sensitivity_level", "keywords"]
            }
        )
    ],
    bedrock_model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    bedrock_max_tokens=2000,
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
        temperature=TEST_CONFIG.bedrock_temperature
    )
    
    # メタデータ生成器初期化
    generator = MetadataGenerator(TEST_CONFIG, bedrock)
    
    # テストデータ  
    file_info = FileInfo(
        bucket='test-bucket',
        key='docs/report.txt',
        content=SAMPLE_REPORT_TXT
    )
    
    # メタデータ生成
    result = generator.generate_metadata(file_info)
    print(result)
    
    # 検証
    assert result.metadata is not None, "Metadata should not be None"


def test_metadata_generation_for_markdown():
    """Test metadata generation for a markdown file."""
    bedrock = BedrockClient(
        model_id=TEST_CONFIG.bedrock_model_id,
        max_tokens=TEST_CONFIG.bedrock_max_tokens,
        temperature=TEST_CONFIG.bedrock_temperature
    )
    
    generator = MetadataGenerator(TEST_CONFIG, bedrock)
    
    # テストデータ
    file_info = FileInfo(
        bucket='test-bucket',
        key='docs/guide.md',
        content=SAMPLE_DOCUMENT_MD
    )
    
    result = generator.generate_metadata(file_info)
    print(result)
    
    # 検証
    assert result.metadata is not None, "Metadata should not be None"


if __name__ == '__main__':    
    results = []
    errors = []
    
    # Test 1: Text file
    try:
        result1 = test_metadata_generation_for_text_file()
        results.append(("Text file test", result1))
    except Exception as e:
        print(f"\n❌ Text file test failed: {e}")
        import traceback
        traceback.print_exc()
        errors.append(("Text file test", e))
    
    # Test 2: Markdown file
    try:
        result2 = test_metadata_generation_for_markdown()
        results.append(("Markdown file test", result2))
    except Exception as e:
        print(f"\n❌ Markdown file test failed: {e}")
        import traceback
        traceback.print_exc()
        errors.append(("Markdown file test", e))
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"\n✅ Passed: {len(results)}")
    print(f"❌ Failed: {len(errors)}")
    
    if errors:
        print("\n❌ Failed tests:")
        for name, error in errors:
            print(f"   - {name}: {error}")
    
    if len(results) == 2 and len(errors) == 0:
        print("\n🎉 All tests passed successfully!")
        print("\nGenerated metadata can now be used with Amazon Bedrock Knowledge Bases.")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)
