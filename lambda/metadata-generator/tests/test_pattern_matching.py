"""Unit tests for pattern matching logic (integration with RuleMatcher)."""

from src.core.schema import MetadataRule
from src.services.rule_matcher import RuleMatcher


def test_pattern_matching_root_level_files():
    """Test that root-level files match ** patterns correctly."""
    matcher = RuleMatcher(
        [
            MetadataRule(pattern="**/*.md", schema={}),
            MetadataRule(pattern="**/*.txt", schema={}),
            MetadataRule(pattern="**/*.pdf", schema={}),
        ]
    )

    # Test root-level files
    assert matcher.match_pattern("Bedrock_Wiki.md", "**/*.md")
    assert matcher.match_pattern("report.txt", "**/*.txt")
    assert matcher.match_pattern("document.pdf", "**/*.pdf")


def test_pattern_matching_nested_files():
    """Test that nested files match ** patterns correctly."""
    matcher = RuleMatcher([MetadataRule(pattern="**/*.md", schema={})])

    # Test nested files
    assert matcher.match_pattern("docs/guide.md", "**/*.md")
    assert matcher.match_pattern("deep/nested/path/readme.md", "**/*.md")


def test_pattern_matching_with_directory_prefix():
    """Test patterns with directory prefix like 'reports/**/*.csv'."""
    matcher = RuleMatcher([MetadataRule(pattern="reports/**/*.csv", schema={})])

    # Should match
    assert matcher.match_pattern("reports/data.csv", "reports/**/*.csv")
    assert matcher.match_pattern("reports/nested/data.csv", "reports/**/*.csv")

    # Should not match
    assert not matcher.match_pattern("other/data.csv", "reports/**/*.csv")


def test_pattern_matching_negative_cases():
    """Test that files with wrong extensions don't match."""
    matcher = RuleMatcher([MetadataRule(pattern="**/*.md", schema={})])

    # Should not match
    assert not matcher.match_pattern("document.docx", "**/*.md")
    assert not matcher.match_pattern("data.csv", "**/*.md")
    assert not matcher.match_pattern("report.txt", "**/*.md")


def test_find_matching_rule():
    """Test that find_matching_rule returns the correct rule."""
    matcher = RuleMatcher(
        [
            MetadataRule(pattern="**/*.md", schema={"type": "markdown"}),
            MetadataRule(pattern="**/*.txt", schema={"type": "text"}),
            MetadataRule(pattern="reports/**/*.csv", schema={"type": "csv"}),
        ]
    )

    # Test matching
    rule = matcher.find_matching_rule("Bedrock_Wiki.md")
    assert rule is not None
    assert rule.schema == {"type": "markdown"}

    rule = matcher.find_matching_rule("docs/report.txt")
    assert rule is not None
    assert rule.schema == {"type": "text"}

    rule = matcher.find_matching_rule("reports/data.csv")
    assert rule is not None
    assert rule.schema == {"type": "csv"}

    # Test no match
    rule = matcher.find_matching_rule("unknown.xyz")
    assert rule is None
