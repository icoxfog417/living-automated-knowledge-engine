"""Unit tests for pattern matching logic."""
from pathlib import PurePosixPath

from src.core.metadata_generator import MetadataGenerator
from src.core.schema import Config, MetadataRule
from src.clients.bedrock_client import BedrockClient


def test_pattern_matching_root_level_files():
    """Test that root-level files match ** patterns correctly."""
    # Create a minimal config for testing
    config = Config(
        rules=[
            MetadataRule(pattern="**/*.md", schema={}),
            MetadataRule(pattern="**/*.txt", schema={}),
            MetadataRule(pattern="**/*.pdf", schema={}),
        ],
        bedrock_model_id="test-model",
        bedrock_max_tokens=1000,
        bedrock_temperature=0.1
    )
    
    bedrock_client = BedrockClient(
        model_id="test-model",
        max_tokens=1000,
        temperature=0.1
    )
    
    generator = MetadataGenerator(config, bedrock_client)
    
    # Test root-level files
    assert generator._match_pattern("Bedrock_Wiki.md", "**/*.md")
    assert generator._match_pattern("report.txt", "**/*.txt")
    assert generator._match_pattern("document.pdf", "**/*.pdf")


def test_pattern_matching_nested_files():
    """Test that nested files match ** patterns correctly."""
    config = Config(
        rules=[MetadataRule(pattern="**/*.md", schema={})],
        bedrock_model_id="test-model",
        bedrock_max_tokens=1000,
        bedrock_temperature=0.1
    )
    
    bedrock_client = BedrockClient(
        model_id="test-model",
        max_tokens=1000,
        temperature=0.1
    )
    
    generator = MetadataGenerator(config, bedrock_client)
    
    # Test nested files
    assert generator._match_pattern("docs/guide.md", "**/*.md")
    assert generator._match_pattern("deep/nested/path/readme.md", "**/*.md")


def test_pattern_matching_with_directory_prefix():
    """Test patterns with directory prefix like 'reports/**/*.csv'."""
    config = Config(
        rules=[MetadataRule(pattern="reports/**/*.csv", schema={})],
        bedrock_model_id="test-model",
        bedrock_max_tokens=1000,
        bedrock_temperature=0.1
    )
    
    bedrock_client = BedrockClient(
        model_id="test-model",
        max_tokens=1000,
        temperature=0.1
    )
    
    generator = MetadataGenerator(config, bedrock_client)
    
    # Should match
    assert generator._match_pattern("reports/data.csv", "reports/**/*.csv")
    assert generator._match_pattern("reports/nested/data.csv", "reports/**/*.csv")
    
    # Should not match
    assert not generator._match_pattern("other/data.csv", "reports/**/*.csv")


def test_pattern_matching_negative_cases():
    """Test that files with wrong extensions don't match."""
    config = Config(
        rules=[MetadataRule(pattern="**/*.md", schema={})],
        bedrock_model_id="test-model",
        bedrock_max_tokens=1000,
        bedrock_temperature=0.1
    )
    
    bedrock_client = BedrockClient(
        model_id="test-model",
        max_tokens=1000,
        temperature=0.1
    )
    
    generator = MetadataGenerator(config, bedrock_client)
    
    # Should not match
    assert not generator._match_pattern("document.docx", "**/*.md")
    assert not generator._match_pattern("data.csv", "**/*.md")
    assert not generator._match_pattern("report.txt", "**/*.md")


def test_find_matching_rule():
    """Test that _find_matching_rule returns the correct rule."""
    config = Config(
        rules=[
            MetadataRule(pattern="**/*.md", schema={"type": "markdown"}),
            MetadataRule(pattern="**/*.txt", schema={"type": "text"}),
            MetadataRule(pattern="reports/**/*.csv", schema={"type": "csv"}),
        ],
        bedrock_model_id="test-model",
        bedrock_max_tokens=1000,
        bedrock_temperature=0.1
    )
    
    bedrock_client = BedrockClient(
        model_id="test-model",
        max_tokens=1000,
        temperature=0.1
    )
    
    generator = MetadataGenerator(config, bedrock_client)
    
    # Test matching
    rule = generator._find_matching_rule("Bedrock_Wiki.md")
    assert rule is not None
    assert rule.schema == {"type": "markdown"}
    
    rule = generator._find_matching_rule("docs/report.txt")
    assert rule is not None
    assert rule.schema == {"type": "text"}
    
    rule = generator._find_matching_rule("reports/data.csv")
    assert rule is not None
    assert rule.schema == {"type": "csv"}
    
    # Test no match
    rule = generator._find_matching_rule("unknown.xyz")
    assert rule is None
