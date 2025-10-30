"""Comprehensive tests for RuleMatcher and related schema classes."""

from src.core.schema import MetadataField, PathRule, FileTypeRule, Config
from src.services.rule_matcher import RuleMatcher


def test_rule_matcher_comprehensive():
    """Test RuleMatcher with both basic and advanced patterns."""
    rules = [
        # More specific patterns first
        PathRule(pattern="contracts/{department}/**", extractions={"department": "{department}", "document_type": "contract"}),
        PathRule(pattern="{department}/{document_type}/*", extractions={"department": "{department}", "document_type": "{document_type}"}),
        PathRule(pattern="reports/**/*.csv", extractions={"document_type": "report"}),
        # General patterns last
        PathRule(pattern="**/*.md", extractions={"document_type": "markdown"}),
    ]

    matcher = RuleMatcher(rules)

    # Basic pattern matching
    assert RuleMatcher.match_pattern("docs/guide.md", "**/*.md")
    assert RuleMatcher.match_pattern("docs/sub/guide.md", "**/*.md")
    assert RuleMatcher.match_pattern("Bedrock_Wiki.md", "*.md")  # Root level files
    assert RuleMatcher.match_pattern("reports/2024/data.csv", "reports/**/*.csv")  # Has subdirectory
    assert not RuleMatcher.match_pattern("other/data.csv", "reports/**/*.csv")
    assert not RuleMatcher.match_pattern("document.docx", "**/*.md")

    # Advanced pattern matching with variables
    assert RuleMatcher.match_pattern("contracts/sales/agreement.pdf", "contracts/{department}/**")
    assert RuleMatcher.match_pattern("engineering/proposal/spec.md", "{department}/{document_type}/*")

    # Rule finding - basic patterns
    rule = matcher.find_matching_rule("docs/guide.md")  # This should match **/*.md
    assert rule is not None
    assert rule.extractions == {"document_type": "markdown"}

    # Root level file should not match any rules
    rule = matcher.find_matching_rule("Bedrock_Wiki.md")
    assert rule is None

    # Rule finding - advanced patterns with extraction
    rule = matcher.find_matching_rule("contracts/sales/agreement.pdf")
    assert rule is not None
    assert rule.extractions["document_type"] == "contract"

    rule = matcher.find_matching_rule("engineering/proposal/spec.md")
    assert rule is not None
    extracted = matcher.extract_values("engineering/proposal/spec.md", rule)
    assert extracted["department"] == "engineering"
    assert extracted["document_type"] == "proposal"

    # No match
    rule = matcher.find_matching_rule("unknown.xyz")
    assert rule is None


def test_config_structure():
    """Test Config class with all components."""
    config = Config(
        metadata_fields={
            "department": MetadataField(type="STRING", options=["sales"], description="Dept")
        },
        path_rules=[
            PathRule(pattern="**/{department}/**", extractions={"department": "{department}"})
        ],
        file_type_rules={
            "table_data": [FileTypeRule(extensions=[".csv"], use_columns_for_metadata=True)]
        },
        bedrock_model_id="test-model",
        bedrock_max_tokens=1000,
        bedrock_input_context_window=2000,
        bedrock_temperature=0.1
    )
    
    assert len(config.metadata_fields) == 1
    assert len(config.path_rules) == 1
    assert "table_data" in config.file_type_rules


def test_file_type_rule():
    """Test FileTypeRule extension matching and behavior."""
    table_rule = FileTypeRule(extensions=[".csv", ".xlsx"], use_columns_for_metadata=True)
    doc_rule = FileTypeRule(extensions=[".pdf", ".docx"], use_columns_for_metadata=False)
    
    assert ".csv" in table_rule.extensions
    assert ".xlsx" in table_rule.extensions
    assert table_rule.use_columns_for_metadata is True
    
    assert ".pdf" in doc_rule.extensions
    assert doc_rule.use_columns_for_metadata is False


def test_rule_priority():
    """Test PathRule has highest priority over FileTypeRule."""
    path_rules = [
        PathRule(pattern="contracts/**", extractions={"document_type": "contract"})
    ]
    
    matcher = RuleMatcher(path_rules)
    
    # PathRule should match contracts/agreement.pdf and override any FileTypeRule
    rule = matcher.find_matching_rule("contracts/agreement.pdf")
    assert rule is not None
    assert rule.extractions["document_type"] == "contract"
